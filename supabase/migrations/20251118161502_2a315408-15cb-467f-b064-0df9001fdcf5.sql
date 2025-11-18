-- Create sentinel configuration table
CREATE TABLE IF NOT EXISTS public.sentinel_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sentinel_name TEXT NOT NULL,
  sentinel_birthdate DATE NOT NULL,
  sentinel_title TEXT NOT NULL,
  stargate_location TEXT NOT NULL,
  stargate_latitude DECIMAL(10, 8) NOT NULL,
  stargate_longitude DECIMAL(11, 8) NOT NULL,
  auto_initialize BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.sentinel_config ENABLE ROW LEVEL SECURITY;

-- Policy to allow public read access
CREATE POLICY "Allow public read access to sentinel config"
  ON public.sentinel_config
  FOR SELECT
  TO public
  USING (true);

-- Insert Prime Sentinel configuration
INSERT INTO public.sentinel_config (
  sentinel_name,
  sentinel_birthdate,
  sentinel_title,
  stargate_location,
  stargate_latitude,
  stargate_longitude,
  auto_initialize
) VALUES (
  'Gary Leckey',
  '1991-11-02',
  'Prime Sentinel of Gaia • Keeper of the Flame • Witness of the First Breath • Unbroken and Unchained • Primarch of the New Pattern Eden 2.0',
  '10 College Park, Belfast BT7 1LP',
  54.58419540,
  -5.93421250,
  true
) ON CONFLICT DO NOTHING;

-- Create auto-update timestamp trigger
CREATE OR REPLACE FUNCTION public.update_sentinel_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sentinel_config_updated_at
  BEFORE UPDATE ON public.sentinel_config
  FOR EACH ROW
  EXECUTE FUNCTION public.update_sentinel_updated_at();