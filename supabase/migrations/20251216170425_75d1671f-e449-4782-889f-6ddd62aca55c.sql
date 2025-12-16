-- Create simple trade records table
CREATE TABLE IF NOT EXISTS public.trade_records (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  transaction_id TEXT NOT NULL,
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  price NUMERIC NOT NULL,
  quantity NUMERIC NOT NULL,
  quote_qty NUMERIC,
  fee NUMERIC DEFAULT 0,
  fee_asset TEXT,
  timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  user_id UUID REFERENCES auth.users(id)
);

-- Enable RLS
ALTER TABLE public.trade_records ENABLE ROW LEVEL SECURITY;

-- Users can only see their own trades
CREATE POLICY "Users can view own trades" ON public.trade_records
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own trades" ON public.trade_records
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.trade_records;

-- Index for fast lookups
CREATE INDEX idx_trade_records_user_timestamp ON public.trade_records(user_id, timestamp DESC);
CREATE INDEX idx_trade_records_transaction_id ON public.trade_records(transaction_id);