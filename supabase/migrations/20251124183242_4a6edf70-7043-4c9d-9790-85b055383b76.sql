-- ============================================
-- AUREON Harmonic Reality Framework - Backend Tables
-- ============================================

-- Rainbow Bridge Emotional Frequency States
CREATE TABLE IF NOT EXISTS public.rainbow_bridge_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Temporal Identity
  temporal_id TEXT NOT NULL,
  sentinel_name TEXT,
  
  -- Frequency Data
  frequency NUMERIC NOT NULL,
  base_frequency NUMERIC NOT NULL,
  harmonic_index INTEGER NOT NULL,
  
  -- Phase Information
  phase TEXT NOT NULL,
  phase_transition BOOLEAN DEFAULT false,
  previous_phase TEXT,
  
  -- Emotional State
  valence NUMERIC NOT NULL CHECK (valence >= 0 AND valence <= 1),
  arousal NUMERIC NOT NULL CHECK (arousal >= 0 AND arousal <= 1),
  dominant_emotion TEXT NOT NULL,
  emotional_tags TEXT[] DEFAULT '{}',
  
  -- Color and Visual
  color TEXT NOT NULL,
  intensity NUMERIC NOT NULL CHECK (intensity >= 0 AND intensity <= 1),
  
  -- Coherence and Alignment
  coherence NUMERIC NOT NULL CHECK (coherence >= 0 AND coherence <= 1),
  lambda_value NUMERIC NOT NULL,
  
  metadata JSONB DEFAULT '{}'
);

-- Prism Transformation States
CREATE TABLE IF NOT EXISTS public.prism_transformation_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Temporal Identity
  temporal_id TEXT NOT NULL,
  sentinel_name TEXT,
  
  -- Prism State
  level INTEGER NOT NULL CHECK (level >= 1 AND level <= 5),
  state TEXT NOT NULL,
  frequency NUMERIC NOT NULL,
  is_love_locked BOOLEAN DEFAULT false,
  
  -- Input Values
  lambda_value NUMERIC NOT NULL,
  coherence NUMERIC NOT NULL CHECK (coherence >= 0 AND coherence <= 1),
  input_frequency NUMERIC NOT NULL,
  
  -- Transformation Metrics
  transformation_quality NUMERIC NOT NULL CHECK (transformation_quality >= 0 AND transformation_quality <= 1),
  harmonic_purity NUMERIC NOT NULL CHECK (harmonic_purity >= 0 AND harmonic_purity <= 1),
  resonance_strength NUMERIC NOT NULL CHECK (resonance_strength >= 0 AND resonance_strength <= 1),
  
  -- Lighthouse Correlation
  lighthouse_event_id UUID REFERENCES public.lighthouse_events(id),
  lighthouse_signal NUMERIC,
  is_lhe_correlated BOOLEAN DEFAULT false,
  
  metadata JSONB DEFAULT '{}'
);

-- Master Equation Field History
CREATE TABLE IF NOT EXISTS public.master_equation_field_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  temporal_id TEXT NOT NULL,
  sentinel_name TEXT,
  
  -- Master Equation Components: Λ(t) = S(t) + O(t) + E(t)
  lambda NUMERIC NOT NULL,
  substrate NUMERIC NOT NULL,
  observer NUMERIC NOT NULL,
  echo NUMERIC NOT NULL,
  
  -- Coherence Metrics
  coherence NUMERIC NOT NULL CHECK (coherence >= 0 AND coherence <= 1),
  coherence_linear NUMERIC NOT NULL DEFAULT 1.0,
  coherence_nonlinear NUMERIC NOT NULL,
  coherence_phi NUMERIC NOT NULL,
  
  -- Field Quality Metrics
  effective_gain NUMERIC NOT NULL,
  quality_factor NUMERIC NOT NULL,
  
  -- Dominant Node
  dominant_node TEXT NOT NULL,
  node_weights JSONB NOT NULL DEFAULT '{}',
  
  -- Market Context (optional)
  symbol TEXT,
  price NUMERIC,
  volume NUMERIC,
  volatility NUMERIC,
  momentum NUMERIC,
  
  metadata JSONB DEFAULT '{}'
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_rainbow_bridge_temporal_time ON public.rainbow_bridge_states(temporal_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_rainbow_bridge_phase ON public.rainbow_bridge_states(phase, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_prism_temporal_time ON public.prism_transformation_states(temporal_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_prism_love_locked ON public.prism_transformation_states(is_love_locked, timestamp DESC) WHERE is_love_locked = true;

CREATE INDEX IF NOT EXISTS idx_master_eq_temporal_time ON public.master_equation_field_history(temporal_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_master_eq_coherence ON public.master_equation_field_history(coherence DESC, timestamp DESC);

-- Enable Row Level Security
ALTER TABLE public.rainbow_bridge_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prism_transformation_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.master_equation_field_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Authenticated users can read rainbow bridge states"
ON public.rainbow_bridge_states FOR SELECT TO authenticated USING (true);

CREATE POLICY "Service role can insert rainbow bridge states"
ON public.prism_transformation_states FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Authenticated users can read prism states"
ON public.prism_transformation_states FOR SELECT TO authenticated USING (true);

CREATE POLICY "Service role can insert prism states"
ON public.prism_transformation_states FOR INSERT TO service_role WITH CHECK (true);

CREATE POLICY "Authenticated users can read master equation history"
ON public.master_equation_field_history FOR SELECT TO authenticated USING (true);

CREATE POLICY "Service role can insert master equation history"
ON public.master_equation_field_history FOR INSERT TO service_role WITH CHECK (true);

-- Enable Realtime
ALTER TABLE public.rainbow_bridge_states REPLICA IDENTITY FULL;
ALTER TABLE public.prism_transformation_states REPLICA IDENTITY FULL;
ALTER TABLE public.master_equation_field_history REPLICA IDENTITY FULL;

ALTER PUBLICATION supabase_realtime ADD TABLE public.rainbow_bridge_states;
ALTER PUBLICATION supabase_realtime ADD TABLE public.prism_transformation_states;
ALTER PUBLICATION supabase_realtime ADD TABLE public.master_equation_field_history;