-- Create tables for TWAP order tracking
CREATE TABLE IF NOT EXISTS public.twap_orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  
  -- Order identification
  algo_id BIGINT,
  client_algo_id TEXT NOT NULL UNIQUE,
  
  -- Hunt/OMS linkage
  hunt_session_id UUID REFERENCES public.hunt_sessions(id),
  oms_order_id UUID REFERENCES public.oms_order_queue(id),
  
  -- Order details
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
  total_quantity NUMERIC NOT NULL,
  duration_seconds INTEGER NOT NULL CHECK (duration_seconds BETWEEN 300 AND 86400),
  limit_price NUMERIC,
  
  -- Execution tracking
  executed_quantity NUMERIC DEFAULT 0,
  executed_amount NUMERIC DEFAULT 0,
  avg_price NUMERIC,
  
  -- Status
  algo_status TEXT DEFAULT 'WORKING' CHECK (algo_status IN ('WORKING', 'FINISHED', 'CANCELLED', 'ERROR')),
  urgency TEXT DEFAULT 'LOW' CHECK (urgency IN ('LOW', 'MEDIUM', 'HIGH')),
  
  -- Timestamps
  book_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  
  -- Error handling
  error_code INTEGER,
  error_message TEXT,
  
  -- Metadata
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Create table for TWAP sub-orders
CREATE TABLE IF NOT EXISTS public.twap_sub_orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  
  twap_order_id UUID NOT NULL REFERENCES public.twap_orders(id) ON DELETE CASCADE,
  
  -- Sub-order details
  sub_id INTEGER NOT NULL,
  order_id BIGINT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  
  -- Execution
  order_status TEXT NOT NULL,
  executed_quantity NUMERIC NOT NULL DEFAULT 0,
  executed_amount NUMERIC NOT NULL DEFAULT 0,
  orig_quantity NUMERIC NOT NULL,
  avg_price NUMERIC,
  
  -- Fees
  fee_amount NUMERIC,
  fee_asset TEXT,
  
  -- Timestamps
  book_time TIMESTAMPTZ NOT NULL,
  
  -- Extra fields
  time_in_force TEXT,
  
  UNIQUE(twap_order_id, sub_id)
);

-- Enable RLS
ALTER TABLE public.twap_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.twap_sub_orders ENABLE ROW LEVEL SECURITY;

-- RLS Policies for twap_orders
CREATE POLICY "Service manages TWAP orders"
  ON public.twap_orders
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Users view own TWAP orders"
  ON public.twap_orders
  FOR SELECT
  TO authenticated
  USING (
    hunt_session_id IN (
      SELECT id FROM public.hunt_sessions WHERE user_id = auth.uid()
    )
  );

-- RLS Policies for twap_sub_orders
CREATE POLICY "Service manages TWAP sub-orders"
  ON public.twap_sub_orders
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Users view own TWAP sub-orders"
  ON public.twap_sub_orders
  FOR SELECT
  TO authenticated
  USING (
    twap_order_id IN (
      SELECT id FROM public.twap_orders 
      WHERE hunt_session_id IN (
        SELECT id FROM public.hunt_sessions WHERE user_id = auth.uid()
      )
    )
  );

-- Create indexes
CREATE INDEX idx_twap_orders_hunt_session ON public.twap_orders(hunt_session_id);
CREATE INDEX idx_twap_orders_algo_id ON public.twap_orders(algo_id);
CREATE INDEX idx_twap_orders_status ON public.twap_orders(algo_status);
CREATE INDEX idx_twap_sub_orders_twap_order ON public.twap_sub_orders(twap_order_id);

-- Create trigger for updated_at
CREATE TRIGGER update_twap_orders_updated_at
  BEFORE UPDATE ON public.twap_orders
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- Add TWAP threshold to hunt_sessions
ALTER TABLE public.hunt_sessions 
ADD COLUMN IF NOT EXISTS twap_threshold_usd NUMERIC DEFAULT 500,
ADD COLUMN IF NOT EXISTS twap_duration_seconds INTEGER DEFAULT 600;