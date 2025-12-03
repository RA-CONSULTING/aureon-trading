-- Create elephant_memory table for trade persistence
CREATE TABLE public.elephant_memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL UNIQUE,
  trades INTEGER DEFAULT 0,
  wins INTEGER DEFAULT 0,
  losses INTEGER DEFAULT 0,
  profit NUMERIC DEFAULT 0,
  last_trade TIMESTAMPTZ,
  loss_streak INTEGER DEFAULT 0,
  blacklisted BOOLEAN DEFAULT FALSE,
  cooldown_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.elephant_memory ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY "Service can manage elephant memory" 
ON public.elephant_memory FOR ALL 
USING (true) WITH CHECK (true);

CREATE POLICY "Authenticated users can read elephant memory" 
ON public.elephant_memory FOR SELECT 
USING (true);

-- Create unified_bus_snapshots table for bus state persistence
CREATE TABLE public.unified_bus_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  snapshot JSONB NOT NULL,
  consensus_signal TEXT,
  consensus_confidence NUMERIC,
  systems_ready INTEGER DEFAULT 0,
  total_systems INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.unified_bus_snapshots ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY "Service can manage bus snapshots" 
ON public.unified_bus_snapshots FOR ALL 
USING (true) WITH CHECK (true);

CREATE POLICY "Authenticated users can read bus snapshots" 
ON public.unified_bus_snapshots FOR SELECT 
USING (true);