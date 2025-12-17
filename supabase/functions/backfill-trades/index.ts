import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.4";
import { createHmac } from "node:crypto";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) {
      return new Response(JSON.stringify({ error: "Missing authorization" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const token = authHeader.replace("Bearer ", "");
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    if (authError || !user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const { symbols } = await req.json().catch(() => ({ symbols: [] }));

    // Get user's Binance credentials
    const { data: session } = await supabase
      .from("aureon_user_sessions")
      .select("binance_api_key_encrypted, binance_api_secret_encrypted, binance_iv")
      .eq("user_id", user.id)
      .single();

    if (!session?.binance_api_key_encrypted || !session?.binance_api_secret_encrypted) {
      return new Response(JSON.stringify({ error: "No Binance credentials configured" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Decrypt credentials
    const encryptionKey = Deno.env.get("MASTER_ENCRYPTION_KEY") || "default-key-32-chars-long!!!!!";
    const keyBuffer = new TextEncoder().encode(encryptionKey.slice(0, 32).padEnd(32, "0"));
    const iv = session.binance_iv ? Uint8Array.from(atob(session.binance_iv), c => c.charCodeAt(0)) : new Uint8Array(12);

    async function decrypt(encrypted: string): Promise<string> {
      try {
        const encryptedBytes = Uint8Array.from(atob(encrypted), c => c.charCodeAt(0));
        const cryptoKey = await crypto.subtle.importKey("raw", keyBuffer, { name: "AES-GCM" }, false, ["decrypt"]);
        const decrypted = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, cryptoKey, encryptedBytes);
        return new TextDecoder().decode(decrypted);
      } catch {
        return atob(encrypted);
      }
    }

    const apiKey = await decrypt(session.binance_api_key_encrypted);
    const apiSecret = await decrypt(session.binance_api_secret_encrypted);

    // If no symbols provided, get from account balances
    let symbolList = symbols || [];
    if (symbolList.length === 0) {
      const timestamp = Date.now();
      const queryString = `timestamp=${timestamp}`;
      const signature = createHmac("sha256", apiSecret).update(queryString).digest("hex");
      
      const accountRes = await fetch(
        `https://api.binance.com/api/v3/account?${queryString}&signature=${signature}`,
        { headers: { "X-MBX-APIKEY": apiKey } }
      );
      
      if (accountRes.ok) {
        const accountData = await accountRes.json();
        const assets = (accountData.balances || [])
          .filter((b: any) => parseFloat(b.free) > 0 || parseFloat(b.locked) > 0)
          .map((b: any) => b.asset)
          .filter((a: string) => !["USDT", "USDC", "BUSD", "USD"].includes(a));
        
        symbolList = assets.map((a: string) => `${a}USDT`);
      }
    }

    console.log(`Backfilling trades for ${symbolList.length} symbols:`, symbolList.slice(0, 10));

    let totalExecutions = 0;
    let totalPositions = 0;
    const errors: string[] = [];

    // Fetch trades for each symbol and insert into trading_executions
    for (const symbol of symbolList.slice(0, 20)) { // Limit to 20 symbols per call
      try {
        const timestamp = Date.now();
        const queryString = `symbol=${symbol}&limit=500&timestamp=${timestamp}`;
        const signature = createHmac("sha256", apiSecret).update(queryString).digest("hex");

        const tradesRes = await fetch(
          `https://api.binance.com/api/v3/myTrades?${queryString}&signature=${signature}`,
          { headers: { "X-MBX-APIKEY": apiKey } }
        );

        if (!tradesRes.ok) {
          const errText = await tradesRes.text();
          if (!errText.includes("-1121")) { // Ignore invalid symbol errors
            errors.push(`${symbol}: ${errText}`);
          }
          continue;
        }

        const trades = await tradesRes.json();
        if (!Array.isArray(trades) || trades.length === 0) continue;

        // Insert into trading_executions
        const executions = trades.map((t: any) => ({
          user_id: user.id,
          symbol: t.symbol,
          side: t.isBuyer ? "BUY" : "SELL",
          order_type: "MARKET",
          quantity: parseFloat(t.qty),
          price: parseFloat(t.price),
          executed_quantity: parseFloat(t.qty),
          executed_price: parseFloat(t.price),
          commission: parseFloat(t.commission || "0"),
          commission_asset: t.commissionAsset,
          exchange_order_id: String(t.orderId),
          status: "FILLED",
          exchange: "binance",
          executed_at: new Date(t.time).toISOString(),
          created_at: new Date(t.time).toISOString(),
        }));

        // Upsert executions (avoid duplicates by exchange_order_id)
        const { error: insertError } = await supabase
          .from("trading_executions")
          .upsert(executions, { onConflict: "exchange_order_id", ignoreDuplicates: true });

        if (insertError) {
          console.error(`Insert error for ${symbol}:`, insertError);
          errors.push(`${symbol}: ${insertError.message}`);
        } else {
          totalExecutions += executions.length;
        }

        // Calculate net position for this symbol
        let netQty = 0;
        let totalBuyCost = 0;
        let totalBuyQty = 0;

        for (const t of trades) {
          const qty = parseFloat(t.qty);
          const price = parseFloat(t.price);
          if (t.isBuyer) {
            netQty += qty;
            totalBuyCost += qty * price;
            totalBuyQty += qty;
          } else {
            netQty -= qty;
          }
        }

        // If we have a net long position, create/update trading_positions
        if (netQty > 0.00000001 && totalBuyQty > 0) {
          const avgEntryPrice = totalBuyCost / totalBuyQty;
          
          // Get current price
          let currentPrice = avgEntryPrice;
          try {
            const priceRes = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${symbol}`);
            if (priceRes.ok) {
              const priceData = await priceRes.json();
              currentPrice = parseFloat(priceData.price);
            }
          } catch {}

          const unrealizedPnl = (currentPrice - avgEntryPrice) * netQty;

          const positionData = {
            user_id: user.id,
            symbol,
            side: "LONG",
            entry_price: avgEntryPrice,
            quantity: netQty,
            position_value_usdt: netQty * avgEntryPrice,
            current_price: currentPrice,
            unrealized_pnl: unrealizedPnl,
            status: "open",
          };

          // Check if position exists
          const { data: existingPos } = await supabase
            .from("trading_positions")
            .select("id")
            .eq("user_id", user.id)
            .eq("symbol", symbol)
            .eq("status", "open")
            .single();

          if (existingPos) {
            await supabase
              .from("trading_positions")
              .update(positionData)
              .eq("id", existingPos.id);
          } else {
            await supabase.from("trading_positions").insert(positionData);
          }
          totalPositions++;
        }

        // Small delay to avoid rate limits
        await new Promise(r => setTimeout(r, 100));

      } catch (err: any) {
        errors.push(`${symbol}: ${err?.message || String(err)}`);
      }
    }

    return new Response(JSON.stringify({
      success: true,
      executionsBackfilled: totalExecutions,
      positionsCreated: totalPositions,
      symbolsProcessed: Math.min(symbolList.length, 20),
      errors: errors.slice(0, 10),
    }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (error: any) {
    console.error("backfill-trades error:", error);
    return new Response(JSON.stringify({ error: error?.message || String(error) }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
