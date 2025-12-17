import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.4";
import { createHmac } from "node:crypto";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

function isPrintableAscii(s: string) {
  if (!s) return false;
  if (/[\s\x00-\x1F\x7F]/.test(s)) return false;
  return /^[\x21-\x7E]+$/.test(s);
}

interface SpotPosition {
  asset: string;
  free: number;
  locked: number;
  total: number;
  usdValue: number;
  exchange: string;
}

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

    const anonSupabase = createClient(supabaseUrl, supabaseAnonKey);
    const token = authHeader.replace("Bearer ", "");
    const { data: { user }, error: authError } = await anonSupabase.auth.getUser(token);

    if (authError || !user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    const { data: session, error: sessionError } = await supabase
      .from("aureon_user_sessions")
      .select("binance_api_key_encrypted, binance_api_secret_encrypted, binance_iv, kraken_api_key_encrypted, kraken_api_secret_encrypted, kraken_iv")
      .eq("user_id", user.id)
      .single();

    if (sessionError || !session) {
      return new Response(JSON.stringify({ error: "No session found" }), {
        status: 404,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Decryption setup
    const primaryKeyString = "aureon-default-key-32chars!!";
    const fallbackKeyString = Deno.env.get("MASTER_ENCRYPTION_KEY") || "";
    const encoder = new TextEncoder();
    const keyBytes1 = encoder.encode(primaryKeyString.padEnd(32, "0").slice(0, 32));
    const keyBytes2 = encoder.encode(fallbackKeyString.padEnd(32, "0").slice(0, 32));

    const cryptoKey1 = await crypto.subtle.importKey("raw", keyBytes1, { name: "AES-GCM" }, false, ["decrypt"]);
    const cryptoKey2 = fallbackKeyString
      ? await crypto.subtle.importKey("raw", keyBytes2, { name: "AES-GCM" }, false, ["decrypt"])
      : null;

    const decodeIvFromB64 = (ivB64: string) => Uint8Array.from(atob(ivB64), (c) => c.charCodeAt(0));

    async function decryptWithKey(encrypted: string, key: CryptoKey, iv: Uint8Array): Promise<string> {
      const encryptedBytes = Uint8Array.from(atob(encrypted), (c) => c.charCodeAt(0));
      const decrypted = await crypto.subtle.decrypt({ name: "AES-GCM", iv: iv as unknown as BufferSource }, key, encryptedBytes);
      return new TextDecoder().decode(decrypted);
    }

    async function decryptCredential(encrypted: string, iv: Uint8Array): Promise<string> {
      try {
        return await decryptWithKey(encrypted, cryptoKey1, iv);
      } catch {
        if (cryptoKey2) {
          try {
            return await decryptWithKey(encrypted, cryptoKey2, iv);
          } catch { /* continue */ }
        }
        try {
          return atob(encrypted);
        } catch {
          throw new Error("Credential decryption failed");
        }
      }
    }

    // Fetch prices for USD conversion
    const pricesRes = await fetch("https://api.binance.com/api/v3/ticker/price");
    const allPrices = pricesRes.ok ? await pricesRes.json() : [];
    const priceMap: Record<string, number> = {};
    for (const p of allPrices) priceMap[p.symbol] = parseFloat(p.price);

    function getUsdValue(asset: string, total: number): number {
      if (asset === "USDT" || asset === "USDC" || asset === "BUSD" || asset === "USD") return total;
      const usdtPair = `${asset}USDT`;
      const btcPair = `${asset}BTC`;
      if (priceMap[usdtPair]) return total * priceMap[usdtPair];
      if (priceMap[btcPair] && priceMap["BTCUSDT"]) return total * priceMap[btcPair] * priceMap["BTCUSDT"];
      return 0;
    }

    const allPositions: SpotPosition[] = [];
    const errors: string[] = [];

    // ========== BINANCE ==========
    if (session.binance_api_key_encrypted && session.binance_api_secret_encrypted && session.binance_iv) {
      try {
        const binanceIv = decodeIvFromB64(session.binance_iv);
        const binanceApiKey = (await decryptCredential(session.binance_api_key_encrypted, binanceIv)).trim();
        const binanceApiSecret = (await decryptCredential(session.binance_api_secret_encrypted, binanceIv)).trim();

        if (isPrintableAscii(binanceApiKey) && isPrintableAscii(binanceApiSecret) && binanceApiKey.length >= 16) {
          const timestamp = Date.now();
          const queryString = `timestamp=${timestamp}`;
          const signature = createHmac("sha256", binanceApiSecret).update(queryString).digest("hex");

          const accountRes = await fetch(`https://api.binance.com/api/v3/account?${queryString}&signature=${signature}`, {
            headers: { "X-MBX-APIKEY": binanceApiKey },
          });

          if (accountRes.ok) {
            const accountData = await accountRes.json();
            const balances = accountData.balances || [];
            for (const b of balances) {
              const free = parseFloat(b.free || "0");
              const locked = parseFloat(b.locked || "0");
              const total = free + locked;
              if (total > 0) {
                allPositions.push({
                  asset: b.asset,
                  free,
                  locked,
                  total,
                  usdValue: getUsdValue(b.asset, total),
                  exchange: "binance",
                });
              }
            }
          } else {
            errors.push(`Binance: ${accountRes.status}`);
          }
        } else {
          errors.push("Binance: Invalid credentials");
        }
      } catch (e: any) {
        errors.push(`Binance: ${e.message}`);
      }
    }

    // ========== KRAKEN ==========
    // IMPORTANT: Avoid hammering Kraken private endpoints.
    // We reuse the existing database-backed cache populated by the portfolio balance fetch.
    // This prevents concurrent Balance calls (which can instantly trigger Kraken rate limits).
    {
      try {
        const { data: cachedRow } = await supabase
          .from("exchange_balance_cache")
          .select("balance_data, cached_at")
          .eq("user_id", user.id)
          .eq("exchange", "kraken")
          .single();

        const cachedAt = cachedRow?.cached_at ? new Date(cachedRow.cached_at).getTime() : 0;
        const isFresh = cachedAt > 0 && Date.now() - cachedAt < 5 * 60 * 1000; // 5 minutes
        const cachedBalance = cachedRow?.balance_data as any;

        if (isFresh && cachedBalance?.assets && Array.isArray(cachedBalance.assets)) {
          for (const a of cachedBalance.assets) {
            const free = parseFloat(String(a.free ?? 0));
            const locked = parseFloat(String(a.locked ?? 0));
            const total = free + locked;
            if (total > 0) {
              allPositions.push({
                asset: String(a.asset),
                free,
                locked,
                total,
                usdValue: parseFloat(String(a.usdValue ?? 0)) || 0,
                exchange: "kraken",
              });
            }
          }
        } else {
          // Don’t call Kraken here; portfolio sync will populate the cache.
          errors.push("Kraken: Waiting for portfolio sync (rate-limit protection)");
        }
      } catch (e: any) {
        errors.push(`Kraken: ${e?.message || "Cache read failed"}`);
      }
    }

    // Sort by USD value descending
    allPositions.sort((a, b) => b.usdValue - a.usdValue);
    const totalUsdValue = allPositions.reduce((sum, p) => sum + p.usdValue, 0);

    return new Response(
      JSON.stringify({
        success: true,
        positions: allPositions,
        totalUsdValue,
        positionCount: allPositions.length,
        exchanges: {
          binance: allPositions.filter((p) => p.exchange === "binance").length > 0,
          kraken: allPositions.filter((p) => p.exchange === "kraken").length > 0,
        },
        errors: errors.length > 0 ? errors : undefined,
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error: any) {
    console.error("fetch-open-positions error:", error);
    return new Response(JSON.stringify({ error: error?.message || String(error) }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
