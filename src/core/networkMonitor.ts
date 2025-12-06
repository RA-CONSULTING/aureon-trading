/**
 * Network Monitor Hook
 * Automatically intercepts fetch/XHR to monitor all API calls
 * Including Supabase edge functions
 */

import { dataStreamMonitor } from './dataStreamMonitor';

let isInitialized = false;

export function initNetworkMonitoring() {
  if (isInitialized || typeof window === 'undefined') return;
  isInitialized = true;

  const originalFetch = window.fetch;

  window.fetch = async function(...args) {
    const [input, init] = args;
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : (input as Request).url;
    
    // Only monitor Supabase functions and Binance API
    const isSupabaseFunction = url.includes('/functions/v1/');
    const isBinanceApi = url.includes('api.binance.com') || url.includes('stream.binance');
    
    if (!isSupabaseFunction && !isBinanceApi) {
      return originalFetch.apply(window, args);
    }

    const startTime = Date.now();
    const requestId = dataStreamMonitor.recordRequest(url, init?.body);

    try {
      const response = await originalFetch.apply(window, args);
      const latency = Date.now() - startTime;
      
      // Clone response to read body without consuming it
      const clonedResponse = response.clone();
      
      try {
        const responseData = await clonedResponse.json();
        dataStreamMonitor.recordResponse(
          requestId, 
          response.ok, 
          responseData,
          response.ok ? undefined : responseData?.error || `HTTP ${response.status}`
        );
      } catch {
        // Response wasn't JSON
        dataStreamMonitor.recordResponse(
          requestId, 
          response.ok, 
          null,
          response.ok ? undefined : `HTTP ${response.status}`
        );
      }

      return response;
    } catch (error: any) {
      dataStreamMonitor.recordResponse(requestId, false, null, error.message || 'Network error');
      throw error;
    }
  };

  console.log('[NetworkMonitor] Initialized - tracking Supabase & Binance API calls');
}
