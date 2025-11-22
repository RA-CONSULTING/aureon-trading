-- OMS Order Queue Tables
CREATE TABLE public.oms_order_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES public.hive_sessions(id) ON DELETE CASCADE,
  hive_id UUID NOT NULL REFERENCES public.hive_instances(id) ON DELETE CASCADE,
  agent_id UUID NOT NULL REFERENCES public.hive_agents(id) ON DELETE CASCADE,
  
  -- Order details
  symbol TEXT NOT NULL,
  side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
  quantity NUMERIC NOT NULL CHECK (quantity > 0),
  price NUMERIC NOT NULL CHECK (price > 0),
  order_type TEXT NOT NULL DEFAULT 'LIMIT' CHECK (order_type IN ('LIMIT', 'MARKET')),
  
  -- Priority and metadata
  priority INTEGER NOT NULL DEFAULT 50 CHECK (priority >= 0 AND priority <= 100),
  signal_strength NUMERIC,
  coherence NUMERIC,
  lighthouse_value NUMERIC,
  
  -- Status tracking
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'executed', 'failed', 'cancelled')),
  queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  executed_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  
  -- Execution results
  exchange_order_id TEXT,
  executed_price NUMERIC,
  executed_quantity NUMERIC,
  error_message TEXT,
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rate limit tracking per 10-second window
CREATE TABLE public.oms_rate_limit_windows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  window_start TIMESTAMPTZ NOT NULL,
  window_end TIMESTAMPTZ NOT NULL,
  orders_executed INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(window_start)
);

-- Execution metrics
CREATE TABLE public.oms_execution_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  -- Queue stats
  queue_depth INTEGER NOT NULL,
  avg_wait_time_ms INTEGER,
  
  -- Rate limit stats
  current_window_orders INTEGER NOT NULL,
  rate_limit_utilization NUMERIC NOT NULL,
  
  -- Execution stats
  orders_executed_last_minute INTEGER NOT NULL,
  orders_failed_last_minute INTEGER NOT NULL,
  avg_execution_latency_ms INTEGER,
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_oms_queue_status_priority ON public.oms_order_queue(status, priority DESC, queued_at ASC);
CREATE INDEX idx_oms_queue_session ON public.oms_order_queue(session_id);
CREATE INDEX idx_oms_queue_agent ON public.oms_order_queue(agent_id);
CREATE INDEX idx_oms_rate_windows ON public.oms_rate_limit_windows(window_start DESC);
CREATE INDEX idx_oms_metrics_timestamp ON public.oms_execution_metrics(timestamp DESC);

-- RLS Policies
ALTER TABLE public.oms_order_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.oms_rate_limit_windows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.oms_execution_metrics ENABLE ROW LEVEL SECURITY;

-- Users can view their own orders
CREATE POLICY "Users view own orders"
  ON public.oms_order_queue
  FOR SELECT
  USING (session_id IN (
    SELECT id FROM public.hive_sessions WHERE user_id = auth.uid()
  ));

-- Service manages orders
CREATE POLICY "Service manages orders"
  ON public.oms_order_queue
  FOR ALL
  USING (true);

-- Service manages rate limits
CREATE POLICY "Service manages rate limits"
  ON public.oms_rate_limit_windows
  FOR ALL
  USING (true);

-- Users can view metrics
CREATE POLICY "Users view metrics"
  ON public.oms_execution_metrics
  FOR SELECT
  USING (true);

-- Service manages metrics
CREATE POLICY "Service manages metrics"
  ON public.oms_execution_metrics
  FOR ALL
  USING (true);