-- Create auris_node_states table for the 9 animal totem readings
CREATE TABLE public.auris_node_states (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
  
  -- 9 Auris Nodes with their frequencies
  tiger_value NUMERIC NOT NULL DEFAULT 0,
  tiger_frequency NUMERIC NOT NULL DEFAULT 741,
  falcon_value NUMERIC NOT NULL DEFAULT 0,
  falcon_frequency NUMERIC NOT NULL DEFAULT 852,
  hummingbird_value NUMERIC NOT NULL DEFAULT 0,
  hummingbird_frequency NUMERIC NOT NULL DEFAULT 963,
  dolphin_value NUMERIC NOT NULL DEFAULT 0,
  dolphin_frequency NUMERIC NOT NULL DEFAULT 528,
  deer_value NUMERIC NOT NULL DEFAULT 0,
  deer_frequency NUMERIC NOT NULL DEFAULT 396,
  owl_value NUMERIC NOT NULL DEFAULT 0,
  owl_frequency NUMERIC NOT NULL DEFAULT 432,
  panda_value NUMERIC NOT NULL DEFAULT 0,
  panda_frequency NUMERIC NOT NULL DEFAULT 412,
  cargoship_value NUMERIC NOT NULL DEFAULT 0,
  cargoship_frequency NUMERIC NOT NULL DEFAULT 174,
  clownfish_value NUMERIC NOT NULL DEFAULT 0,
  clownfish_frequency NUMERIC NOT NULL DEFAULT 639,
  
  -- Aggregate metrics
  dominant_node TEXT NOT NULL DEFAULT 'dolphin',
  total_coherence NUMERIC NOT NULL DEFAULT 0,
  active_nodes INTEGER NOT NULL DEFAULT 9,
  harmonic_resonance NUMERIC NOT NULL DEFAULT 0,
  
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.auris_node_states ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY "Authenticated users can read auris_node_states"
ON public.auris_node_states FOR SELECT
USING (true);

CREATE POLICY "Service can insert auris_node_states"
ON public.auris_node_states FOR INSERT
WITH CHECK (true);

-- Create kelly_computation_states table for dynamic Kelly calculations
CREATE TABLE public.kelly_computation_states (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
  
  -- Kelly inputs from calibration_trades
  total_trades INTEGER NOT NULL DEFAULT 0,
  winning_trades INTEGER NOT NULL DEFAULT 0,
  losing_trades INTEGER NOT NULL DEFAULT 0,
  win_rate NUMERIC NOT NULL DEFAULT 0.5,
  avg_win NUMERIC NOT NULL DEFAULT 0,
  avg_loss NUMERIC NOT NULL DEFAULT 0,
  win_loss_ratio NUMERIC NOT NULL DEFAULT 1,
  
  -- Kelly computation
  kelly_fraction NUMERIC NOT NULL DEFAULT 0,
  kelly_half NUMERIC NOT NULL DEFAULT 0,
  kelly_quarter NUMERIC NOT NULL DEFAULT 0,
  recommended_position_pct NUMERIC NOT NULL DEFAULT 2.5,
  
  -- Safety bounds
  max_position_pct NUMERIC NOT NULL DEFAULT 5,
  min_position_pct NUMERIC NOT NULL DEFAULT 0.5,
  
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.kelly_computation_states ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY "Authenticated users can read kelly_computation_states"
ON public.kelly_computation_states FOR SELECT
USING (true);

CREATE POLICY "Service can insert kelly_computation_states"
ON public.kelly_computation_states FOR INSERT
WITH CHECK (true);