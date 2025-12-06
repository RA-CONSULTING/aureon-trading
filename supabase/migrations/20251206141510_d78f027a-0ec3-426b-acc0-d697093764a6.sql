-- Create telescope_observations table for Quantum Telescope persistence
CREATE TABLE public.telescope_observations (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  symbol TEXT NOT NULL DEFAULT 'BTCUSDT',
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  
  -- Light Beam input data
  beam_intensity NUMERIC NOT NULL DEFAULT 0,
  beam_wavelength NUMERIC NOT NULL DEFAULT 0,
  beam_velocity NUMERIC NOT NULL DEFAULT 0,
  beam_angle NUMERIC NOT NULL DEFAULT 0,
  beam_polarization NUMERIC NOT NULL DEFAULT 0,
  
  -- Geometric solid resonances (5 Platonic solids)
  tetrahedron_resonance NUMERIC NOT NULL DEFAULT 0,
  hexahedron_resonance NUMERIC NOT NULL DEFAULT 0,
  octahedron_resonance NUMERIC NOT NULL DEFAULT 0,
  icosahedron_resonance NUMERIC NOT NULL DEFAULT 0,
  dodecahedron_resonance NUMERIC NOT NULL DEFAULT 0,
  
  -- Computed outputs
  geometric_alignment NUMERIC NOT NULL DEFAULT 0,
  dominant_solid TEXT NOT NULL DEFAULT 'Tetrahedron',
  probability_spectrum JSONB DEFAULT '[]'::jsonb,
  holographic_projection JSONB DEFAULT '{}'::jsonb,
  focal_coherence NUMERIC NOT NULL DEFAULT 0,
  
  -- Prism integration
  prism_boost_factor NUMERIC NOT NULL DEFAULT 1,
  
  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable RLS
ALTER TABLE public.telescope_observations ENABLE ROW LEVEL SECURITY;

-- Create policy for public read (system data)
CREATE POLICY "Allow public read for telescope observations"
ON public.telescope_observations
FOR SELECT
USING (true);

-- Create policy for authenticated insert
CREATE POLICY "Allow authenticated insert for telescope observations"
ON public.telescope_observations
FOR INSERT
WITH CHECK (true);

-- Create index for temporal lookups
CREATE INDEX idx_telescope_observations_temporal ON public.telescope_observations(temporal_id, timestamp DESC);
CREATE INDEX idx_telescope_observations_symbol ON public.telescope_observations(symbol, timestamp DESC);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.telescope_observations;