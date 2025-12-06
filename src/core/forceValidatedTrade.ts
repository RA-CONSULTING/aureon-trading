import { supabase } from '@/integrations/supabase/client';

export interface ValidationStep {
  step: number;
  name: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
  timestamp: string;
}

export interface ValidationTrace {
  steps: ValidationStep[];
  startTime: string;
  endTime?: string;
  success: boolean;
  tradeId?: string;
  orderId?: string;
}

export interface ForceTradeResult {
  success: boolean;
  trace: ValidationTrace;
  message: string;
  error?: string;
}

export async function forceValidatedTrade(
  userId: string,
  symbol: string = 'BTCUSDT',
  side: 'BUY' | 'SELL' = 'BUY',
  mode: 'paper' | 'live' = 'paper'
): Promise<ForceTradeResult> {
  console.log('[ForceValidatedTrade] Starting Cycle 1 validation...', { userId, symbol, side, mode });

  try {
    const { data, error } = await supabase.functions.invoke('force-validated-trade', {
      body: { userId, symbol, side, mode },
    });

    if (error) {
      console.error('[ForceValidatedTrade] Edge function error:', error);
      return {
        success: false,
        trace: { steps: [], startTime: new Date().toISOString(), success: false },
        message: `Edge function error: ${error.message}`,
        error: error.message,
      };
    }

    console.log('[ForceValidatedTrade] Validation complete:', data);
    return data as ForceTradeResult;

  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    console.error('[ForceValidatedTrade] Failed:', errorMessage);
    return {
      success: false,
      trace: { steps: [], startTime: new Date().toISOString(), success: false },
      message: `Failed to execute forced validation: ${errorMessage}`,
      error: errorMessage,
    };
  }
}

// Get the last forced validation trade - simplified to avoid type issues
export async function getLastForcedValidation(userId: string): Promise<ValidationTrace | null> {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { data, error } = await (supabase as any)
      .from('trading_executions')
      .select('validation_trace')
      .eq('user_id', userId)
      .eq('is_forced_validation', true)
      .order('created_at', { ascending: false })
      .limit(1);

    if (error || !data || data.length === 0) {
      return null;
    }

    const trace = data[0]?.validation_trace;
    if (typeof trace === 'object' && trace !== null && 'steps' in trace && 'startTime' in trace) {
      return trace as ValidationTrace;
    }
    
    return null;
  } catch {
    return null;
  }
}
