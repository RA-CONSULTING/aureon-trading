/**
 * Network Monitor Hook
 * Automatically intercepts fetch/XHR to monitor all API calls
 * Including Supabase edge functions and all exchange APIs
 */

import { dataStreamMonitor } from './dataStreamMonitor';

let isInitialized = false;

// Extract API key identifier from URL or headers for grouping
function extractApiKeyGroup(url: string, headers?: HeadersInit): string {
  // Check for exchange-specific patterns
  if (url.includes('api.binance.com') || url.includes('stream.binance')) return 'binance';
  if (url.includes('api.kraken.com')) return 'kraken';
  if (url.includes('api.alpaca.markets') || url.includes('paper-api.alpaca')) return 'alpaca';
  if (url.includes('api-capital.backend-capital.com')) return 'capital';
  
  // Supabase functions
  if (url.includes('/functions/v1/')) {
    const match = url.match(/\/functions\/v1\/([^?/]+)/);
    return match ? `supabase:${match[1]}` : 'supabase:unknown';
  }
  
  return 'other';
}

export function initNetworkMonitoring() {
  if (isInitialized || typeof window === 'undefined') return;
  isInitialized = true;

  const originalFetch = window.fetch;

  window.fetch = async function(...args) {
    const [input, init] = args;
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : (input as Request).url;
    
    // Monitor Supabase functions and all exchange APIs
    const isSupabaseFunction = url.includes('/functions/v1/');
    const isBinanceApi = url.includes('api.binance.com') || url.includes('stream.binance');
    const isKrakenApi = url.includes('api.kraken.com');
    const isAlpacaApi = url.includes('api.alpaca.markets') || url.includes('paper-api.alpaca');
    const isCapitalApi = url.includes('api-capital.backend-capital.com');
    
    const shouldMonitor = isSupabaseFunction || isBinanceApi || isKrakenApi || isAlpacaApi || isCapitalApi;
    
    if (!shouldMonitor) {
      return originalFetch.apply(window, args);
    }

    const startTime = Date.now();
    const apiGroup = extractApiKeyGroup(url, init?.headers);
    const endpoint = `[${apiGroup}] ${url.split('?')[0].split('/').slice(-2).join('/')}`;
    const requestId = dataStreamMonitor.recordRequest(endpoint, init?.body);

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

  console.log('[NetworkMonitor] Initialized - tracking Supabase, Binance, Kraken, Alpaca, Capital.com API calls');
}
