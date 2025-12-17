-- Create exchange balance cache table for rate limiting
CREATE TABLE IF NOT EXISTS public.exchange_balance_cache (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  exchange TEXT NOT NULL,
  balance_data JSONB NOT NULL,
  cached_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  CONSTRAINT unique_user_exchange UNIQUE (user_id, exchange)
);

-- Enable RLS
ALTER TABLE public.exchange_balance_cache ENABLE ROW LEVEL SECURITY;

-- Users can only read/write their own cache
CREATE POLICY "Users can read own cache" ON public.exchange_balance_cache
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own cache" ON public.exchange_balance_cache
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own cache" ON public.exchange_balance_cache
  FOR UPDATE USING (auth.uid() = user_id);

-- Service role can manage all
CREATE POLICY "Service role full access" ON public.exchange_balance_cache
  FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Index for fast lookups
CREATE INDEX idx_exchange_balance_cache_user_exchange ON public.exchange_balance_cache(user_id, exchange);