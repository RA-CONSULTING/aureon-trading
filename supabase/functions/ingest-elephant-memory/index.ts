import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface SymbolMemory {
  symbol: string;
  trades: number;
  wins: number;
  losses: number;
  profit: number;
  lastTrade: number | null;
  lossStreak: number;
  blacklisted: boolean;
  cooldownUntil: number | null;
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const body = await req.json();
    const { action, data } = body;

    console.log(`[ingest-elephant-memory] Action: ${action}`);

    if (action === 'sync') {
      // Sync all memories from client
      const memories = data.memories as Record<string, SymbolMemory>;
      
      for (const [symbol, memory] of Object.entries(memories)) {
        const { error } = await supabase
          .from('elephant_memory')
          .upsert({
            symbol,
            trades: memory.trades,
            wins: memory.wins,
            losses: memory.losses,
            profit: memory.profit,
            last_trade: memory.lastTrade ? new Date(memory.lastTrade).toISOString() : null,
            loss_streak: memory.lossStreak,
            blacklisted: memory.blacklisted,
            cooldown_until: memory.cooldownUntil ? new Date(memory.cooldownUntil).toISOString() : null,
            updated_at: new Date().toISOString(),
          }, { onConflict: 'symbol' });

        if (error) {
          console.error(`[ingest-elephant-memory] Error syncing ${symbol}:`, error);
        }
      }

      return new Response(
        JSON.stringify({ success: true, synced: Object.keys(memories).length }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'record_trade') {
      // Record a single trade
      const { symbol, profit, side } = data;
      
      // Get existing record or create new one
      const { data: existing } = await supabase
        .from('elephant_memory')
        .select('*')
        .eq('symbol', symbol)
        .single();

      const isWin = profit > 0;
      const newLossStreak = isWin ? 0 : (existing?.loss_streak ?? 0) + 1;
      const newBlacklisted = newLossStreak >= 3;

      const { error } = await supabase
        .from('elephant_memory')
        .upsert({
          symbol,
          trades: (existing?.trades ?? 0) + 1,
          wins: (existing?.wins ?? 0) + (isWin ? 1 : 0),
          losses: (existing?.losses ?? 0) + (isWin ? 0 : 1),
          profit: (existing?.profit ?? 0) + profit,
          last_trade: new Date().toISOString(),
          loss_streak: newLossStreak,
          blacklisted: newBlacklisted,
          cooldown_until: new Date(Date.now() + 15 * 60 * 1000).toISOString(), // 15 min cooldown
          updated_at: new Date().toISOString(),
        }, { onConflict: 'symbol' });

      if (error) {
        throw error;
      }

      return new Response(
        JSON.stringify({ success: true, blacklisted: newBlacklisted }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'fetch') {
      // Fetch all memories from database
      const { data: memories, error } = await supabase
        .from('elephant_memory')
        .select('*')
        .order('updated_at', { ascending: false });

      if (error) {
        throw error;
      }

      return new Response(
        JSON.stringify({ success: true, memories }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'unblacklist') {
      // Remove symbol from blacklist
      const { symbol } = data;
      
      const { error } = await supabase
        .from('elephant_memory')
        .update({
          blacklisted: false,
          loss_streak: 0,
          updated_at: new Date().toISOString(),
        })
        .eq('symbol', symbol);

      if (error) {
        throw error;
      }

      return new Response(
        JSON.stringify({ success: true }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({ error: 'Unknown action' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('[ingest-elephant-memory] Error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ error: message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
