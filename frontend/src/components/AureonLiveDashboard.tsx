/**
 * 🌉 AUREON LIVE BRIDGE DASHBOARD 🌉
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Displays LIVE data from ALL trading platforms and ALL systems
 * via the aureon_frontend_bridge.py WebSocket server.
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { 
  Zap, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown,
  AlertTriangle, 
  CheckCircle2, 
  Activity,
  Wifi,
  WifiOff,
  Brain,
  Target,
  Sparkles
} from 'lucide-react';
import { useAureonLiveData } from '@/hooks/useAureonLiveData';

// ════════════════════════════════════════════════════════════════════════════
// EXCHANGE ICONS
// ════════════════════════════════════════════════════════════════════════════

const EXCHANGE_ICONS: Record<string, string> = {
  kraken: '🦑',
  binance: '🔶',
  alpaca: '🦙',
  capital: '📈',
};

const EXCHANGE_COLORS: Record<string, string> = {
  kraken: 'text-purple-400',
  binance: 'text-yellow-400',
  alpaca: 'text-green-400',
  capital: 'text-blue-400',
};

// ════════════════════════════════════════════════════════════════════════════
// SYSTEM ICONS
// ════════════════════════════════════════════════════════════════════════════

const SYSTEM_ICONS: Record<string, string> = {
  V14: '🏆',
  Mycelium: '🍄',
  Commando: '🦅',
  Nexus: '🔮',
  Multiverse: '🌌',
  MinerBrain: '🧠',
  Harmonic: '🌊',
  Omega: '🔱',
};

// ════════════════════════════════════════════════════════════════════════════
// COMPONENT
// ════════════════════════════════════════════════════════════════════════════

export function AureonLiveDashboard() {
  const {
    connected,
    connecting,
    error,
    exchanges,
    totalPortfolioValue,
    allBalances,
    signals,
    signalCount,
    opportunities,
    systemsOnline,
    systemsOffline,
    topMovers,
    refresh,
    reconnect,
    lastUpdate,
    updatesReceived,
  } = useAureonLiveData();

  const formatTime = (ts: number) => {
    if (!ts) return 'Never';
    const date = new Date(ts * 1000);
    return date.toLocaleTimeString();
  };

  return (
    <div className="space-y-4 p-4">
      {/* Connection Header */}
      <Card className={`border-2 ${connected ? 'border-green-500/50' : 'border-red-500/50'}`}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              {connected ? (
                <Wifi className="h-6 w-6 text-green-500 animate-pulse" />
              ) : (
                <WifiOff className="h-6 w-6 text-red-500" />
              )}
              Aureon Live Bridge
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant={connected ? 'default' : 'destructive'}>
                {connecting ? 'CONNECTING...' : connected ? 'LIVE' : 'OFFLINE'}
              </Badge>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={connected ? refresh : reconnect}
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${connecting ? 'animate-spin' : ''}`} />
                {connected ? 'Refresh' : 'Reconnect'}
              </Button>
            </div>
          </div>
          <CardDescription>
            Updates: {updatesReceived} | Last: {formatTime(lastUpdate)}
            {error && <span className="text-red-400 ml-2">| Error: {error}</span>}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">
              ${totalPortfolioValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </div>
            <div className="text-sm text-muted-foreground">Total Portfolio Value</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-400">
              {signalCount}
            </div>
            <div className="text-sm text-muted-foreground">Active Signals</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-yellow-400">
              {opportunities.length}
            </div>
            <div className="text-sm text-muted-foreground">Opportunities</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Exchanges Panel */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              Exchange Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(exchanges).map(([name, data]) => (
                <div
                  key={name}
                  className={`p-3 rounded-lg border ${
                    data.connected 
                      ? 'bg-green-500/10 border-green-500/30' 
                      : 'bg-red-500/10 border-red-500/30'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-lg font-semibold ${EXCHANGE_COLORS[name] || 'text-gray-400'}`}>
                      {EXCHANGE_ICONS[name] || '📊'} {name.toUpperCase()}
                    </span>
                    <Badge variant={data.connected ? 'default' : 'destructive'} className="text-xs">
                      {data.connected ? 'LIVE' : 'OFF'}
                    </Badge>
                  </div>
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Value:</span>
                      <span className="font-mono font-semibold">
                        ${data.total_value?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || '0'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Tickers:</span>
                      <span className="font-mono">{data.ticker_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Assets:</span>
                      <span className="font-mono">{Object.keys(data.balances || {}).length}</span>
                    </div>
                  </div>
                  {data.error && (
                    <div className="mt-2 text-xs text-red-400 truncate">{data.error}</div>
                  )}
                </div>
              ))}
            </div>

            {Object.keys(exchanges).length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No exchange data yet...</p>
                <p className="text-xs">Start aureon_frontend_bridge.py</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Systems Panel */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              Trading Systems
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {/* Online Systems */}
              <div className="flex flex-wrap gap-2">
                {systemsOnline.map(system => (
                  <Badge key={system} variant="default" className="text-xs py-1 px-2">
                    {SYSTEM_ICONS[system] || '⚡'} {system}
                    <CheckCircle2 className="h-3 w-3 ml-1 text-green-400" />
                  </Badge>
                ))}
              </div>
              
              {/* Offline Systems */}
              {systemsOffline.length > 0 && (
                <>
                  <Separator className="my-2" />
                  <div className="flex flex-wrap gap-2">
                    {systemsOffline.map(system => (
                      <Badge key={system} variant="outline" className="text-xs py-1 px-2 opacity-50">
                        {SYSTEM_ICONS[system] || '⚡'} {system}
                        <AlertTriangle className="h-3 w-3 ml-1 text-yellow-500" />
                      </Badge>
                    ))}
                  </div>
                </>
              )}
              
              {systemsOnline.length === 0 && systemsOffline.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Brain className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No system data yet...</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Signals Panel */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              Live Signals ({signalCount})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {signals.slice(0, 15).map((signal, idx) => (
                <div
                  key={`${signal.system}-${signal.symbol}-${idx}`}
                  className={`p-2 rounded-lg border ${
                    signal.signal_type === 'BUY' || signal.signal_type === 'CONVERT'
                      ? 'bg-green-500/10 border-green-500/30'
                      : signal.signal_type === 'SELL'
                      ? 'bg-red-500/10 border-red-500/30'
                      : 'bg-yellow-500/10 border-yellow-500/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {SYSTEM_ICONS[signal.system] || '⚡'} {signal.system}
                      </Badge>
                      <span className="font-mono font-semibold">{signal.symbol}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant={
                          signal.signal_type === 'BUY' || signal.signal_type === 'CONVERT' 
                            ? 'default' 
                            : signal.signal_type === 'SELL' 
                            ? 'destructive' 
                            : 'secondary'
                        }
                      >
                        {signal.signal_type}
                      </Badge>
                      <span className="text-xs font-mono">
                        {(signal.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {signal.reason}
                  </div>
                </div>
              ))}
              
              {signals.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No signals yet...</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Opportunities Panel */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-yellow-400" />
              High Score Opportunities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {opportunities.map((opp, idx) => (
                <div
                  key={`opp-${opp.symbol}-${idx}`}
                  className="p-3 rounded-lg border bg-yellow-500/10 border-yellow-500/30"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono font-semibold text-yellow-400">
                      {opp.symbol}
                    </span>
                    <Badge variant="default" className="bg-yellow-600">
                      Score: {opp.score}/10
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      {SYSTEM_ICONS[opp.system]} {opp.system}
                    </span>
                    <span className="text-green-400">
                      {(opp.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                </div>
              ))}
              
              {opportunities.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No high-score opportunities yet...</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Movers */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Top Movers
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-2">
            {topMovers.slice(0, 10).map((mover, idx) => (
              <div
                key={`${mover.symbol}-${idx}`}
                className={`p-2 rounded-lg border text-center ${
                  mover.change > 0 
                    ? 'bg-green-500/10 border-green-500/30' 
                    : 'bg-red-500/10 border-red-500/30'
                }`}
              >
                <div className="font-mono text-xs truncate" title={mover.symbol}>
                  {mover.symbol.substring(0, 8)}
                </div>
                <div className={`text-sm font-semibold ${mover.change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {mover.change > 0 ? (
                    <TrendingUp className="h-3 w-3 inline mr-1" />
                  ) : (
                    <TrendingDown className="h-3 w-3 inline mr-1" />
                  )}
                  {mover.change > 0 ? '+' : ''}{mover.change.toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
          
          {topMovers.length === 0 && (
            <div className="text-center py-4 text-muted-foreground">
              No market data yet...
            </div>
          )}
        </CardContent>
      </Card>

      {/* Combined Balances */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Combined Balances (All Exchanges)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-6 gap-2 max-h-[200px] overflow-y-auto">
            {Object.entries(allBalances)
              .sort((a, b) => {
                const totalA = Object.values(a[1]).reduce((s, v) => s + v, 0);
                const totalB = Object.values(b[1]).reduce((s, v) => s + v, 0);
                return totalB - totalA;
              })
              .slice(0, 24)
              .map(([asset, exchanges]) => {
                const total = Object.values(exchanges).reduce((sum, val) => sum + val, 0);
                return (
                  <div 
                    key={asset}
                    className="p-2 rounded-lg border bg-background/50 text-center"
                    title={Object.entries(exchanges).map(([e, v]) => `${e}: ${v}`).join(', ')}
                  >
                    <div className="font-mono text-xs font-semibold">{asset}</div>
                    <div className="text-xs text-muted-foreground">
                      {total.toFixed(total < 1 ? 6 : 2)}
                    </div>
                    <div className="text-[10px] text-muted-foreground">
                      {Object.keys(exchanges).length} exchange{Object.keys(exchanges).length > 1 ? 's' : ''}
                    </div>
                  </div>
                );
              })}
          </div>
          
          {Object.keys(allBalances).length === 0 && (
            <div className="text-center py-4 text-muted-foreground">
              No balances yet...
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default AureonLiveDashboard;
