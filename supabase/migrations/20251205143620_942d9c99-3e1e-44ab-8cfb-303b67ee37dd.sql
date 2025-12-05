-- Create unified aureon_user_sessions table
CREATE TABLE public.aureon_user_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Account
  binance_api_key_encrypted TEXT,
  binance_api_secret_encrypted TEXT,
  binance_iv TEXT,
  payment_completed BOOLEAN DEFAULT false,
  payment_completed_at TIMESTAMPTZ,
  
  -- Trading Status
  is_trading_active BOOLEAN DEFAULT false,
  trading_mode TEXT DEFAULT 'paper',
  
  -- Current Quantum State
  current_coherence NUMERIC DEFAULT 0,
  current_lambda NUMERIC DEFAULT 0,
  current_lighthouse_signal NUMERIC DEFAULT 0,
  dominant_node TEXT,
  prism_level INTEGER DEFAULT 0,
  prism_state TEXT DEFAULT 'FORMING',
  
  -- Balances
  total_equity_usdt NUMERIC DEFAULT 0,
  available_balance_usdt NUMERIC DEFAULT 0,
  
  -- Performance
  total_trades INTEGER DEFAULT 0,
  winning_trades INTEGER DEFAULT 0,
  total_pnl_usdt NUMERIC DEFAULT 0,
  gas_tank_balance NUMERIC DEFAULT 100,
  
  -- Recent Trades (JSON array)
  recent_trades JSONB DEFAULT '[]'::jsonb,
  
  -- Timestamps
  last_trade_at TIMESTAMPTZ,
  last_quantum_update_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(user_id)
);

-- Enable RLS
ALTER TABLE public.aureon_user_sessions ENABLE ROW LEVEL SECURITY;

-- Users can view their own session
CREATE POLICY "Users can view own session"
  ON public.aureon_user_sessions
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own session
CREATE POLICY "Users can insert own session"
  ON public.aureon_user_sessions
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own session
CREATE POLICY "Users can update own session"
  ON public.aureon_user_sessions
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Service role can manage all sessions
CREATE POLICY "Service can manage all sessions"
  ON public.aureon_user_sessions
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Enable realtime for live updates
ALTER PUBLICATION supabase_realtime ADD TABLE public.aureon_user_sessions;

-- Create trigger for updated_at
CREATE TRIGGER update_aureon_sessions_updated_at
  BEFORE UPDATE ON public.aureon_user_sessions
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();