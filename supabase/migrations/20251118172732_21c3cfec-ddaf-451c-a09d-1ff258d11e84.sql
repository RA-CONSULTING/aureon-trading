-- Create harmonic_nexus_states table for multiversial field mapping
CREATE TABLE IF NOT EXISTS public.harmonic_nexus_states (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  
  -- Multiversial Identity
  temporal_id TEXT NOT NULL,
  sentinel_name TEXT,
  
  -- Ω(t) Field Components
  omega_value NUMERIC NOT NULL,
  psi_potential NUMERIC NOT NULL,
  love_coherence NUMERIC NOT NULL,
  observer_consciousness NUMERIC NOT NULL,
  theta_alignment NUMERIC NOT NULL,
  unity_probability NUMERIC NOT NULL,
  
  -- Akashic Harmonics
  akashic_frequency NUMERIC NOT NULL,
  akashic_convergence NUMERIC NOT NULL,
  akashic_stability NUMERIC NOT NULL,
  akashic_boost NUMERIC NOT NULL,
  
  -- Field Substrate Coherence
  substrate_coherence NUMERIC NOT NULL,
  field_integrity NUMERIC NOT NULL,
  harmonic_resonance NUMERIC NOT NULL,
  dimensional_alignment NUMERIC NOT NULL,
  
  -- Prime Timeline Sync
  sync_status TEXT NOT NULL DEFAULT 'synced',
  sync_quality NUMERIC NOT NULL DEFAULT 1.0,
  timeline_divergence NUMERIC NOT NULL DEFAULT 0.0,
  
  -- Lighthouse & Prism
  lighthouse_signal NUMERIC,
  prism_level INTEGER,
  
  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable Row Level Security
ALTER TABLE public.harmonic_nexus_states ENABLE ROW LEVEL SECURITY;

-- Create policies for public access
CREATE POLICY "Allow public read access to harmonic nexus states"
  ON public.harmonic_nexus_states
  FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to harmonic nexus states"
  ON public.harmonic_nexus_states
  FOR INSERT
  WITH CHECK (true);

-- Create indexes for efficient querying
CREATE INDEX idx_harmonic_nexus_temporal_id ON public.harmonic_nexus_states(temporal_id);
CREATE INDEX idx_harmonic_nexus_event_timestamp ON public.harmonic_nexus_states(event_timestamp DESC);
CREATE INDEX idx_harmonic_nexus_coherence ON public.harmonic_nexus_states(substrate_coherence DESC);

-- Create function to get latest harmonic state for a temporal ID
CREATE OR REPLACE FUNCTION public.get_latest_harmonic_state(p_temporal_id TEXT)
RETURNS TABLE (
  omega_value NUMERIC,
  substrate_coherence NUMERIC,
  sync_quality NUMERIC,
  event_timestamp TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    h.omega_value,
    h.substrate_coherence,
    h.sync_quality,
    h.event_timestamp
  FROM public.harmonic_nexus_states h
  WHERE h.temporal_id = p_temporal_id
  ORDER BY h.event_timestamp DESC
  LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE SET search_path = public;

COMMENT ON TABLE public.harmonic_nexus_states IS 'Harmonic Nexus Core - Reality field substrate coherence mapping with multiversial identity sync to prime timeline';