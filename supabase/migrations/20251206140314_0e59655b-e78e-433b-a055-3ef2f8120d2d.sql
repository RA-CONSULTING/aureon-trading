-- Create crypto assets registry table for all tradeable assets
CREATE TABLE public.crypto_assets_registry (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  symbol TEXT NOT NULL,
  base_asset TEXT NOT NULL,
  quote_asset TEXT NOT NULL,
  exchange TEXT NOT NULL DEFAULT 'binance',
  min_qty NUMERIC,
  max_qty NUMERIC,
  step_size NUMERIC,
  min_notional NUMERIC,
  tick_size NUMERIC,
  price_precision INTEGER,
  quantity_precision INTEGER,
  is_active BOOLEAN DEFAULT true,
  is_spot_trading_allowed BOOLEAN DEFAULT true,
  status TEXT DEFAULT 'TRADING',
  last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(symbol, exchange)
);

-- Enable RLS
ALTER TABLE public.crypto_assets_registry ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Anyone can read crypto assets registry"
ON public.crypto_assets_registry FOR SELECT
USING (true);

CREATE POLICY "Service role can manage crypto assets registry"
ON public.crypto_assets_registry FOR ALL
USING (true)
WITH CHECK (true);

-- Create trade audit log table for complete trade lifecycle tracking
CREATE TABLE public.trade_audit_log (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  trade_id UUID NOT NULL,
  external_order_id TEXT,
  client_order_id TEXT,
  stage TEXT NOT NULL DEFAULT 'SIGNAL_GENERATED',
  exchange TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT DEFAULT 'MARKET',
  quantity NUMERIC NOT NULL,
  price NUMERIC,
  executed_qty NUMERIC,
  executed_price NUMERIC,
  commission NUMERIC,
  commission_asset TEXT,
  exchange_response JSONB,
  validation_status TEXT DEFAULT 'pending',
  validation_message TEXT,
  error_code TEXT,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.trade_audit_log ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Authenticated users can read trade audit log"
ON public.trade_audit_log FOR SELECT
USING (true);

CREATE POLICY "Service role can manage trade audit log"
ON public.trade_audit_log FOR ALL
USING (true)
WITH CHECK (true);

-- Create indexes for fast lookups
CREATE INDEX idx_crypto_assets_symbol ON public.crypto_assets_registry(symbol);
CREATE INDEX idx_crypto_assets_exchange ON public.crypto_assets_registry(exchange);
CREATE INDEX idx_crypto_assets_quote ON public.crypto_assets_registry(quote_asset);
CREATE INDEX idx_trade_audit_trade_id ON public.trade_audit_log(trade_id);
CREATE INDEX idx_trade_audit_external_order ON public.trade_audit_log(external_order_id);
CREATE INDEX idx_trade_audit_stage ON public.trade_audit_log(stage);
CREATE INDEX idx_trade_audit_validation ON public.trade_audit_log(validation_status);

-- Enable realtime for trade audit log
ALTER PUBLICATION supabase_realtime ADD TABLE public.trade_audit_log;