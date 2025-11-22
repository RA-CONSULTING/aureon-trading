import { useEffect, useRef, useState } from 'react';
import { QGITASignal } from '@/core/qgitaSignalGenerator';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { useQueenHive } from '@/hooks/useQueenHive';

interface QGITAAutoTradingProps {
  signal: QGITASignal | null;
  symbol: string;
  currentPrice: number;
  enabled: boolean;
}

const STORAGE_KEY = 'qgita-auto-trading-enabled';

// CRITICAL FAIL-SAFE CONSTANTS (per Strategic Plan)
const MAX_PRICE_AGE_MS = 2000; // Kill switch if data older than 2s
const MAX_ORDERS_PER_10S = 5; // Conservative limit to stay under Binance 100/10s
const CIRCUIT_BREAKER_FAILURES = 3; // Trip after 3 consecutive failures
const CIRCUIT_BREAKER_RESET_MS = 60000; // Reset after 1 minute

// Order rate limiting tracker
const orderTimestamps: number[] = [];
let consecutiveFailures = 0;
let circuitBreakerTrippedUntil = 0;

export function useQGITAAutoTrading({ signal, symbol, currentPrice, enabled }: QGITAAutoTradingProps) {
  const { toast } = useToast();
  const { session: hiveSession } = useQueenHive();
  const [isExecuting, setIsExecuting] = useState(false);
  const lastExecutedSignalRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled || !signal || !currentPrice) return;

    // Only execute Tier 1 or Tier 2 signals
    if (signal.tier === 3 || signal.signalType === 'HOLD') return;

    // Prevent duplicate executions
    const signalKey = `${signal.timestamp}-${signal.signalType}-${signal.confidence}`;
    if (lastExecutedSignalRef.current === signalKey) return;

    // === CRITICAL FAIL-SAFES (Strategic Plan: "Fail Safe, Not Fail Open") ===
    
    // 1. DATA QUALITY CHECK: Kill switch if data is stale (>2s old)
    const dataAge = Date.now() - signal.timestamp;
    if (dataAge > MAX_PRICE_AGE_MS) {
      console.warn(`🛑 KILL SWITCH: Data too old (${dataAge}ms). Aborting trade.`);
      toast({
        title: "🛑 Trade Aborted",
        description: `Data latency too high (${dataAge}ms). Trading halted for safety.`,
        variant: "destructive",
      });
      return;
    }

    // 2. PRICE VALIDATION: Reject invalid prices
    if (!currentPrice || isNaN(currentPrice) || currentPrice <= 0) {
      console.error('🛑 KILL SWITCH: Invalid price data', currentPrice);
      toast({
        title: "🛑 Trade Aborted",
        description: "Invalid price data detected. Trading halted.",
        variant: "destructive",
      });
      return;
    }

    // 3. CIRCUIT BREAKER: Stop trading if too many recent failures
    const now = Date.now();
    if (now < circuitBreakerTrippedUntil) {
      const remainingSeconds = Math.ceil((circuitBreakerTrippedUntil - now) / 1000);
      console.warn(`🔥 CIRCUIT BREAKER ACTIVE: ${remainingSeconds}s remaining`);
      toast({
        title: "🔥 Circuit Breaker Active",
        description: `Auto-trading paused due to failures. Resumes in ${remainingSeconds}s.`,
        variant: "destructive",
      });
      return;
    }

    // 4. QUEEN-HIVE SESSION CHECK: OMS requires active session
    if (!hiveSession || hiveSession.status !== 'running') {
      console.warn('⏸️ No active Queen-Hive session. Start a session to enable QGITA auto-trading.');
      toast({
        title: "⏸️ No Active Session",
        description: "Start a Queen-Hive session to enable QGITA auto-trading.",
        variant: "destructive",
      });
      return;
    }

    executeQGITATrade();

    async function executeQGITATrade() {
      if (isExecuting) return;

      try {
        setIsExecuting(true);
        lastExecutedSignalRef.current = signalKey;

        // Calculate priority based on signal quality (0-100)
        // Tier 1 (80-100% confidence) → Priority 80-100
        // Tier 2 (60-79% confidence) → Priority 60-79
        // Tier 3 (<60% confidence) → Priority 40-59
        let priority = Math.floor(signal.confidence);
        
        // Boost priority for exceptional signals
        if (signal.ftcpDetected) priority = Math.min(100, priority + 10);
        if (signal.coherence.crossScaleCoherence > 0.95) priority = Math.min(100, priority + 5);
        if (signal.lighthouse.L > 0.95) priority = Math.min(100, priority + 5);
        
        // Calculate position size based on tier
        const tierMultiplier = signal.tier === 1 ? 1.0 : signal.tier === 2 ? 0.5 : 0.25;
        const baseSize = 100; // $100 base position
        const positionSize = baseSize * tierMultiplier;
        const quantity = positionSize / currentPrice;

        toast({
          title: "📋 QGITA → OMS Queue",
          description: `Queuing ${signal.signalType} signal (Tier ${signal.tier}, P${priority}, ${signal.confidence.toFixed(1)}%)`,
        });

        // Get active hive and agent (use first available)
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

        // Enqueue order via OMS with priority
        const { data, error } = await supabase.functions.invoke('oms-leaky-bucket', {
          body: {
            action: 'enqueue',
            sessionId: hiveSession!.id,
            hiveId: hives.id,
            agentId: agent.id,
            symbol,
            side: signal.signalType,
            quantity,
            price: currentPrice,
            priority,
            metadata: {
              signalStrength: signal.confidence,
              coherence: signal.coherence.crossScaleCoherence,
              lighthouseValue: signal.lighthouse.L,
              lighthouseConfidence: signal.lighthouse.confidence,
              prismLevel: 5,
              qgitaTier: signal.tier,
              qgitaCurvature: signal.curvature,
              qgitaFTCP: signal.ftcpDetected,
              qgitaGoldenRatio: signal.goldenRatioScore,
              qgitaAnomaly: signal.anomalyPointer,
              reasoning: signal.reasoning,
            },
          },
        });

        if (error) throw error;

        if (data.success) {
          // SUCCESS: Reset failure counter
          consecutiveFailures = 0;

          toast({
            title: "✅ Order Queued",
            description: `${signal.signalType} order queued via OMS (Position #${data.position}, Priority ${priority})`,
          });

          console.log('QGITA order enqueued:', {
            orderId: data.orderId,
            position: data.position,
            priority,
            tier: signal.tier,
            confidence: signal.confidence,
          });
        }

      } catch (error) {
        console.error('QGITA OMS queueing error:', error);
        
        // FAILURE: Increment counter and potentially trip circuit breaker
        consecutiveFailures++;
        
        if (consecutiveFailures >= CIRCUIT_BREAKER_FAILURES) {
          circuitBreakerTrippedUntil = Date.now() + CIRCUIT_BREAKER_RESET_MS;
          console.error(`🔥 CIRCUIT BREAKER TRIPPED after ${consecutiveFailures} failures. Trading halted for ${CIRCUIT_BREAKER_RESET_MS/1000}s.`);
          toast({
            title: "🔥 Circuit Breaker Tripped",
            description: `Auto-trading paused after ${consecutiveFailures} failures. Will retry in ${CIRCUIT_BREAKER_RESET_MS/1000}s.`,
            variant: "destructive",
          });
          // Reset counter after circuit breaker trip
          consecutiveFailures = 0;
        } else {
          toast({
            title: "❌ Failed to Queue Order",
            description: error instanceof Error ? error.message : 'Failed to queue QGITA trade',
            variant: "destructive",
          });
        }
      } finally {
        setIsExecuting(false);
      }
    }
  }, [enabled, signal, symbol, currentPrice, toast, isExecuting]);

  return {
    isExecuting,
  };
}

export function useQGITAAutoTradingToggle() {
  const [isEnabled, setIsEnabled] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored === 'true';
    } catch {
      return false;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(isEnabled));
    } catch (error) {
      console.error('Failed to save QGITA auto-trading state:', error);
    }
  }, [isEnabled]);

  return {
    isEnabled,
    setIsEnabled,
  };
}
