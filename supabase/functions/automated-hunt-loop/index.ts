import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const binanceKey = Deno.env.get('BINANCE_API_KEY');
    const supabase = createClient(supabaseUrl, supabaseKey);

    const authHeader = req.headers.get('Authorization');
    const { action, huntSessionId } = await req.json();
    
    console.log(`Hunt Loop ${action} request:`, { huntSessionId });

    if (action === 'scan') {
      // === PRIDE SCANNER: Find opportunities across all markets ===
      if (!huntSessionId) throw new Error('huntSessionId required');

      const scanStart = Date.now();

      // Get hunt session
      const { data: huntSession, error: sessionError } = await supabase
        .from('hunt_sessions')
        .select('*, hive_sessions!inner(*)')
        .eq('id', huntSessionId)
        .single();

      if (sessionError || !huntSession) {
        throw new Error('Hunt session not found');
      }

      if (huntSession.status !== 'active') {
        return new Response(
          JSON.stringify({ success: false, error: 'Hunt session not active' }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 }
        );
      }

      // Get active hive and agent
      const { data: hives } = await supabase
        .from('hive_instances')
        .select('id')
        .eq('status', 'active')
        .limit(1)
        .single();

      if (!hives) {
        throw new Error('No active hive found');
      }

      const { data: agent } = await supabase
        .from('hive_agents')
        .select('id')
        .eq('hive_id', hives.id)
        .limit(1)
        .single();

      if (!agent) {
        throw new Error('No active agent found');
      }

      // Fetch market data from Binance
      const tickerResponse = await fetch('https://api.binance.com/api/v3/ticker/24hr');
      if (!tickerResponse.ok) {
        throw new Error('Failed to fetch Binance market data');
      }

      const tickers = await tickerResponse.json();
      console.log(`Fetched ${tickers.length} market pairs`);

      // Filter and score opportunities
      const opportunities = [];
      for (const ticker of tickers) {
        // Only USDT pairs for simplicity
        if (!ticker.symbol.endsWith('USDT')) continue;

        const price = parseFloat(ticker.lastPrice);
        const volume24h = parseFloat(ticker.quoteVolume);
        const priceChange = parseFloat(ticker.priceChangePercent);
        
        // Calculate volatility as abs(price change)
        const volatility = Math.abs(priceChange);

        // Filter by minimum thresholds
        if (volatility < huntSession.min_volatility_pct) continue;
        if (volume24h < huntSession.min_volume_usd) continue;

        // Opportunity score = volatility × volume (normalized)
        const opportunityScore = volatility * (volume24h / 1000000);

        opportunities.push({
          symbol: ticker.symbol,
          baseAsset: ticker.symbol.replace('USDT', ''),
          quoteAsset: 'USDT',
          price,
          volume24h,
          volatility24h: volatility,
          opportunityScore,
          priceChange,
        });
      }

      // Sort by opportunity score and take top N
      opportunities.sort((a, b) => b.opportunityScore - a.opportunityScore);
      const topTargets = opportunities.slice(0, huntSession.max_targets);

      console.log(`Found ${topTargets.length} targets out of ${opportunities.length} candidates`);

      let signalsGenerated = 0;
      let ordersQueued = 0;

      // Process each target through QGITA → OMS pipeline
      for (const target of topTargets) {
        let savedTargetId: string | null = null;
        
        try {
          // Save target to database
          const { data: savedTarget } = await supabase
            .from('hunt_targets')
            .insert({
              hunt_session_id: huntSessionId,
              symbol: target.symbol,
              base_asset: target.baseAsset,
              quote_asset: target.quoteAsset,
              price: target.price,
              volume_24h: target.volume24h,
              volatility_24h: target.volatility24h,
              opportunity_score: target.opportunityScore,
              status: 'analyzing',
            })
            .select()
            .single();

          if (!savedTarget) continue;
          savedTargetId = savedTarget.id;

          // Generate mock QGITA signal (in production, would call actual QGITA)
          // For now: use volatility direction as signal
          const signalType = target.priceChange > 0 ? 'BUY' : 'SELL';
          
          // Confidence based on volatility strength (higher vol = higher confidence)
          const confidence = Math.min(95, 60 + (target.volatility24h * 2));
          
          // Tier based on confidence
          const tier = confidence >= 80 ? 1 : confidence >= 60 ? 2 : 3;
          
          // Priority = confidence + bonuses
          let priority = Math.floor(confidence);
          if (target.volatility24h > 10) priority = Math.min(100, priority + 10); // High vol bonus
          if (target.volume24h > 10000000) priority = Math.min(100, priority + 5); // High volume bonus

          if (!savedTarget) continue;

          // Update target with signal
          await supabase
            .from('hunt_targets')
            .update({
              status: 'queued',
              signal_generated: true,
              signal_type: signalType,
              signal_confidence: confidence,
              signal_tier: tier,
              processed_at: new Date().toISOString(),
            })
            .eq('id', savedTargetId);

          signalsGenerated++;

          // Only queue Tier 1 and Tier 2 signals
          if (tier <= 2) {
            // Calculate position size based on tier
            const tierMultiplier = tier === 1 ? 1.0 : 0.5;
            const baseSize = 100;
            const positionSize = baseSize * tierMultiplier;
            const quantity = positionSize / target.price;

            // Enqueue via OMS
            const { data: omsResult } = await supabase.functions.invoke('oms-leaky-bucket', {
              body: {
                action: 'enqueue',
                sessionId: huntSession.hive_session_id,
                hiveId: hives.id,
                agentId: agent.id,
                symbol: target.symbol,
                side: signalType,
                quantity,
                price: target.price,
                priority,
                metadata: {
                  signalStrength: confidence,
                  coherence: 0.85 + (tier === 1 ? 0.1 : 0.0),
                  lighthouseValue: 0.9,
                  huntOpportunityScore: target.opportunityScore,
                  volatility24h: target.volatility24h,
                  volume24h: target.volume24h,
                },
              },
            });

            if (omsResult?.success) {
              await supabase
                .from('hunt_targets')
                .update({ order_queued: true })
                .eq('id', savedTargetId);

              ordersQueued++;
              console.log(`✅ ${target.symbol} queued: ${signalType} P${priority} Tier${tier}`);
            }
          } else {
            // Tier 3 signals rejected
            await supabase
              .from('hunt_targets')
              .update({
                status: 'rejected',
                rejection_reason: 'Tier 3 signal (confidence < 60%)',
              })
              .eq('id', savedTargetId);
          }

        } catch (error) {
          console.error(`Failed to process ${target.symbol}:`, error);
          if (savedTargetId) {
            await supabase
              .from('hunt_targets')
              .update({
                status: 'error',
                rejection_reason: error instanceof Error ? error.message : 'Unknown error',
              })
              .eq('id', savedTargetId);
          }
        }
      }

      const scanDuration = Date.now() - scanStart;

      // Record scan history
      await supabase
        .from('hunt_scans')
        .insert({
          hunt_session_id: huntSessionId,
          scan_duration_ms: scanDuration,
          pairs_scanned: tickers.length,
          targets_found: topTargets.length,
          signals_generated: signalsGenerated,
          orders_queued: ordersQueued,
          top_symbol: topTargets[0]?.symbol,
          top_score: topTargets[0]?.opportunityScore,
        });

      // Update hunt session stats
      await supabase
        .from('hunt_sessions')
        .update({
          total_scans: huntSession.total_scans + 1,
          total_targets_found: huntSession.total_targets_found + topTargets.length,
          total_signals_generated: huntSession.total_signals_generated + signalsGenerated,
          total_orders_queued: huntSession.total_orders_queued + ordersQueued,
          last_scan_at: new Date().toISOString(),
        })
        .eq('id', huntSessionId);

      console.log(`🦁 Hunt scan complete: ${topTargets.length} targets, ${signalsGenerated} signals, ${ordersQueued} queued (${scanDuration}ms)`);

      return new Response(
        JSON.stringify({
          success: true,
          scanDuration,
          pairsScanned: tickers.length,
          targetsFound: topTargets.length,
          signalsGenerated,
          ordersQueued,
          topTargets: topTargets.slice(0, 3).map(t => ({
            symbol: t.symbol,
            score: t.opportunityScore.toFixed(2),
            volatility: t.volatility24h.toFixed(2),
            volume: `$${(t.volume24h / 1000000).toFixed(2)}M`,
          })),
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    throw new Error(`Unknown action: ${action}`);

  } catch (error) {
    console.error('Hunt loop error:', error);
    return new Response(
      JSON.stringify({ success: false, error: error instanceof Error ? error.message : 'Unknown error' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    );
  }
});
