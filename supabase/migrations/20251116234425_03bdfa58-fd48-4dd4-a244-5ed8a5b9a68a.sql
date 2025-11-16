-- Create table for Lighthouse Events (LHEs)
CREATE TABLE public.lighthouse_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  lambda_value DECIMAL NOT NULL,
  coherence DECIMAL NOT NULL,
  lighthouse_signal DECIMAL NOT NULL,
  threshold DECIMAL NOT NULL,
  confidence DECIMAL NOT NULL,
  is_lhe BOOLEAN NOT NULL,
  
  -- Five consensus metrics
  metric_clin DECIMAL NOT NULL,
  metric_cnonlin DECIMAL NOT NULL,
  metric_cphi DECIMAL NOT NULL,
  metric_geff DECIMAL NOT NULL,
  metric_q DECIMAL NOT NULL,
  
  -- Additional context
  dominant_node TEXT,
  prism_level INTEGER,
  prism_state TEXT,
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create table for Trading Signals
CREATE TABLE public.trading_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  signal_type TEXT NOT NULL CHECK (signal_type IN ('LONG', 'SHORT', 'HOLD')),
  strength DECIMAL NOT NULL CHECK (strength >= 0 AND strength <= 1),
  
  -- Related metrics
  lighthouse_value DECIMAL NOT NULL,
  coherence DECIMAL NOT NULL,
  prism_level INTEGER NOT NULL,
  
  -- Signal reasoning
  reason TEXT NOT NULL,
  
  -- Link to lighthouse event if applicable
  lighthouse_event_id UUID REFERENCES public.lighthouse_events(id),
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX idx_lighthouse_events_timestamp ON public.lighthouse_events(timestamp DESC);
CREATE INDEX idx_lighthouse_events_is_lhe ON public.lighthouse_events(is_lhe) WHERE is_lhe = true;
CREATE INDEX idx_trading_signals_timestamp ON public.trading_signals(timestamp DESC);
CREATE INDEX idx_trading_signals_type ON public.trading_signals(signal_type);

-- Enable Row Level Security
ALTER TABLE public.lighthouse_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trading_signals ENABLE ROW LEVEL SECURITY;

-- Create policies (public read access for now, will be user-scoped when auth is added)
CREATE POLICY "Allow public read access to lighthouse events"
  ON public.lighthouse_events
  FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to lighthouse events"
  ON public.lighthouse_events
  FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public read access to trading signals"
  ON public.trading_signals
  FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to trading signals"
  ON public.trading_signals
  FOR INSERT
  WITH CHECK (true);

-- Enable realtime for both tables
ALTER TABLE public.lighthouse_events REPLICA IDENTITY FULL;
ALTER TABLE public.trading_signals REPLICA IDENTITY FULL;

-- Create view for recent optimal signals
CREATE VIEW public.recent_optimal_signals AS
SELECT 
  ts.id,
  ts.timestamp,
  ts.signal_type,
  ts.strength,
  ts.reason,
  ts.coherence,
  ts.lighthouse_value,
  le.is_lhe,
  le.lighthouse_signal,
  le.confidence as lhe_confidence
FROM public.trading_signals ts
LEFT JOIN public.lighthouse_events le ON ts.lighthouse_event_id = le.id
WHERE ts.signal_type = 'LONG' 
  AND ts.strength > 0.7
  AND ts.timestamp > now() - interval '24 hours'
ORDER BY ts.timestamp DESC;

-- Create function to get signal statistics
CREATE OR REPLACE FUNCTION public.get_signal_statistics(
  time_range INTERVAL DEFAULT '24 hours'
)
RETURNS TABLE (
  total_signals BIGINT,
  long_signals BIGINT,
  short_signals BIGINT,
  hold_signals BIGINT,
  optimal_signals BIGINT,
  avg_strength DECIMAL,
  lhe_count BIGINT
) 
LANGUAGE SQL
STABLE
AS $$
  SELECT 
    COUNT(*)::BIGINT as total_signals,
    COUNT(*) FILTER (WHERE signal_type = 'LONG')::BIGINT as long_signals,
    COUNT(*) FILTER (WHERE signal_type = 'SHORT')::BIGINT as short_signals,
    COUNT(*) FILTER (WHERE signal_type = 'HOLD')::BIGINT as hold_signals,
    COUNT(*) FILTER (WHERE reason LIKE '🎯 OPTIMAL%')::BIGINT as optimal_signals,
    AVG(strength) as avg_strength,
    (SELECT COUNT(*)::BIGINT FROM public.lighthouse_events 
     WHERE is_lhe = true 
     AND timestamp > now() - time_range) as lhe_count
  FROM public.trading_signals
  WHERE timestamp > now() - time_range;
$$;