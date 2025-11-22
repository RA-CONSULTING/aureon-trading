-- Automated Hunt Loop Tables

-- Hunt sessions track active/stopped hunts
CREATE TABLE public.hunt_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  hive_session_id UUID REFERENCES public.hive_sessions(id) ON DELETE CASCADE,
  
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'stopped')),
  
  -- Configuration
  min_volatility_pct NUMERIC NOT NULL DEFAULT 2.0,
  min_volume_usd NUMERIC NOT NULL DEFAULT 100000,
  max_targets INTEGER NOT NULL DEFAULT 5,
  scan_interval_seconds INTEGER NOT NULL DEFAULT 300, -- 5 minutes
  
  -- Statistics
  total_scans INTEGER NOT NULL DEFAULT 0,
  total_targets_found INTEGER NOT NULL DEFAULT 0,
  total_signals_generated INTEGER NOT NULL DEFAULT 0,
  total_orders_queued INTEGER NOT NULL DEFAULT 0,
  
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_scan_at TIMESTAMPTZ,
  stopped_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hunt targets are discovered opportunities
CREATE TABLE public.hunt_targets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hunt_session_id UUID NOT NULL REFERENCES public.hunt_sessions(id) ON DELETE CASCADE,
  
  -- Target info
  symbol TEXT NOT NULL,
  base_asset TEXT NOT NULL,
  quote_asset TEXT NOT NULL,
  
  -- Market metrics
  price NUMERIC NOT NULL,
  volume_24h NUMERIC NOT NULL,
  volatility_24h NUMERIC NOT NULL,
  opportunity_score NUMERIC NOT NULL,
  
  -- Processing status
  status TEXT NOT NULL DEFAULT 'discovered' CHECK (status IN ('discovered', 'analyzing', 'queued', 'rejected', 'error')),
  signal_generated BOOLEAN DEFAULT FALSE,
  order_queued BOOLEAN DEFAULT FALSE,
  
  -- Signal details (if generated)
  signal_type TEXT,
  signal_confidence NUMERIC,
  signal_tier INTEGER,
  rejection_reason TEXT,
  
  discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hunt scan history tracks each scan cycle
CREATE TABLE public.hunt_scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hunt_session_id UUID NOT NULL REFERENCES public.hunt_sessions(id) ON DELETE CASCADE,
  
  scan_duration_ms INTEGER NOT NULL,
  pairs_scanned INTEGER NOT NULL,
  targets_found INTEGER NOT NULL,
  signals_generated INTEGER NOT NULL,
  orders_queued INTEGER NOT NULL,
  
  top_symbol TEXT,
  top_score NUMERIC,
  
  scan_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_hunt_sessions_user ON public.hunt_sessions(user_id);
CREATE INDEX idx_hunt_sessions_status ON public.hunt_sessions(status);
CREATE INDEX idx_hunt_targets_session ON public.hunt_targets(hunt_session_id);
CREATE INDEX idx_hunt_targets_symbol ON public.hunt_targets(symbol);
CREATE INDEX idx_hunt_targets_score ON public.hunt_targets(opportunity_score DESC);
CREATE INDEX idx_hunt_scans_session ON public.hunt_scans(hunt_session_id);
CREATE INDEX idx_hunt_scans_timestamp ON public.hunt_scans(scan_timestamp DESC);

-- RLS Policies
ALTER TABLE public.hunt_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hunt_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hunt_scans ENABLE ROW LEVEL SECURITY;

-- Users manage their own hunt sessions
CREATE POLICY "Users manage own hunt sessions"
  ON public.hunt_sessions
  FOR ALL
  USING (auth.uid() = user_id);

-- Users view their hunt targets
CREATE POLICY "Users view own hunt targets"
  ON public.hunt_targets
  FOR SELECT
  USING (hunt_session_id IN (
    SELECT id FROM public.hunt_sessions WHERE user_id = auth.uid()
  ));

-- Service manages targets
CREATE POLICY "Service manages hunt targets"
  ON public.hunt_targets
  FOR ALL
  USING (true);

-- Users view their hunt scans
CREATE POLICY "Users view own hunt scans"
  ON public.hunt_scans
  FOR SELECT
  USING (hunt_session_id IN (
    SELECT id FROM public.hunt_sessions WHERE user_id = auth.uid()
  ));

-- Service manages scans
CREATE POLICY "Service manages hunt scans"
  ON public.hunt_scans
  FOR ALL
  USING (true);