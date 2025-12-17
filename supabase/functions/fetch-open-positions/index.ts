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
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

    // Verify user with anon client
    const anonSupabase = createClient(supabaseUrl, supabaseAnonKey);
    const token = authHeader.replace("Bearer ", "");
    const { data: { user }, error: authError } = await anonSupabase.auth.getUser(token);
    
    if (authError || !user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Use service role for database access
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Get user's Binance credentials
    const { data: session } = await supabase
      .from("aureon_user_sessions")
      .select("binance_api_key_encrypted, binance_api_secret_encrypted, binance_iv")
      .eq("user_id", user.id)
      .single();

    if (!session?.binance_api_key_encrypted || !session?.binance_api_secret_encrypted || !session?.binance_iv) {
      return new Response(JSON.stringify({ error: "No Binance credentials configured" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Use consistent text-padded encryption key (matches get-user-balances)
    const encryptionKey = 'aureon-default-key-32chars!!';
    const encoder = new TextEncoder();
    const keyData = encoder.encode(encryptionKey.padEnd(32, '0').slice(0, 32));
    
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM' },
      false,
      ['decrypt']
    );

    const decodeIvFromB64 = (ivB64: string) => Uint8Array.from(atob(ivB64), c => c.charCodeAt(0));

    async function decrypt(encrypted: string, iv: Uint8Array): Promise<string> {
      const encryptedBytes = Uint8Array.from(atob(encrypted), c => c.charCodeAt(0));
      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv as unknown as BufferSource },
        cryptoKey,
        encryptedBytes
      );
      return new TextDecoder().decode(decrypted);
    }

    const iv = decodeIvFromB64(session.binance_iv);
    const apiKey = await decrypt(session.binance_api_key_encrypted, iv);
    const apiSecret = await decrypt(session.binance_api_secret_encrypted, iv);

    // Fetch account info from Binance
    const timestamp = Date.now();
    const queryString = `timestamp=${timestamp}`;
    const signature = createHmac("sha256", apiSecret).update(queryString).digest("hex");

    const accountRes = await fetch(
      `https://api.binance.com/api/v3/account?${queryString}&signature=${signature}`,
      { headers: { "X-MBX-APIKEY": apiKey } }
    );

    if (!accountRes.ok) {
      const errText = await accountRes.text();
      console.error("Binance account error:", errText);
      return new Response(JSON.stringify({ error: "Failed to fetch Binance account", details: errText }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const accountData = await accountRes.json();
    const balances = accountData.balances || [];

    // Filter to non-zero balances (spot positions)
    const spotPositions = balances
      .filter((b: any) => {
        const free = parseFloat(b.free || "0");
        const locked = parseFloat(b.locked || "0");
        return free > 0 || locked > 0;
      })
      .map((b: any) => ({
        asset: b.asset,
        free: parseFloat(b.free || "0"),
        locked: parseFloat(b.locked || "0"),
        total: parseFloat(b.free || "0") + parseFloat(b.locked || "0"),
      }));

    // Fetch current prices for USD value calculation
    const pricesRes = await fetch("https://api.binance.com/api/v3/ticker/price");
    const allPrices = pricesRes.ok ? await pricesRes.json() : [];
    const priceMap: Record<string, number> = {};
    for (const p of allPrices) {
      priceMap[p.symbol] = parseFloat(p.price);
    }

    // Enrich positions with USD values
    const enrichedPositions = spotPositions.map((pos: any) => {
      let usdValue = 0;
      if (pos.asset === "USDT" || pos.asset === "USDC" || pos.asset === "BUSD") {
        usdValue = pos.total;
      } else {
        const usdtPair = `${pos.asset}USDT`;
        const btcPair = `${pos.asset}BTC`;
        if (priceMap[usdtPair]) {
          usdValue = pos.total * priceMap[usdtPair];
        } else if (priceMap[btcPair] && priceMap["BTCUSDT"]) {
          usdValue = pos.total * priceMap[btcPair] * priceMap["BTCUSDT"];
        }
      }
      return { ...pos, usdValue };
    });

    // Sort by USD value descending
    enrichedPositions.sort((a: any, b: any) => b.usdValue - a.usdValue);

    const totalUsdValue = enrichedPositions.reduce((sum: number, p: any) => sum + p.usdValue, 0);

    return new Response(JSON.stringify({
      success: true,
      positions: enrichedPositions,
      totalUsdValue,
      positionCount: enrichedPositions.length,
    }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (error: any) {
    console.error("fetch-open-positions error:", error);
    return new Response(JSON.stringify({ error: error?.message || String(error) }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
