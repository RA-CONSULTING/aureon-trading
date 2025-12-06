/**
 * Kraken Status Panel
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Displays real-time Kraken WebSocket connection status and ticker data
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Wifi, WifiOff, RefreshCw, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { useKrakenRealtime } from '@/hooks/useKrakenRealtime';
import { supabase } from '@/integrations/supabase/client';

interface KrakenAPIData {
  success: boolean;
  tickers?: Record<string, any>;
  primaryTicker?: any;
  latencyMs?: number;
  dataSource?: string;
  error?: string;
}

export const KrakenStatusPanel: React.FC = () => {
  const { 
    isConnected, 
    tickers, 
    lastUpdate, 
    error, 
    connect, 
    disconnect,
    btcPrice,
    ethPrice,
    tickerCount,
    connectionAttempts,
  } = useKrakenRealtime({ autoConnect: true });

  const [apiData, setApiData] = useState<KrakenAPIData | null>(null);
  const [isLoadingAPI, setIsLoadingAPI] = useState(false);

  // Fetch from edge function as backup/validation
  const fetchFromAPI = async () => {
    setIsLoadingAPI(true);
    try {
      const { data, error } = await supabase.functions.invoke('fetch-kraken-market-data', {
        body: { symbols: ['BTCUSD', 'ETHUSD', 'SOLUSD'] }
      });
      
      if (error) throw error;
      setApiData(data);
    } catch (err) {
      console.error('Kraken API fetch error:', err);
      setApiData({ success: false, error: err instanceof Error ? err.message : 'API error' });
    } finally {
      setIsLoadingAPI(false);
    }
  };

  useEffect(() => {
    fetchFromAPI();
    // Refresh API data every 30 seconds
    const interval = setInterval(fetchFromAPI, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatPrice = (price: number | null | undefined) => {
    if (!price) return '-';
    return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatTime = (timestamp: number | null) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <Card className="bg-card/50 border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <span className="text-2xl">🦑</span>
            Kraken Integration
          </CardTitle>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
                <Wifi className="h-3 w-3 mr-1" />
                WebSocket LIVE
              </Badge>
            ) : (
              <Badge variant="destructive">
                <WifiOff className="h-3 w-3 mr-1" />
                Disconnected
              </Badge>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={isConnected ? disconnect : connect}
            >
              <RefreshCw className={`h-4 w-4 ${isConnected ? '' : 'animate-spin'}`} />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Connection Status */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">WebSocket Status</p>
            <div className="flex items-center gap-2">
              {isConnected ? (
                <Activity className="h-4 w-4 text-green-500 animate-pulse" />
              ) : (
                <WifiOff className="h-4 w-4 text-destructive" />
              )}
              <span className={isConnected ? 'text-green-400' : 'text-destructive'}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Attempts: {connectionAttempts}
            </p>
          </div>
          
          <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">Tickers Streaming</p>
            <p className="text-xl font-bold">{tickerCount}</p>
            <p className="text-xs text-muted-foreground">
              Updated: {formatTime(lastUpdate)}
            </p>
          </div>
        </div>

        {/* Live Prices from WebSocket */}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-muted-foreground">WebSocket Prices</h4>
          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 rounded bg-muted/20 border border-border/30">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">BTC</span>
                {btcPrice && (
                  <TrendingUp className="h-3 w-3 text-green-500" />
                )}
              </div>
              <p className="text-lg font-bold text-primary">{formatPrice(btcPrice)}</p>
            </div>
            <div className="p-2 rounded bg-muted/20 border border-border/30">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">ETH</span>
                {ethPrice && (
                  <TrendingUp className="h-3 w-3 text-green-500" />
                )}
              </div>
              <p className="text-lg font-bold text-primary">{formatPrice(ethPrice)}</p>
            </div>
          </div>
        </div>

        {/* API Data (Edge Function) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-muted-foreground">REST API Validation</h4>
            <Button variant="ghost" size="sm" onClick={fetchFromAPI} disabled={isLoadingAPI}>
              <RefreshCw className={`h-3 w-3 ${isLoadingAPI ? 'animate-spin' : ''}`} />
            </Button>
          </div>
          
          {apiData?.success ? (
            <div className="p-2 rounded bg-green-500/10 border border-green-500/30">
              <div className="flex items-center justify-between">
                <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
                  {apiData.dataSource}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {apiData.latencyMs}ms
                </span>
              </div>
              {apiData.primaryTicker && (
                <p className="text-sm mt-1">
                  BTC: {formatPrice(apiData.primaryTicker.price)}
                </p>
              )}
            </div>
          ) : (
            <div className="p-2 rounded bg-destructive/10 border border-destructive/30">
              <p className="text-xs text-destructive">{apiData?.error || 'No data'}</p>
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-2 rounded bg-destructive/10 border border-destructive/30">
            <p className="text-xs text-destructive">WebSocket Error: {error}</p>
          </div>
        )}

        {/* All Streaming Tickers */}
        {Object.keys(tickers).length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-muted-foreground">All Streaming Tickers</h4>
            <div className="max-h-40 overflow-y-auto space-y-1">
              {Object.entries(tickers).map(([symbol, ticker]) => (
                <div 
                  key={symbol}
                  className="flex items-center justify-between p-2 rounded bg-muted/20 text-sm"
                >
                  <span className="font-mono">{symbol}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-bold">{formatPrice(ticker.price)}</span>
                    <span className={`text-xs ${ticker.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {ticker.change24h >= 0 ? '+' : ''}{ticker.change24h.toFixed(2)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
