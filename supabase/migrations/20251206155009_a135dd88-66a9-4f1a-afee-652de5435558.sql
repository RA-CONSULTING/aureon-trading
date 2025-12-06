-- Decision Audit Log Table
-- Tracks all BUY/SELL/HOLD decisions with full metrics and outcome verification

CREATE TABLE IF NOT EXISTS public.decision_audit_log (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  symbol TEXT NOT NULL DEFAULT 'BTCUSDT',
  decision_action TEXT NOT NULL CHECK (decision_action IN ('BUY', 'SELL', 'HOLD')),
  confidence NUMERIC(5,4) NOT NULL,
  
  -- Input metrics at decision time
  coherence NUMERIC(5,4) NOT NULL,
  lambda NUMERIC(8,4) NOT NULL,
  lighthouse_l NUMERIC(5,4),
  qgita_tier INTEGER,
  qgita_confidence NUMERIC(5,4),
  prism_frequency NUMERIC(8,2),
  prism_level INTEGER,
  wave_state TEXT,
  harmonic_lock BOOLEAN DEFAULT false,
  probability_fused NUMERIC(5,4),
  sentiment_score NUMERIC(5,4),
  geometric_alignment NUMERIC(5,4),
  
  -- Price tracking for outcome verification
  price_at_decision NUMERIC(20,8),
  price_after_1m NUMERIC(20,8),
  price_after_5m NUMERIC(20,8),
  price_after_15m NUMERIC(20,8),
  
  -- Outcome verification
  actual_direction_1m TEXT CHECK (actual_direction_1m IN ('UP', 'DOWN', 'FLAT')),
  actual_direction_5m TEXT CHECK (actual_direction_5m IN ('UP', 'DOWN', 'FLAT')),
  actual_direction_15m TEXT CHECK (actual_direction_15m IN ('UP', 'DOWN', 'FLAT')),
  accuracy_1m BOOLEAN,
  accuracy_5m BOOLEAN,
  accuracy_15m BOOLEAN,
  
  -- Decision explanation
  summary TEXT,
  reasoning JSONB,
  factors JSONB,
  
  -- Timestamps
  decision_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.decision_audit_log ENABLE ROW LEVEL SECURITY;

-- Users can only see their own decisions
CREATE POLICY "Users can view their own decisions"
  ON public.decision_audit_log
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own decisions"
  ON public.decision_audit_log
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own decisions"
  ON public.decision_audit_log
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Indexes for efficient querying
CREATE INDEX idx_decision_audit_user_symbol ON public.decision_audit_log(user_id, symbol);
CREATE INDEX idx_decision_audit_timestamp ON public.decision_audit_log(decision_timestamp DESC);
CREATE INDEX idx_decision_audit_action ON public.decision_audit_log(decision_action);
CREATE INDEX idx_decision_audit_unverified ON public.decision_audit_log(verified_at) WHERE verified_at IS NULL;