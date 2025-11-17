-- Create backtest_results table
CREATE TABLE IF NOT EXISTS public.backtest_results (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  symbol TEXT NOT NULL,
  start_date TIMESTAMP WITH TIME ZONE NOT NULL,
  end_date TIMESTAMP WITH TIME ZONE NOT NULL,
  initial_capital NUMERIC NOT NULL,
  final_capital NUMERIC NOT NULL,
  total_return NUMERIC NOT NULL,
  total_trades INTEGER NOT NULL,
  winning_trades INTEGER NOT NULL,
  losing_trades INTEGER NOT NULL,
  win_rate NUMERIC NOT NULL,
  profit_factor NUMERIC NOT NULL,
  max_drawdown NUMERIC NOT NULL,
  sharpe_ratio NUMERIC,
  avg_trade_duration NUMERIC,
  config JSONB NOT NULL,
  trades JSONB NOT NULL,
  equity_curve JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'completed'
);

-- Enable RLS
ALTER TABLE public.backtest_results ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust as needed)
CREATE POLICY "Allow public read access to backtest results"
  ON public.backtest_results
  FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to backtest results"
  ON public.backtest_results
  FOR INSERT
  WITH CHECK (true);

-- Create index for faster queries
CREATE INDEX idx_backtest_results_symbol ON public.backtest_results(symbol);
CREATE INDEX idx_backtest_results_created_at ON public.backtest_results(created_at DESC);