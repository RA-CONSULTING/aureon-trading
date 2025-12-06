-- Create prime_seal_packets table for 10-9-1 data packet stream
CREATE TABLE public.prime_seal_packets (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  intent_text TEXT,
  w_unity_10 NUMERIC NOT NULL DEFAULT 10,
  w_flow_9 NUMERIC NOT NULL DEFAULT 9,
  w_anchor_1 NUMERIC NOT NULL DEFAULT 1,
  amplitude_gain NUMERIC NOT NULL DEFAULT 1.0,
  packet_value NUMERIC NOT NULL DEFAULT 0,
  seal_lock BOOLEAN NOT NULL DEFAULT false,
  prime_coherence NUMERIC NOT NULL DEFAULT 0,
  lattice_phase NUMERIC NOT NULL DEFAULT 0,
  systems_contributing JSONB DEFAULT '[]'::jsonb,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.prime_seal_packets ENABLE ROW LEVEL SECURITY;

-- Policy: Authenticated users can read
CREATE POLICY "Authenticated users can read prime_seal_packets"
ON public.prime_seal_packets
FOR SELECT
USING (true);

-- Policy: Service role can insert
CREATE POLICY "Service can insert prime_seal_packets"
ON public.prime_seal_packets
FOR INSERT
WITH CHECK (true);

-- Create index for temporal_id lookups
CREATE INDEX idx_prime_seal_packets_temporal_id ON public.prime_seal_packets(temporal_id);
CREATE INDEX idx_prime_seal_packets_timestamp ON public.prime_seal_packets(timestamp DESC);

-- Enable realtime for live dashboard updates
ALTER PUBLICATION supabase_realtime ADD TABLE public.prime_seal_packets;