import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT'];
const AGENTS_PER_HIVE = 5;
const SPAWN_MULTIPLIER = 5; // Spawn new hive at 5x growth
const HARVEST_PERCENTAGE = 0.10; // Harvest 10% for new hive
const MAX_GENERATIONS = 3; // Prevent exponential explosion

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      throw new Error('Missing authorization header');
    }

    // Get user from JWT
    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: userError } = await supabase.auth.getUser(token);
    if (userError || !user) {
      throw new Error('Unauthorized');
    }

    const { action, sessionId, initialCapital, maxSteps = 100 } = await req.json();
    console.log(`Queen-Hive ${action} request:`, { user: user.id, sessionId, initialCapital });

    if (action === 'start') {
      // === START NEW QUEEN-HIVE SESSION ===
      if (!initialCapital || initialCapital < 10) {
        return new Response(
          JSON.stringify({ success: false, error: 'Minimum capital: $10' }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
        );
      }

      // Create root hive
      const { data: rootHive, error: hiveError } = await supabase
        .from('hive_instances')
        .insert({
          generation: 0,
          initial_balance: initialCapital,
          current_balance: initialCapital,
          num_agents: AGENTS_PER_HIVE,
          status: 'active',
        })
        .select()
        .single();

      if (hiveError || !rootHive) {
        console.error('Failed to create root hive:', hiveError);
        throw new Error('Failed to create hive');
      }

      // Create agents for root hive
      const agents = Array.from({ length: AGENTS_PER_HIVE }, (_, i) => ({
        hive_id: rootHive.id,
        agent_index: i,
        current_symbol: SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
        position_open: false,
      }));

      const { error: agentsError } = await supabase
        .from('hive_agents')
        .insert(agents);

      if (agentsError) {
        console.error('Failed to create agents:', agentsError);
        throw new Error('Failed to create agents');
      }

      // Create session
      const { data: session, error: sessionError } = await supabase
        .from('hive_sessions')
        .insert({
          user_id: user.id,
          root_hive_id: rootHive.id,
          initial_capital: initialCapital,
          current_equity: initialCapital,
          status: 'running',
        })
        .select()
        .single();

      if (sessionError || !session) {
        console.error('Failed to create session:', sessionError);
        throw new Error('Failed to create session');
      }

      console.log(`✅ Queen-Hive session started: ${session.id}`);

      return new Response(
        JSON.stringify({
          success: true,
          session: session,
          message: `Queen-Hive deployed with ${AGENTS_PER_HIVE} agents and $${initialCapital} capital`,
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'step') {
      // === EXECUTE ONE TRADING STEP ===
      if (!sessionId) {
        throw new Error('sessionId required for step action');
      }

      // Get session
      const { data: session, error: sessionError } = await supabase
        .from('hive_sessions')
        .select('*')
        .eq('id', sessionId)
        .eq('user_id', user.id)
        .single();

      if (sessionError || !session) {
        throw new Error('Session not found');
      }

      if (session.status !== 'running') {
        return new Response(
          JSON.stringify({ success: false, error: `Session is ${session.status}` }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
        );
      }

      // Get all active hives
      const { data: hives } = await supabase
        .from('hive_instances')
        .select('*')
        .eq('status', 'active')
        .or(`id.eq.${session.root_hive_id},parent_hive_id.eq.${session.root_hive_id}`);

      if (!hives || hives.length === 0) {
        throw new Error('No active hives found');
      }

      // Get all agents
      const hiveIds = hives.map(h => h.id);
      const { data: agents } = await supabase
        .from('hive_agents')
        .select('*')
        .in('hive_id', hiveIds);

      if (!agents || agents.length === 0) {
        throw new Error('No agents found');
      }

      // Execute trades for each agent (simplified - paper trading simulation)
      let totalTrades = 0;
      for (const agent of agents) {
        // Random decision: 30% chance to trade
        if (Math.random() > 0.7) {
          const hive = hives.find(h => h.id === agent.hive_id);
          if (!hive) continue;

          // Simulate trade
          const side = Math.random() > 0.5 ? 'BUY' : 'SELL';
          const price = 50000 + Math.random() * 10000; // Mock price
          const positionSize = hive.current_balance * 0.01; // 1% risk
          const quantity = positionSize / price;

          // Simulate P&L (random walk)
          const pnl = positionSize * (Math.random() * 0.04 - 0.02); // ±2% return

          // Update agent
          await supabase
            .from('hive_agents')
            .update({
              trades_count: agent.trades_count + 1,
              total_pnl: agent.total_pnl + pnl,
              last_trade_at: new Date().toISOString(),
              current_symbol: SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
            })
            .eq('id', agent.id);

          // Update hive balance
          const newBalance = hive.current_balance + pnl;
          await supabase
            .from('hive_instances')
            .update({ current_balance: newBalance, updated_at: new Date().toISOString() })
            .eq('id', hive.id);

          // Record trade
          await supabase
            .from('hive_trades')
            .insert({
              session_id: sessionId,
              hive_id: hive.id,
              agent_id: agent.id,
              symbol: agent.current_symbol,
              side,
              entry_price: price,
              exit_price: price * (1 + (Math.random() * 0.04 - 0.02)),
              quantity,
              pnl,
              status: 'closed',
              closed_at: new Date().toISOString(),
            });

          totalTrades++;
        }
      }

      // Check hive spawning conditions
      for (const hive of hives) {
        const growthMultiplier = hive.current_balance / hive.initial_balance;
        
        if (
          growthMultiplier >= SPAWN_MULTIPLIER &&
          hive.generation < MAX_GENERATIONS &&
          hive.status === 'active'
        ) {
          // Spawn new hive by harvesting 10%
          const harvestAmount = hive.current_balance * HARVEST_PERCENTAGE;
          const remainingBalance = hive.current_balance - harvestAmount;

          // Create child hive
          const { data: childHive } = await supabase
            .from('hive_instances')
            .insert({
              parent_hive_id: hive.id,
              generation: hive.generation + 1,
              initial_balance: harvestAmount,
              current_balance: harvestAmount,
              num_agents: AGENTS_PER_HIVE,
              status: 'active',
            })
            .select()
            .single();

          if (childHive) {
            // Create agents for child hive
            const childAgents = Array.from({ length: AGENTS_PER_HIVE }, (_, i) => ({
              hive_id: childHive.id,
              agent_index: i,
              current_symbol: SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
              position_open: false,
            }));

            await supabase.from('hive_agents').insert(childAgents);

            // Update parent hive balance
            await supabase
              .from('hive_instances')
              .update({ current_balance: remainingBalance })
              .eq('id', hive.id);

            // Update session stats
            await supabase
              .from('hive_sessions')
              .update({
                total_hives_spawned: session.total_hives_spawned + 1,
                total_agents: session.total_agents + AGENTS_PER_HIVE,
              })
              .eq('id', sessionId);

            console.log(`🐝 New hive spawned! Gen ${childHive.generation} with $${harvestAmount}`);
          }
        }
      }

      // Calculate total equity
      const totalEquity = hives.reduce((sum, h) => sum + parseFloat(h.current_balance), 0);

      // Update session
      await supabase
        .from('hive_sessions')
        .update({
          current_equity: totalEquity,
          total_trades: session.total_trades + totalTrades,
          steps_executed: session.steps_executed + 1,
        })
        .eq('id', sessionId);

      return new Response(
        JSON.stringify({
          success: true,
          step: session.steps_executed + 1,
          trades: totalTrades,
          equity: totalEquity,
          hives: hives.length,
          agents: agents.length,
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'stop') {
      // === STOP SESSION ===
      if (!sessionId) {
        throw new Error('sessionId required for stop action');
      }

      await supabase
        .from('hive_sessions')
        .update({
          status: 'stopped',
          stopped_at: new Date().toISOString(),
        })
        .eq('id', sessionId)
        .eq('user_id', user.id);

      return new Response(
        JSON.stringify({ success: true, message: 'Session stopped' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    if (action === 'status') {
      // === GET SESSION STATUS ===
      if (!sessionId) {
        throw new Error('sessionId required for status action');
      }

      const { data: session } = await supabase
        .from('hive_sessions')
        .select('*')
        .eq('id', sessionId)
        .eq('user_id', user.id)
        .single();

      if (!session) {
        throw new Error('Session not found');
      }

      // Get hives
      const { data: hives } = await supabase
        .from('hive_instances')
        .select('*')
        .or(`id.eq.${session.root_hive_id},parent_hive_id.eq.${session.root_hive_id}`);

      // Get agents
      const hiveIds = hives?.map(h => h.id) || [];
      const { data: agents } = await supabase
        .from('hive_agents')
        .select('*')
        .in('hive_id', hiveIds);

      return new Response(
        JSON.stringify({
          success: true,
          session,
          hives: hives || [],
          agents: agents || [],
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    throw new Error(`Unknown action: ${action}`);

  } catch (error) {
    console.error('Queen-Hive orchestrator error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
