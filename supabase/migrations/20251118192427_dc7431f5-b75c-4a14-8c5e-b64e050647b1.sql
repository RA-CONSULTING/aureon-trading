-- Create stargate_network_states table for historical network metrics
CREATE TABLE IF NOT EXISTS public.stargate_network_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  sentinel_name TEXT,
  active_nodes INTEGER NOT NULL,
  network_strength NUMERIC NOT NULL,
  grid_energy NUMERIC NOT NULL,
  avg_coherence NUMERIC,
  avg_frequency NUMERIC,
  phase_locks INTEGER,
  resonance_quality NUMERIC,
  metadata JSONB DEFAULT '{}'::jsonb,
  event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create index for efficient temporal queries
CREATE INDEX idx_stargate_network_temporal ON public.stargate_network_states(temporal_id, event_timestamp DESC);

-- Create index for time-based queries
CREATE INDEX idx_stargate_network_timestamp ON public.stargate_network_states(event_timestamp DESC);

-- Enable RLS
ALTER TABLE public.stargate_network_states ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for public access
CREATE POLICY "Allow public read access to stargate network states"
  ON public.stargate_network_states
  FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to stargate network states"
  ON public.stargate_network_states
  FOR INSERT
  WITH CHECK (true);