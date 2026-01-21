import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Wifi, WifiOff } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface MarketTicker {
  symbol: string;
  price: string;
  change: string;
  changePercent: number;
  volume: string;
  lastUpdate: number;
}

const BINANCE_SYMBOLS = [
  // TOP TIER
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'AVAXUSDT',
  'DOTUSDT', 'ATOMUSDT', 'NEARUSDT', 'APTUSDT', 'SUIUSDT',
  // LAYER 2s
  'ARBUSDT', 'OPUSDT', 'MATICUSDT',
  // DEFI
  'UNIUSDT', 'AAVEUSDT', 'LINKUSDT',
  // AI
  'FETUSDT', 'INJUSDT', 'WLDUSDT',
  // MEMECOINS
  'DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT', 'BONKUSDT', 'WIFUSDT',
];

const MarketOverview = () => {
  const [tickers, setTickers] = useState<Map<string, MarketTicker>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Create WebSocket connection to Binance mini ticker stream
    const streams = BINANCE_SYMBOLS.map(s => `${s.toLowerCase()}@miniTicker`).join('/');
    const wsUrl = `wss://stream.binance.com:9443/stream?streams=${streams}`;
    
    console.log('[MarketOverview] Connecting to Binance WebSocket...');
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('✅ [MarketOverview] Connected to Binance WebSocket');
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.data && message.data.e === '24hrMiniTicker') {
          const data = message.data;
          
          setTickers(prev => {
            const updated = new Map(prev);
            updated.set(data.s, {
              symbol: data.s,
              price: parseFloat(data.c).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 6
              }),
              change: parseFloat(data.p).toFixed(2),
              changePercent: parseFloat(data.P),
              volume: (parseFloat(data.v) / 1000000).toFixed(2) + 'M',
              lastUpdate: Date.now()
            });
            return updated;
          });
        }
      } catch (error) {
        console.error('[MarketOverview] Parse error:', error);
      }
    };

    socket.onerror = (error) => {
      console.error('❌ [MarketOverview] WebSocket error:', error);
      setIsConnected(false);
    };

    socket.onclose = () => {
      console.log('🔌 [MarketOverview] WebSocket disconnected');
      setIsConnected(false);
    };

    setWs(socket);

    return () => {
      console.log('[MarketOverview] Cleaning up WebSocket');
      socket.close();
    };
  }, []);

  const formatSymbol = (symbol: string) => {
    return symbol.replace('USDT', '/USDT');
  };

  return (
    <section className="py-24 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <h2 className="text-4xl font-bold">Live Market Data</h2>
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
          <p className="text-muted-foreground text-lg">Real-time prices from Binance WebSocket</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {BINANCE_SYMBOLS.map((symbol) => {
            const ticker = tickers.get(symbol);
            const isPositive = ticker ? ticker.changePercent >= 0 : false;
            
            return (
              <Card 
                key={symbol} 
                className="bg-card shadow-card hover:shadow-glow transition-all duration-300 cursor-pointer"
              >
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center justify-between">
                    <span>{ticker ? formatSymbol(ticker.symbol) : symbol}</span>
                    {isPositive ? (
                      <TrendingUp className="h-5 w-5 text-success" />
                    ) : (
                      <TrendingDown className="h-5 w-5 text-destructive" />
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {ticker ? (
                    <>
                      <div className="flex items-end justify-between mb-2">
                        <div>
                          <p className="text-3xl font-bold">${ticker.price}</p>
                        </div>
                        <div className={`text-lg font-semibold ${isPositive ? "text-success" : "text-destructive"}`}>
                          {isPositive ? '+' : ''}{ticker.changePercent.toFixed(2)}%
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>24h Vol: {ticker.volume}</span>
                        <span className={isPositive ? "text-success" : "text-destructive"}>
                          {isPositive ? '+' : ''}{ticker.change}
                        </span>
                      </div>
                    </>
                  ) : (
                    <div className="text-muted-foreground">
                      <p className="text-2xl">Connecting...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default MarketOverview;
