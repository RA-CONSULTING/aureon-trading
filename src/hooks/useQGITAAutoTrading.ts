import { useEffect, useRef, useState } from 'react';
import { QGITASignal } from '@/core/qgitaSignalGenerator';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

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

    // 4. RATE LIMIT COMPLIANCE: Binance 100 orders/10s (we use conservative 5/10s)
    const tenSecondsAgo = now - 10000;
    const recentOrders = orderTimestamps.filter(ts => ts > tenSecondsAgo);
    if (recentOrders.length >= MAX_ORDERS_PER_10S) {
      console.warn(`⏸️ RATE LIMIT: ${recentOrders.length}/${MAX_ORDERS_PER_10S} orders in last 10s`);
      toast({
        title: "⏸️ Rate Limit Protection",
        description: `Order queued. ${recentOrders.length} orders in last 10s.`,
      });
      // Queue for next window (simplified - production needs priority queue)
      setTimeout(() => executeQGITATrade(), 2000);
      return;
    }

    executeQGITATrade();

    async function executeQGITATrade() {
      if (isExecuting) return;

      try {
        setIsExecuting(true);
        lastExecutedSignalRef.current = signalKey;

        // Track order timestamp for rate limiting
        orderTimestamps.push(Date.now());
        // Clean up old timestamps (keep only last 10s)
        while (orderTimestamps.length > 0 && orderTimestamps[0] < Date.now() - 10000) {
          orderTimestamps.shift();
        }

        toast({
          title: "🎯 QGITA Auto-Trading",
          description: `Executing ${signal.signalType} signal (Tier ${signal.tier}, ${signal.confidence.toFixed(1)}% confidence)`,
        });

        const { data, error } = await supabase.functions.invoke('execute-trade', {
          body: {
            symbol,
            signalType: signal.signalType,
            price: currentPrice,
            coherence: signal.coherence.crossScaleCoherence,
            lighthouseValue: signal.lighthouse.L,
            lighthouseConfidence: signal.lighthouse.confidence,
            prismLevel: 5, // QGITA signals are high-quality
            signalStrength: signal.confidence,
            signalReasoning: signal.reasoning,
            // QGITA-specific metadata
            qgitaTier: signal.tier,
            qgitaCurvature: signal.curvature,
            qgitaFTCP: signal.ftcpDetected,
            qgitaGoldenRatio: signal.goldenRatioScore,
          },
        });

        if (error) throw error;

        // SUCCESS: Reset failure counter
        consecutiveFailures = 0;

        toast({
          title: "✅ Trade Executed",
          description: `${signal.signalType} order placed successfully via QGITA auto-trading`,
        });

        console.log('QGITA Auto-Trade executed:', data);

      } catch (error) {
        console.error('QGITA Auto-Trading error:', error);
        
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
            title: "❌ Auto-Trade Failed",
            description: error instanceof Error ? error.message : 'Failed to execute QGITA trade',
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
