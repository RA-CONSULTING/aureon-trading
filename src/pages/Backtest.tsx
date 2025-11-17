import { useState } from 'react';
import Navbar from '@/components/Navbar';
import { BacktestRunner } from '@/components/BacktestRunner';
import { BacktestResultsDisplay } from '@/components/BacktestResults';
import type { BacktestResults } from '@/core/backtestEngine';

const Backtest = () => {
  const [results, setResults] = useState<BacktestResults | null>(null);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">🔬 AUREON Backtesting System</h1>
          <p className="text-muted-foreground">
            Validate trading strategy on historical data before live deployment
          </p>
        </div>

        <div className="space-y-8">
          <BacktestRunner onResultsReady={setResults} />
          <BacktestResultsDisplay results={results} />
        </div>
      </main>
    </div>
  );
};

export default Backtest;
