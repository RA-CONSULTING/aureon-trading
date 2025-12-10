-- Create calibration_trades table for trade history with frequency band classification
CREATE TABLE public.calibration_trades (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  entry_price NUMERIC NOT NULL,
  exit_price NUMERIC,
  entry_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  exit_time TIMESTAMP WITH TIME ZONE,
  quantity NUMERIC NOT NULL,
  position_size_usd NUMERIC NOT NULL,
  frequency_band TEXT NOT NULL,
  prism_frequency NUMERIC NOT NULL,
  coherence_at_entry NUMERIC NOT NULL,
  lambda_at_entry NUMERIC NOT NULL,
  lighthouse_confidence NUMERIC NOT NULL,
  hnc_probability NUMERIC NOT NULL,
  qgita_tier INTEGER NOT NULL DEFAULT 3,
  pnl NUMERIC,
  pnl_percent NUMERIC,
  is_win BOOLEAN,
  exchange TEXT NOT NULL DEFAULT 'binance',
  order_id TEXT,
  regime TEXT NOT NULL DEFAULT 'NORMAL',
  cosmic_phase TEXT,
  is_forced BOOLEAN DEFAULT false,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create adaptive_learning_states table for learned thresholds
CREATE TABLE public.adaptive_learning_states (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  min_coherence NUMERIC NOT NULL DEFAULT 0.45,
  min_confidence NUMERIC NOT NULL DEFAULT 0.50,
  max_position_pct NUMERIC NOT NULL DEFAULT 5.0,
  kelly_multiplier NUMERIC NOT NULL DEFAULT 0.5,
  learning_rate NUMERIC NOT NULL DEFAULT 0.01,
  total_trades_learned INTEGER NOT NULL DEFAULT 0,
  calibration_win_rate NUMERIC,
  calibration_profit_factor NUMERIC,
  band_performance JSONB DEFAULT '{}'::jsonb,
  tier_performance JSONB DEFAULT '{}'::jsonb,
  hourly_performance JSONB DEFAULT '{}'::jsonb,
  symbol_adjustments JSONB DEFAULT '{}'::jsonb,
  regime_adjustments JSONB DEFAULT '{}'::jsonb,
  confidence_score NUMERIC NOT NULL DEFAULT 0,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create exchange_learning_states table for per-exchange performance tracking
CREATE TABLE public.exchange_learning_states (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  total_trades INTEGER NOT NULL DEFAULT 0,
  wins INTEGER NOT NULL DEFAULT 0,
  losses INTEGER NOT NULL DEFAULT 0,
  total_profit NUMERIC NOT NULL DEFAULT 0,
  avg_latency_ms INTEGER,
  last_trade_at TIMESTAMP WITH TIME ZONE,
  win_rate NUMERIC,
  avg_pnl NUMERIC,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.calibration_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.adaptive_learning_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exchange_learning_states ENABLE ROW LEVEL SECURITY;

-- RLS policies for calibration_trades
CREATE POLICY "Authenticated users can read calibration_trades"
  ON public.calibration_trades FOR SELECT USING (true);
CREATE POLICY "Service can insert calibration_trades"
  ON public.calibration_trades FOR INSERT WITH CHECK (true);
CREATE POLICY "Service can update calibration_trades"
  ON public.calibration_trades FOR UPDATE USING (true);

-- RLS policies for adaptive_learning_states
CREATE POLICY "Authenticated users can read adaptive_learning_states"
  ON public.adaptive_learning_states FOR SELECT USING (true);
CREATE POLICY "Service can insert adaptive_learning_states"
  ON public.adaptive_learning_states FOR INSERT WITH CHECK (true);

-- RLS policies for exchange_learning_states
CREATE POLICY "Authenticated users can read exchange_learning_states"
  ON public.exchange_learning_states FOR SELECT USING (true);
CREATE POLICY "Service can insert exchange_learning_states"
  ON public.exchange_learning_states FOR INSERT WITH CHECK (true);

-- Create indexes for performance
CREATE INDEX idx_calibration_trades_symbol ON public.calibration_trades(symbol);
CREATE INDEX idx_calibration_trades_frequency_band ON public.calibration_trades(frequency_band);
CREATE INDEX idx_calibration_trades_temporal ON public.calibration_trades(temporal_id);
CREATE INDEX idx_adaptive_learning_temporal ON public.adaptive_learning_states(temporal_id);
CREATE INDEX idx_exchange_learning_exchange_symbol ON public.exchange_learning_states(exchange, symbol);