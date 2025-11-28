-- Gas Tank Accounts (one per user)
CREATE TABLE gas_tank_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE,
  balance NUMERIC NOT NULL DEFAULT 0,
  initial_balance NUMERIC NOT NULL DEFAULT 0,
  high_water_mark NUMERIC NOT NULL DEFAULT 0,
  total_fees_paid NUMERIC NOT NULL DEFAULT 0,
  fees_paid_today NUMERIC NOT NULL DEFAULT 0,
  membership_type TEXT NOT NULL DEFAULT 'standard' CHECK (membership_type IN ('founder', 'standard')),
  fee_rate NUMERIC NOT NULL DEFAULT 0.20,
  status TEXT NOT NULL DEFAULT 'EMPTY' CHECK (status IN ('ACTIVE', 'LOW', 'CRITICAL', 'EMPTY', 'PAUSED')),
  last_top_up_at TIMESTAMPTZ,
  last_fee_deducted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Gas Tank Transactions (audit trail)
CREATE TABLE gas_tank_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES gas_tank_accounts(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('TOP_UP', 'FEE_DEDUCTION', 'REFUND', 'ADJUSTMENT')),
  amount NUMERIC NOT NULL,
  balance_before NUMERIC NOT NULL,
  balance_after NUMERIC NOT NULL,
  description TEXT,
  trade_execution_id UUID REFERENCES trading_executions(id),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_gas_tank_accounts_user_id ON gas_tank_accounts(user_id);
CREATE INDEX idx_gas_tank_accounts_status ON gas_tank_accounts(status);
CREATE INDEX idx_gas_tank_transactions_account_id ON gas_tank_transactions(account_id);
CREATE INDEX idx_gas_tank_transactions_type ON gas_tank_transactions(type);
CREATE INDEX idx_gas_tank_transactions_created_at ON gas_tank_transactions(created_at DESC);

-- RLS Policies
ALTER TABLE gas_tank_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE gas_tank_transactions ENABLE ROW LEVEL SECURITY;

-- Users can view their own gas tank
CREATE POLICY "Users view own gas tank" ON gas_tank_accounts
  FOR SELECT USING (auth.uid() = user_id);

-- Service role manages gas tanks
CREATE POLICY "Service manages gas tanks" ON gas_tank_accounts
  FOR ALL USING (true) WITH CHECK (true);

-- Users can view own transactions
CREATE POLICY "Users view own transactions" ON gas_tank_transactions
  FOR SELECT USING (account_id IN (SELECT id FROM gas_tank_accounts WHERE user_id = auth.uid()));

-- Service inserts transactions
CREATE POLICY "Service inserts transactions" ON gas_tank_transactions
  FOR INSERT WITH CHECK (true);

-- Enable realtime for live updates
ALTER PUBLICATION supabase_realtime ADD TABLE gas_tank_accounts;
ALTER PUBLICATION supabase_realtime ADD TABLE gas_tank_transactions;

-- Update trading_config for demo thresholds
UPDATE trading_config SET 
  min_coherence = 0.70,
  min_prism_level = 1,
  min_lighthouse_confidence = 0.50,
  max_daily_trades = 100
WHERE trading_mode = 'paper';