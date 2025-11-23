import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { BacktestEngine, type BacktestConfig, type BacktestResults } from '@/core/backtestEngine';
import { PlayCircle, Loader2 } from 'lucide-react';

interface BacktestRunnerProps {
  onResultsReady: (results: BacktestResults) => void;
}

export const BacktestRunner = ({ onResultsReady }: BacktestRunnerProps) => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();

  const [config, setConfig] = useState<BacktestConfig>({
    symbol: 'BTCUSDT',
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    endDate: new Date(),
    initialCapital: 10000,
    positionSize: 0.95,
    stopLossPercent: 2,
    takeProfitPercent: 5,
    tradingFee: 0.001,
    slippage: 0.0001,
    minCoherence: 0.945,
    minLighthouseConfidence: 0.7,
    minPrismLevel: 3,
    requireLHE: true,
  });

  const runBacktest = async () => {
    setIsRunning(true);
    setProgress(0);

    try {
      toast({
        title: '🎯 Starting Backtest',
        description: `Testing ${config.symbol} from ${config.startDate.toLocaleDateString()} to ${config.endDate.toLocaleDateString()}`,
      });

      // Fetch historical data
      setProgress(10);
      
      toast({
        title: '📡 Fetching Data',
        description: 'Downloading historical market data from Binance...',
      });
      
      const { data: histData, error: histError } = await supabase.functions.invoke('fetch-historical-data', {
        body: {
          symbol: config.symbol,
          interval: '15m',
          startTime: config.startDate.getTime(),
          endTime: config.endDate.getTime(),
          limit: 1000,
        },
      });

      if (histError) {
        console.error('Historical data error:', histError);
        throw new Error(`Failed to fetch historical data: ${histError.message}`);
      }
      
      if (!histData?.candles || histData.candles.length === 0) {
        throw new Error('No historical data available for selected period. Try a different date range.');
      }

      console.log(`📊 Fetched ${histData.candles.length} candles`);
      setProgress(30);

      toast({
        title: '⚙️ Running Backtest',
        description: `Processing ${histData.candles.length} candles through AUREON system...`,
      });

      // Run backtest
      const engine = new BacktestEngine();
      const results = await engine.runBacktest(histData.candles, config);
      setProgress(70);
      
      toast({
        title: '💾 Saving Results',
        description: 'Storing backtest results in database...',
      });

      // Save results to database
      const { error: saveError } = await supabase
        .from('backtest_results')
        .insert({
          symbol: config.symbol,
          start_date: config.startDate.toISOString(),
          end_date: config.endDate.toISOString(),
          initial_capital: config.initialCapital,
          final_capital: results.metrics.finalCapital,
          total_return: results.metrics.totalReturnPercent,
          total_trades: results.metrics.totalTrades,
          winning_trades: results.metrics.winningTrades,
          losing_trades: results.metrics.losingTrades,
          win_rate: results.metrics.winRate,
          profit_factor: results.metrics.profitFactor,
          max_drawdown: results.metrics.maxDrawdownPercent,
          sharpe_ratio: results.metrics.sharpeRatio,
          avg_trade_duration: results.metrics.avgTradeDuration,
          config: config as any,
          trades: results.trades as any,
          equity_curve: results.equityCurve as any,
        });

      if (saveError) throw saveError;

      setProgress(100);

      toast({
        title: '✅ Backtest Complete',
        description: `${results.metrics.totalTrades} trades | ${results.metrics.totalReturnPercent.toFixed(2)}% return`,
        duration: 5000,
      });

      onResultsReady(results);
    } catch (error) {
      console.error('Backtest error:', error);
      toast({
        title: 'Backtest Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsRunning(false);
      setProgress(0);
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">🔬 Backtest Configuration</h2>
          <p className="text-sm text-muted-foreground">Test AUREON strategy on historical data</p>
        </div>
        <Button onClick={runBacktest} disabled={isRunning} size="lg">
          {isRunning ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Running... {progress}%
            </>
          ) : (
            <>
              <PlayCircle className="mr-2 h-5 w-5" />
              Run Backtest
            </>
          )}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Market Settings */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">Market Settings</h3>
          
          <div>
            <Label>Trading Pair</Label>
            <Select value={config.symbol} onValueChange={(value) => setConfig({ ...config, symbol: value })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BTCUSDT">BTC/USDT</SelectItem>
                <SelectItem value="ETHUSDT">ETH/USDT</SelectItem>
                <SelectItem value="BNBUSDT">BNB/USDT</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Start Date</Label>
            <Input
              type="date"
              value={config.startDate.toISOString().split('T')[0]}
              onChange={(e) => setConfig({ ...config, startDate: new Date(e.target.value) })}
            />
          </div>

          <div>
            <Label>End Date</Label>
            <Input
              type="date"
              value={config.endDate.toISOString().split('T')[0]}
              onChange={(e) => setConfig({ ...config, endDate: new Date(e.target.value) })}
            />
          </div>

          <div>
            <Label>Initial Capital ($)</Label>
            <Input
              type="number"
              value={config.initialCapital}
              onChange={(e) => setConfig({ ...config, initialCapital: Number(e.target.value) })}
            />
          </div>
        </div>

        {/* Risk Management */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">Risk Management</h3>
          
          <div>
            <Label>Position Size: {(config.positionSize * 100).toFixed(0)}%</Label>
            <Slider
              value={[config.positionSize * 100]}
              onValueChange={([value]) => setConfig({ ...config, positionSize: value / 100 })}
              min={10}
              max={100}
              step={5}
            />
          </div>

          <div>
            <Label>Stop Loss: {config.stopLossPercent}%</Label>
            <Slider
              value={[config.stopLossPercent]}
              onValueChange={([value]) => setConfig({ ...config, stopLossPercent: value })}
              min={0.5}
              max={10}
              step={0.5}
            />
          </div>

          <div>
            <Label>Take Profit: {config.takeProfitPercent}%</Label>
            <Slider
              value={[config.takeProfitPercent]}
              onValueChange={([value]) => setConfig({ ...config, takeProfitPercent: value })}
              min={1}
              max={20}
              step={0.5}
            />
          </div>

          <div>
            <Label>Trading Fee: {(config.tradingFee * 100).toFixed(2)}%</Label>
            <Slider
              value={[config.tradingFee * 100]}
              onValueChange={([value]) => setConfig({ ...config, tradingFee: value / 100 })}
              min={0.01}
              max={0.5}
              step={0.01}
            />
          </div>

          <div>
            <Label>Slippage: {(config.slippage * 100).toFixed(3)}%</Label>
            <Slider
              value={[config.slippage * 1000]}
              onValueChange={([value]) => setConfig({ ...config, slippage: value / 1000 })}
              min={0.01}
              max={0.5}
              step={0.01}
            />
          </div>
        </div>

        {/* AUREON Filters */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">AUREON Filters</h3>
          
          <div>
            <Label>Min Coherence (Γ): {config.minCoherence.toFixed(3)}</Label>
            <Slider
              value={[config.minCoherence * 1000]}
              onValueChange={([value]) => setConfig({ ...config, minCoherence: value / 1000 })}
              min={800}
              max={990}
              step={5}
            />
          </div>

          <div>
            <Label>Min Lighthouse Confidence: {config.minLighthouseConfidence.toFixed(2)}</Label>
            <Slider
              value={[config.minLighthouseConfidence * 100]}
              onValueChange={([value]) => setConfig({ ...config, minLighthouseConfidence: value / 100 })}
              min={50}
              max={95}
              step={5}
            />
          </div>

          <div>
            <Label>Min Prism Level: {config.minPrismLevel}</Label>
            <Slider
              value={[config.minPrismLevel]}
              onValueChange={([value]) => setConfig({ ...config, minPrismLevel: value })}
              min={1}
              max={5}
              step={1}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label>Require LHE (Lighthouse Event)</Label>
            <Switch
              checked={config.requireLHE}
              onCheckedChange={(checked) => setConfig({ ...config, requireLHE: checked })}
            />
          </div>
        </div>
      </div>

      {isRunning && (
        <div className="mt-6">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </Card>
  );
};
