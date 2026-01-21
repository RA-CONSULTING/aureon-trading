/**
 * Instrumented Supabase Functions
 * Wraps supabase.functions.invoke with data stream monitoring
 */

import { supabase } from '@/integrations/supabase/client';
import { dataStreamMonitor } from './dataStreamMonitor';

export async function invokeWithMonitoring<T = any>(
  functionName: string,
  options?: { body?: any; headers?: Record<string, string> }
): Promise<{ data: T | null; error: any }> {
  const startTime = Date.now();
  const requestId = dataStreamMonitor.recordRequest(functionName, options?.body);
  
  try {
    const result = await supabase.functions.invoke(functionName, options);
    const latency = Date.now() - startTime;
    
    if (result.error) {
      dataStreamMonitor.recordResponse(requestId, false, result.error, result.error.message || 'Unknown error');
    } else {
      dataStreamMonitor.recordResponse(requestId, true, result.data);
    }
    
    return result as { data: T | null; error: any };
  } catch (error: any) {
    const latency = Date.now() - startTime;
    dataStreamMonitor.recordResponse(requestId, false, null, error.message || 'Exception');
    throw error;
  }
}

// Helper to record external API calls (Binance, etc.)
export function recordExternalStream(
  endpoint: string,
  success: boolean,
  latencyMs: number,
  requestData?: any,
  responseData?: any,
  errorMessage?: string
) {
  dataStreamMonitor.recordStream(endpoint, success, latencyMs, requestData, responseData, errorMessage);
}
