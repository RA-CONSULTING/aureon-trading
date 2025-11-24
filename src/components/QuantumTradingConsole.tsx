import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useBinanceWebSocket } from '@/hooks/useBinanceWebSocket';
import { useBinanceCredentials } from '@/hooks/useBinanceCredentials';
import { 
  TrendingUp, TrendingDown, Activity, Radio, Zap, 
  Waves, DollarSign, BarChart3, Shield, AlertCircle, AlertTriangle, Wifi 
} from 'lucide-react';
import { AutonomousTradingPanel } from './AutonomousTradingPanel';
import { RealBinanceBalances } from './RealBinanceBalances';

interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  volume: number;
  volatility: number;
}

interface AurisNode {
  name: string;
  value: number;
  color: string;
  active: boolean;
}

interface Position {
  symbol: string;
  side: 'long' | 'short';
  entry: number;
  current: number;
  size: number;
  pnl: number;
  pnlPercent: number;
}

export default function QuantumTradingConsole() {
  const { hasCredentials } = useBinanceCredentials();
  const { marketData: liveData, connected } = useBinanceWebSocket(['BTCUSDT', 'ETHUSDT', 'SOLUSDT']);
  
  const [marketData, setMarketData] = useState<MarketData[]>([
    { symbol: 'BTC/USDT', price: 43250.50, change24h: 2.34, volume: 28500000000, volatility: 0.042 },
    { symbol: 'ETH/USDT', price: 2285.75, change24h: -1.12, volume: 15200000000, volatility: 0.038 },
    { symbol: 'SOL/USDT', price: 98.42, change24h: 5.67, volume: 3400000000, volatility: 0.065 },
  ]);

  const [lambda, setLambda] = useState(0.756);
  const [coherence, setCoherence] = useState(0.892);
  const [prismLevel, setPrismLevel] = useState(4);
  const [lighthouseVotes, setLighthouseVotes] = useState(7);
  const [phase, setPhase] = useState<'FEAR' | 'LOVE' | 'AWE' | 'UNITY'>('LOVE');

  const [aurisNodes, setAurisNodes] = useState<AurisNode[]>([
    { name: 'Tiger', value: 0.82, color: 'text-orange-500', active: true },
    { name: 'Falcon', value: 0.91, color: 'text-blue-500', active: true },
    { name: 'Hummingbird', value: 0.67, color: 'text-green-500', active: true },
    { name: 'Dolphin', value: 0.88, color: 'text-cyan-500', active: true },
    { name: 'Deer', value: 0.74, color: 'text-yellow-500', active: true },
    { name: 'Owl', value: 0.79, color: 'text-purple-500', active: true },
    { name: 'Panda', value: 0.85, color: 'text-gray-400', active: true },
    { name: 'CargoShip', value: 0.72, color: 'text-blue-400', active: false },
    { name: 'Clownfish', value: 0.69, color: 'text-pink-500', active: false },
  ]);

  const [positions, setPositions] = useState<Position[]>([
    { 
      symbol: 'BTC/USDT', 
      side: 'long', 
      entry: 42850.00, 
      current: 43250.50, 
      size: 0.05, 
      pnl: 20.03,
      pnlPercent: 0.93
    },
    { 
      symbol: 'ETH/USDT', 
      side: 'long', 
      entry: 2310.50, 
      current: 2285.75, 
      size: 0.8, 
      pnl: -19.80,
      pnlPercent: -1.07
    },
  ]);

  const [totalPnl, setTotalPnl] = useState(0);
  const [accountBalance, setAccountBalance] = useState(10250.50);

  useEffect(() => {
    // Update market data from live WebSocket
    if (connected && liveData) {
      setMarketData(prev => prev.map((m, i) => {
        const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'];
        const live = liveData[symbols[i]];
        if (live) {
          return {
            ...m,
            price: live.price,
            change24h: live.priceChange24h,
            volume: live.volume24h,
            volatility: Math.abs(live.priceChange24h) / 100
          };
        }
        return m;
      }));
    }
  }, [liveData, connected]);

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate real-time updates if not connected
      if (!connected) {
        setMarketData(prev => prev.map(m => ({
          ...m,
          price: m.price * (1 + (Math.random() - 0.5) * 0.001),
          change24h: m.change24h + (Math.random() - 0.5) * 0.1,
        })));
      }

      // Update Λ, Γ, Prism based on market volatility
      const avgVolatility = marketData.reduce((sum, m) => sum + (m.volatility || 0), 0) / marketData.length;
      setLambda(prev => Math.max(0, Math.min(1, prev + avgVolatility * (Math.random() - 0.5) * 0.1)));
      setCoherence(prev => Math.max(0, Math.min(1, prev + (Math.random() - 0.5) * 0.03)));
      
      const votes = Math.floor(Math.random() * 3) + 6;
      setLighthouseVotes(votes);
      
      if (coherence > 0.9) {
        setPhase('UNITY');
        setPrismLevel(5);
      } else if (coherence > 0.75) {
        setPhase('LOVE');
        setPrismLevel(4);
      } else if (coherence > 0.6) {
        setPhase('AWE');
        setPrismLevel(3);
      } else {
        setPhase('FEAR');
        setPrismLevel(Math.floor(Math.random() * 2) + 1);
      }

      setAurisNodes(prev => prev.map(node => ({
        ...node,
        value: Math.max(0, Math.min(1, node.value + (Math.random() - 0.5) * 0.1)),
        active: node.value > 0.7
      })));

      // Update positions P&L
      setPositions(prev => prev.map((pos, i) => {
        const currentPrice = marketData[i]?.price || pos.current;
        const pnl = pos.side === 'long' 
          ? (currentPrice - pos.entry) * pos.size 
          : (pos.entry - currentPrice) * pos.size;
        const pnlPercent = ((currentPrice - pos.entry) / pos.entry) * 100 * (pos.side === 'long' ? 1 : -1);
        
        return { ...pos, current: currentPrice, pnl, pnlPercent };
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, [coherence, marketData]);

  useEffect(() => {
    const total = positions.reduce((sum, pos) => sum + pos.pnl, 0);
    setTotalPnl(total);
  }, [positions]);

  const phaseColors = {
    FEAR: 'bg-red-500/20 text-red-400 border-red-500/30',
    LOVE: 'bg-secondary/20 text-secondary border-secondary/30',
    AWE: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    UNITY: 'bg-primary/20 text-primary border-primary/30',
  };

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Connection Status */}
      {!hasCredentials && (
        <Alert className="bg-yellow-500/10 border-yellow-500/20 animate-fade-in">
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
          <AlertDescription className="text-yellow-500">
            <strong>No API credentials configured.</strong> Go to the "API Keys" tab to connect your Binance account for live trading.
          </AlertDescription>
        </Alert>
      )}

      {hasCredentials && !connected && (
        <Alert className="bg-blue-500/10 border-blue-500/20 animate-fade-in">
          <Wifi className="h-4 w-4 text-blue-500 animate-pulse" />
          <AlertDescription className="text-blue-500">
            Connecting to Binance WebSocket streams...
          </AlertDescription>
        </Alert>
      )}

      {connected && (
        <Alert className="bg-green-500/10 border-green-500/20 animate-fade-in">
          <Wifi className="h-4 w-4 text-green-500" />
          <AlertDescription className="text-green-500">
            🌈 <strong>LIVE</strong> • Connected to Binance • {Object.keys(liveData).length} pairs streaming in real-time
          </AlertDescription>
        </Alert>
      )}
      
      {/* Header with Account Summary */}
      <div className="flex items-center justify-between animate-fade-in">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="h-3 w-3 rounded-full bg-primary animate-quantum-pulse" />
            <h1 className="text-3xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              AUREON Trading Console
            </h1>
          </div>
          <p className="text-muted-foreground">Real-time quantum consciousness trading system</p>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Account Balance</div>
            <div className="text-2xl font-bold">${accountBalance.toFixed(2)}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Total P&L</div>
            <div className={`text-2xl font-bold ${totalPnl >= 0 ? 'text-success' : 'text-destructive'}`}>
              ${totalPnl.toFixed(2)} ({((totalPnl / accountBalance) * 100).toFixed(2)}%)
            </div>
          </div>
        </div>
      </div>

      {/* Real Binance Wallet Balances */}
      <RealBinanceBalances />

      {/* Autonomous Trading Panel */}
      <AutonomousTradingPanel />

      {/* Master Controls */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Lambda */}
        <Card className="p-4 border-primary/30 bg-gradient-card glow-primary animate-slide-in">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" />
              <span className="font-semibold">Master Λ(t)</span>
            </div>
            <Badge variant="outline" className="border-primary/50 text-primary text-xs">
              ACTIVE
            </Badge>
          </div>
          <div className="text-3xl font-bold text-primary mb-2">{lambda.toFixed(4)}</div>
          <div className="text-xs text-muted-foreground">S + O + E</div>
        </Card>

        {/* Coherence */}
        <Card className="p-4 border-accent/30 bg-gradient-card glow-accent animate-slide-in" style={{ animationDelay: '100ms' }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Waves className="h-4 w-4 text-accent" />
              <span className="font-semibold">Coherence Γ</span>
            </div>
            <Badge variant="outline" className="border-accent/50 text-accent text-xs">
              {coherence > 0.9 ? 'OPTIMAL' : 'STABLE'}
            </Badge>
          </div>
          <div className="text-3xl font-bold text-accent mb-2">{coherence.toFixed(4)}</div>
          <div className="text-xs text-muted-foreground">Lighthouse: {lighthouseVotes}/9 votes</div>
        </Card>

        {/* Prism */}
        <Card className="p-4 border-secondary/30 bg-gradient-card glow-secondary animate-slide-in" style={{ animationDelay: '200ms' }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Radio className="h-4 w-4 text-secondary" />
              <span className="font-semibold">Prism Level</span>
            </div>
            <Badge variant="outline" className="border-secondary/50 text-secondary text-xs">
              528 Hz
            </Badge>
          </div>
          <div className="text-3xl font-bold text-secondary mb-2">Level {prismLevel}</div>
          <div className="flex gap-1 mt-2">
            {[1,2,3,4,5].map(l => (
              <div key={l} className={`h-1.5 flex-1 rounded-full transition-all ${l <= prismLevel ? 'bg-secondary' : 'bg-muted'}`} />
            ))}
          </div>
        </Card>

        {/* Phase */}
        <Card className={`p-4 border ${phaseColors[phase]} bg-gradient-card animate-slide-in`} style={{ animationDelay: '300ms' }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              <span className="font-semibold">Bridge Phase</span>
            </div>
          </div>
          <div className="text-3xl font-bold mb-2">{phase}</div>
          <div className="text-xs opacity-80">Emotional Frequency</div>
        </Card>
      </div>

      {/* Main Trading Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Market Data */}
        <Card className="p-6 border-border/50 bg-gradient-card lg:col-span-2 animate-fade-in" style={{ animationDelay: '400ms' }}>
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            Live Markets
          </h3>
          <div className="space-y-3">
            {marketData.map((market, i) => (
              <div key={i} className="p-4 rounded-lg bg-muted/30 border border-border/30 hover:border-primary/50 transition-all">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="text-lg font-bold">{market.symbol}</div>
                    <Badge variant={market.change24h >= 0 ? 'default' : 'destructive'} className="text-xs">
                      {market.change24h >= 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                      {Math.abs(market.change24h).toFixed(2)}%
                    </Badge>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">${market.price.toFixed(2)}</div>
                    <div className="text-xs text-muted-foreground">
                      Vol: ${(market.volume / 1e9).toFixed(2)}B
                    </div>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Volatility: {(market.volatility * 100).toFixed(2)}%</span>
                  <Button size="sm" className="h-7 text-xs">
                    <DollarSign className="h-3 w-3 mr-1" />
                    Trade
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* 9 Auris Nodes */}
        <Card className="p-6 border-border/50 bg-gradient-card animate-fade-in" style={{ animationDelay: '500ms' }}>
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            9 Auris Nodes
          </h3>
          <div className="space-y-2">
            {aurisNodes.map((node, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/20">
                <div className="flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${node.active ? 'bg-primary animate-quantum-pulse' : 'bg-muted'}`} />
                  <span className={`text-sm font-medium ${node.color}`}>{node.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${node.value * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-muted-foreground w-10 text-right">
                    {node.value.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Positions */}
      <Card className="p-6 border-border/50 bg-gradient-card animate-fade-in" style={{ animationDelay: '600ms' }}>
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          Active Positions
        </h3>
        {positions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <AlertCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
            No active positions
          </div>
        ) : (
          <div className="space-y-3">
            {positions.map((pos, i) => (
              <div key={i} className="p-4 rounded-lg bg-muted/30 border border-border/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Badge variant={pos.side === 'long' ? 'default' : 'destructive'}>
                      {pos.side.toUpperCase()}
                    </Badge>
                    <div>
                      <div className="font-bold">{pos.symbol}</div>
                      <div className="text-xs text-muted-foreground">
                        Size: {pos.size} | Entry: ${pos.entry.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold">${pos.current.toFixed(2)}</div>
                    <div className={`text-sm font-semibold ${pos.pnl >= 0 ? 'text-success' : 'text-destructive'}`}>
                      ${pos.pnl.toFixed(2)} ({pos.pnlPercent >= 0 ? '+' : ''}{pos.pnlPercent.toFixed(2)}%)
                    </div>
                  </div>
                  <Button size="sm" variant="destructive" className="h-8">
                    Close
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
