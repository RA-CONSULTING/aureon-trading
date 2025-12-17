import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.49.4";
import { createHmac } from "node:crypto";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface PositionWithPnL {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  entryPrice: number;
  quantity: number;
  positionValueUsdt: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
  openedAt: string;
  exchange: string;
  // Fees & costs
  entryFee: number;
  gasCost: number;
  totalCosts: number;
  // Net P&L after costs
  netPnl: number;
  // Duration
  holdingDurationMs: number;
  holdingDurationFormatted: string;
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

    // Fetch user's open positions
    const { data: positions, error: posError } = await supabase
      .from("trading_positions")
      .select("*")
      .eq("user_id", user.id)
      .eq("status", "open")
      .order("opened_at", { ascending: false });

    if (posError) {
      console.error("Error fetching positions:", posError);
      return new Response(JSON.stringify({ error: "Failed to fetch positions" }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    if (!positions || positions.length === 0) {
      return new Response(JSON.stringify({
        success: true,
        positions: [],
        summary: { totalPnl: 0, totalCosts: 0, netPnl: 0, positionCount: 0 },
      }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Fetch current prices from Binance
    const pricesRes = await fetch("https://api.binance.com/api/v3/ticker/price");
    const allPrices = pricesRes.ok ? await pricesRes.json() : [];
    const priceMap: Record<string, number> = {};
    for (const p of allPrices) priceMap[p.symbol] = parseFloat(p.price);

    // Fetch related trade audit data for fees
    const executionIds = positions.map((p: any) => p.execution_id).filter(Boolean);
    let feeMap: Record<string, number> = {};
    
    if (executionIds.length > 0) {
      const { data: audits } = await supabase
        .from("trade_audit_log")
        .select("trade_id, commission")
        .in("trade_id", executionIds);
      
      if (audits) {
        for (const a of audits) {
          feeMap[a.trade_id] = parseFloat(a.commission || "0");
        }
      }
    }

    // Fetch gas tank transactions for this user
    const { data: gasTankAccount } = await supabase
      .from("gas_tank_accounts")
      .select("id")
      .eq("user_id", user.id)
      .single();

    let gasMap: Record<string, number> = {};
    if (gasTankAccount && executionIds.length > 0) {
      const { data: gasTxns } = await supabase
        .from("gas_tank_transactions")
        .select("trade_execution_id, amount")
        .eq("account_id", gasTankAccount.id)
        .eq("type", "FEE_DEDUCTION")
        .in("trade_execution_id", executionIds);
      
      if (gasTxns) {
        for (const g of gasTxns) {
          gasMap[g.trade_execution_id] = Math.abs(parseFloat(g.amount || "0"));
        }
      }
    }

    // Calculate P&L for each position
    const enrichedPositions: PositionWithPnL[] = positions.map((pos: any) => {
      const currentPrice = priceMap[pos.symbol] || pos.current_price || pos.entry_price;
      const entryPrice = parseFloat(pos.entry_price);
      const quantity = parseFloat(pos.quantity);
      const positionValue = parseFloat(pos.position_value_usdt);

      // Calculate unrealized P&L
      let unrealizedPnl = 0;
      if (pos.side === "BUY" || pos.side === "LONG") {
        unrealizedPnl = (currentPrice - entryPrice) * quantity;
      } else {
        unrealizedPnl = (entryPrice - currentPrice) * quantity;
      }
      
      const unrealizedPnlPct = positionValue > 0 ? (unrealizedPnl / positionValue) * 100 : 0;

      // Get fees and gas
      const entryFee = feeMap[pos.execution_id] || 0;
      const gasCost = gasMap[pos.execution_id] || 0;
      const totalCosts = entryFee + gasCost;
      const netPnl = unrealizedPnl - totalCosts;

      // Calculate holding duration
      const openedAt = new Date(pos.opened_at);
      const holdingDurationMs = Date.now() - openedAt.getTime();
      const holdingDurationFormatted = formatDuration(holdingDurationMs);

      return {
        id: pos.id,
        symbol: pos.symbol,
        side: pos.side,
        entryPrice,
        quantity,
        positionValueUsdt: positionValue,
        currentPrice,
        unrealizedPnl,
        unrealizedPnlPct,
        openedAt: pos.opened_at,
        exchange: "binance", // TODO: get from position
        entryFee,
        gasCost,
        totalCosts,
        netPnl,
        holdingDurationMs,
        holdingDurationFormatted,
      };
    });

    // Calculate summary
    const totalPnl = enrichedPositions.reduce((sum, p) => sum + p.unrealizedPnl, 0);
    const totalCosts = enrichedPositions.reduce((sum, p) => sum + p.totalCosts, 0);
    const netPnl = totalPnl - totalCosts;

    return new Response(JSON.stringify({
      success: true,
      positions: enrichedPositions,
      summary: {
        totalPnl,
        totalCosts,
        netPnl,
        positionCount: enrichedPositions.length,
      },
    }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (error: any) {
    console.error("fetch-positions-pnl error:", error);
    return new Response(JSON.stringify({ error: error?.message || String(error) }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});

function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ${hours % 24}h`;
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}
