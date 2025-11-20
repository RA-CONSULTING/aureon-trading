import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus, Wifi, WifiOff } from "lucide-react";
import { useLiveTradingSignals } from "@/hooks/useLiveTradingSignals";

export const LiveTradingSignals = ({ symbol = 'btcusdt' }: { symbol?: string }) => {
  const { signals, currentLambda, isConnected, lastMarketData } = useLiveTradingSignals(symbol);

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'LONG':
        return <TrendingUp className="h-4 w-4 text-success" />;
      case 'SHORT':
        return <TrendingDown className="h-4 w-4 text-destructive" />;
      default:
        return <Minus className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'LONG':
        return 'bg-success text-success-foreground';
      case 'SHORT':
        return 'bg-destructive text-destructive-foreground';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <Card className="bg-card shadow-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Live Trading Signals</CardTitle>
          <Badge variant={isConnected ? "default" : "secondary"} className="gap-1">
            {isConnected ? (
              <>
                <Wifi className="w-3 h-3" />
                Live
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                Connecting...
              </>
            )}
          </Badge>
        </div>
        {currentLambda && lastMarketData && (
          <div className="mt-2 text-sm text-muted-foreground">
            <div className="flex gap-4">
              <span>Λ(t): {currentLambda.lambda.toFixed(4)}</span>
              <span>Γ: {currentLambda.coherence.toFixed(4)}</span>
              <span>Price: ${lastMarketData.price.toFixed(2)}</span>
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {signals.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>Waiting for trading signals...</p>
              <p className="text-xs mt-2">Signals appear when coherence threshold is met</p>
            </div>
          ) : (
            signals.map((signal, idx) => (
              <div
                key={`${signal.timestamp}-${idx}`}
                className="flex items-center justify-between p-3 rounded-lg bg-muted/20 hover:bg-muted/40 transition-colors border border-border"
              >
                <div className="flex items-center gap-3">
                  {getSignalIcon(signal.signal)}
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge className={getSignalColor(signal.signal)}>
                        {signal.signal}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {new Date(signal.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm">{signal.reason}</p>
                    <div className="flex gap-3 text-xs text-muted-foreground mt-1">
                      <span>Strength: {(signal.strength * 100).toFixed(1)}%</span>
                      <span>Prism: L{signal.prismLevel}</span>
                      <span>Node: {signal.lambda.dominantNode}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-mono">${signal.marketData.price.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">
                    Vol: {(signal.marketData.volume * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};