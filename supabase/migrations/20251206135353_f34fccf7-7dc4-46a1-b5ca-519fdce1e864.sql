-- Create ticker_snapshots table for persisting real-time ticker data
CREATE TABLE public.ticker_snapshots (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  exchange TEXT NOT NULL DEFAULT 'binance',
  price NUMERIC NOT NULL,
  bid_price NUMERIC,
  ask_price NUMERIC,
  volume NUMERIC,
  volume_usd NUMERIC,
  high_24h NUMERIC,
  low_24h NUMERIC,
  price_change_24h NUMERIC,
  volatility NUMERIC,
  momentum NUMERIC,
  spread NUMERIC,
  is_validated BOOLEAN DEFAULT false,
  validation_status TEXT DEFAULT 'pending',
  data_source TEXT DEFAULT 'live',
  fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create indexes for fast queries
CREATE INDEX idx_ticker_snapshots_symbol ON public.ticker_snapshots(symbol);
CREATE INDEX idx_ticker_snapshots_exchange ON public.ticker_snapshots(exchange);
CREATE INDEX idx_ticker_snapshots_fetched_at ON public.ticker_snapshots(fetched_at DESC);
CREATE INDEX idx_ticker_snapshots_temporal ON public.ticker_snapshots(temporal_id);

-- Enable RLS
ALTER TABLE public.ticker_snapshots ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read ticker data
CREATE POLICY "Users can read ticker snapshots" 
ON public.ticker_snapshots 
FOR SELECT 
TO authenticated
USING (true);

-- Allow service role to insert ticker data
CREATE POLICY "Service role can insert ticker snapshots"
ON public.ticker_snapshots
FOR INSERT
WITH CHECK (true);

-- Create data_validation_log table for tracking data quality
CREATE TABLE public.data_validation_log (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  exchange TEXT NOT NULL,
  validation_type TEXT NOT NULL,
  is_valid BOOLEAN NOT NULL,
  error_message TEXT,
  packet_timestamp TIMESTAMP WITH TIME ZONE,
  validation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_validation_log_exchange ON public.data_validation_log(exchange);
CREATE INDEX idx_validation_log_timestamp ON public.data_validation_log(validation_timestamp DESC);

ALTER TABLE public.data_validation_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read validation logs" 
ON public.data_validation_log 
FOR SELECT 
TO authenticated
USING (true);

CREATE POLICY "Service role can insert validation logs"
ON public.data_validation_log
FOR INSERT
WITH CHECK (true);