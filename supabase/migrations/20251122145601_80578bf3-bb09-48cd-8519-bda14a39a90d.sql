-- Queen-Hive Multi-Agent Trading System Schema

-- Hive instances (each hive is a capital pool with agents)
CREATE TABLE IF NOT EXISTS hive_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_hive_id UUID REFERENCES hive_instances(id),
  generation INTEGER NOT NULL DEFAULT 0,
  initial_balance NUMERIC NOT NULL,
  current_balance NUMERIC NOT NULL,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'harvested')),
  num_agents INTEGER NOT NULL DEFAULT 5,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Trading agents within hives
CREATE TABLE IF NOT EXISTS hive_agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hive_id UUID NOT NULL REFERENCES hive_instances(id) ON DELETE CASCADE,
  agent_index INTEGER NOT NULL,
  current_symbol TEXT NOT NULL,
  position_open BOOLEAN NOT NULL DEFAULT false,
  position_entry_price NUMERIC,
  position_quantity NUMERIC,
  position_side TEXT CHECK (position_side IN ('BUY', 'SELL')),
  total_pnl NUMERIC NOT NULL DEFAULT 0,
  trades_count INTEGER NOT NULL DEFAULT 0,
  last_trade_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(hive_id, agent_index)
);

-- Hive orchestration sessions (tracks Queen-Hive runs)
CREATE TABLE IF NOT EXISTS hive_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  root_hive_id UUID NOT NULL REFERENCES hive_instances(id),
  status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'paused', 'stopped')),
  initial_capital NUMERIC NOT NULL,
  current_equity NUMERIC NOT NULL,
  total_hives_spawned INTEGER NOT NULL DEFAULT 1,
  total_agents INTEGER NOT NULL DEFAULT 5,
  total_trades INTEGER NOT NULL DEFAULT 0,
  steps_executed INTEGER NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  stopped_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Hive trade executions (separate from trading_executions for hive tracking)
CREATE TABLE IF NOT EXISTS hive_trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES hive_sessions(id) ON DELETE CASCADE,
  hive_id UUID NOT NULL REFERENCES hive_instances(id) ON DELETE CASCADE,
  agent_id UUID NOT NULL REFERENCES hive_agents(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  entry_price NUMERIC NOT NULL,
  exit_price NUMERIC,
  quantity NUMERIC NOT NULL,
  pnl NUMERIC,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
  opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE hive_instances ENABLE ROW LEVEL SECURITY;
ALTER TABLE hive_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE hive_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE hive_trades ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can view their own hive data
CREATE POLICY "Users view own hive instances"
  ON hive_instances FOR SELECT
  USING (
    id IN (
      SELECT root_hive_id FROM hive_sessions WHERE user_id = auth.uid()
    ) OR parent_hive_id IN (
      SELECT root_hive_id FROM hive_sessions WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users view own agents"
  ON hive_agents FOR SELECT
  USING (
    hive_id IN (
      SELECT id FROM hive_instances 
      WHERE id IN (SELECT root_hive_id FROM hive_sessions WHERE user_id = auth.uid())
    )
  );

CREATE POLICY "Users view own sessions"
  ON hive_sessions FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users insert own sessions"
  ON hive_sessions FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users update own sessions"
  ON hive_sessions FOR UPDATE
  USING (user_id = auth.uid());

CREATE POLICY "Users view own hive trades"
  ON hive_trades FOR SELECT
  USING (
    session_id IN (SELECT id FROM hive_sessions WHERE user_id = auth.uid())
  );

-- Service role policies for hive orchestrator
CREATE POLICY "Service manages hive instances"
  ON hive_instances FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service manages agents"
  ON hive_agents FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service manages sessions"
  ON hive_sessions FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service manages hive trades"
  ON hive_trades FOR ALL
  USING (true)
  WITH CHECK (true);

-- Indexes for performance
CREATE INDEX idx_hive_instances_parent ON hive_instances(parent_hive_id);
CREATE INDEX idx_hive_agents_hive ON hive_agents(hive_id);
CREATE INDEX idx_hive_sessions_user ON hive_sessions(user_id);
CREATE INDEX idx_hive_sessions_status ON hive_sessions(status);
CREATE INDEX idx_hive_trades_session ON hive_trades(session_id);
CREATE INDEX idx_hive_trades_agent ON hive_trades(agent_id);