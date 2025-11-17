import { useState } from 'react';
import Navbar from '@/components/Navbar';
import { BacktestRunner } from '@/components/BacktestRunner';
import { BacktestResultsDisplay } from '@/components/BacktestResults';
import { MonteCarloRunner } from '@/components/MonteCarloRunner';
import { MonteCarloResultsDisplay } from '@/components/MonteCarloResults';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { BacktestResults, BacktestConfig } from '@/core/backtestEngine';
import type { MonteCarloResults } from '@/core/monteCarloEngine';

const Backtest = () => {
  const [backtestResults, setBacktestResults] = useState<BacktestResults | null>(null);
  const [monteCarloResults, setMonteCarloResults] = useState<MonteCarloResults | null>(null);
  const [baseConfig, setBaseConfig] = useState<BacktestConfig | null>(null);

  const handleBacktestResults = (results: BacktestResults) => {
    setBacktestResults(results);
    setBaseConfig(results.config);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">🔬 AUREON Backtesting & Simulation</h1>
          <p className="text-muted-foreground">
            Validate trading strategy on historical data and test robustness with Monte Carlo simulations
          </p>
        </div>

        <Tabs defaultValue="backtest" className="space-y-8">
          <TabsList>
            <TabsTrigger value="backtest">Single Backtest</TabsTrigger>
            <TabsTrigger value="montecarlo" disabled={!baseConfig}>
              Monte Carlo Simulation {!baseConfig && '(Run backtest first)'}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="backtest" className="space-y-8">
            <BacktestRunner onResultsReady={handleBacktestResults} />
            <BacktestResultsDisplay results={backtestResults} />
          </TabsContent>

          <TabsContent value="montecarlo" className="space-y-8">
            {baseConfig && (
              <>
                <MonteCarloRunner baseConfig={baseConfig} onResultsReady={setMonteCarloResults} />
                <MonteCarloResultsDisplay results={monteCarloResults} />
              </>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Backtest;
