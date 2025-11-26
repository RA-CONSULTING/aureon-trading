-- Add INSERT policy for rainbow_bridge_states
CREATE POLICY "Service role can insert rainbow bridge states"
ON public.rainbow_bridge_states
FOR INSERT
WITH CHECK (true);

-- Create storage buckets for data archival
INSERT INTO storage.buckets (id, name, public) 
VALUES 
  ('trading-logs', 'trading-logs', false),
  ('quantum-states', 'quantum-states', false)
ON CONFLICT (id) DO NOTHING;

-- Add RLS policies for storage buckets
CREATE POLICY "Service can manage trading logs"
ON storage.objects
FOR ALL
USING (bucket_id = 'trading-logs')
WITH CHECK (bucket_id = 'trading-logs');

CREATE POLICY "Service can manage quantum states"
ON storage.objects
FOR ALL
USING (bucket_id = 'quantum-states')
WITH CHECK (bucket_id = 'quantum-states');