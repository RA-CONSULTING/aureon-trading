-- Create table for multiple Binance API credentials
CREATE TABLE IF NOT EXISTS public.binance_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  api_key_encrypted TEXT NOT NULL,
  api_secret_encrypted TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  last_used_at TIMESTAMP WITH TIME ZONE,
  requests_count INTEGER DEFAULT 0,
  rate_limit_reset_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.binance_credentials ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can manage all credentials
CREATE POLICY "Service role can manage credentials"
  ON public.binance_credentials
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Add updated_at trigger
CREATE TRIGGER update_binance_credentials_updated_at
  BEFORE UPDATE ON public.binance_credentials
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- Create index for efficient lookups
CREATE INDEX idx_binance_credentials_active ON public.binance_credentials(is_active, last_used_at);
CREATE INDEX idx_binance_credentials_rate_limit ON public.binance_credentials(rate_limit_reset_at);