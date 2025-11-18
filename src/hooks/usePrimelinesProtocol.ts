import { useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { getTemporalId, getSentinelName } from '@/core/primelinesIdentity';
import { useToast } from '@/hooks/use-toast';

export type ProtocolOperation = 
  | 'SYNC_HARMONIC_NEXUS'
  | 'VALIDATE_LIGHTHOUSE_EVENT'
  | 'EXECUTE_TRADE'
  | 'LOCK_CASIMIR_FIELD'
  | 'QUERY_HISTORICAL_NODES';

export interface ProtocolRequest {
  operation: ProtocolOperation;
  payload: any;
  requireValidation?: boolean;
}

export interface ProtocolResponse {
  success: boolean;
  operation: string;
  temporalId: string;
  sentinelName: string;
  identityValid: boolean;
  aiValidation?: {
    valid: boolean;
    coherence: number;
    resonance: number;
    recommendation: string;
  };
  result: any;
  timestamp: string;
  error?: string;
}

export function usePrimelinesProtocol() {
  const { toast } = useToast();
  const temporalId = getTemporalId();
  const sentinelName = getSentinelName();

  const invokeProtocol = useCallback(async (
    request: ProtocolRequest
  ): Promise<ProtocolResponse> => {
    console.log('🌀 Invoking Primelines Protocol:', request.operation);
    console.log('🔑 Temporal ID:', temporalId);
    console.log('🛡️ Sentinel:', sentinelName);

    try {
      const { data, error } = await supabase.functions.invoke('primelines-protocol-gateway', {
        body: {
          ...request,
          temporalId,
          sentinelName,
        },
      });

      if (error) {
        console.error('❌ Protocol error:', error);
        throw error;
      }

      if (!data.success) {
        console.error('❌ Protocol validation failed:', data);
        toast({
          title: "Protocol Validation Failed",
          description: data.error || "Operation rejected by Primelines Gateway",
          variant: "destructive",
        });
      } else {
        console.log('✅ Protocol response:', data);
        
        // Show AI validation if present
        if (data.aiValidation) {
          const { valid, coherence, resonance, recommendation } = data.aiValidation;
          console.log(`🤖 AI Validation: ${valid ? '✅' : '❌'}`);
          console.log(`   Coherence: ${(coherence * 100).toFixed(1)}%`);
          console.log(`   Resonance: ${resonance} Hz`);
          console.log(`   Recommendation: ${recommendation}`);
        }
      }

      return data;
    } catch (error) {
      console.error('❌ Failed to invoke protocol:', error);
      toast({
        title: "Protocol Error",
        description: error instanceof Error ? error.message : "Failed to connect to Primelines Gateway",
        variant: "destructive",
      });
      throw error;
    }
  }, [temporalId, sentinelName, toast]);

  const syncHarmonicNexus = useCallback(async (harmonicState: any) => {
    return invokeProtocol({
      operation: 'SYNC_HARMONIC_NEXUS',
      payload: { harmonicState },
      requireValidation: true,
    });
  }, [invokeProtocol]);

  const validateLighthouseEvent = useCallback(async (lighthouseEvent: any) => {
    return invokeProtocol({
      operation: 'VALIDATE_LIGHTHOUSE_EVENT',
      payload: { lighthouseEvent },
      requireValidation: true,
    });
  }, [invokeProtocol]);

  const validateTradeExecution = useCallback(async (tradeSignal: any) => {
    return invokeProtocol({
      operation: 'EXECUTE_TRADE',
      payload: { tradeSignal },
      requireValidation: true,
    });
  }, [invokeProtocol]);

  const lockCasimirField = useCallback(async (nodeCount: number, resonanceFrequency: number) => {
    return invokeProtocol({
      operation: 'LOCK_CASIMIR_FIELD',
      payload: { nodeCount, resonanceFrequency },
      requireValidation: true,
    });
  }, [invokeProtocol]);

  const queryHistoricalNodes = useCallback(async (limit = 50, minCoherence = 0) => {
    return invokeProtocol({
      operation: 'QUERY_HISTORICAL_NODES',
      payload: { limit, minCoherence },
      requireValidation: false, // Query operations don't need validation
    });
  }, [invokeProtocol]);

  return {
    invokeProtocol,
    syncHarmonicNexus,
    validateLighthouseEvent,
    validateTradeExecution,
    lockCasimirField,
    queryHistoricalNodes,
    temporalId,
    sentinelName,
  };
}
