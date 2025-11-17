-- Create monte_carlo_simulations table
CREATE TABLE IF NOT EXISTS public.monte_carlo_simulations (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  symbol TEXT NOT NULL,
  start_date TIMESTAMP WITH TIME ZONE NOT NULL,
  end_date TIMESTAMP WITH TIME ZONE NOT NULL,
  num_simulations INTEGER NOT NULL,
  base_config JSONB NOT NULL,
  randomization_method TEXT NOT NULL,
  results JSONB NOT NULL,
  confidence_intervals JSONB NOT NULL,
  distribution_stats JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'completed'
);

-- Enable RLS
ALTER TABLE public.monte_carlo_simulations ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow public read access to monte carlo simulations"
  ON public.monte_carlo_simulations
  FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to monte carlo simulations"
  ON public.monte_carlo_simulations
  FOR INSERT
  WITH CHECK (true);

-- Create index
CREATE INDEX idx_monte_carlo_simulations_symbol ON public.monte_carlo_simulations(symbol);
CREATE INDEX idx_monte_carlo_simulations_created_at ON public.monte_carlo_simulations(created_at DESC);