-- Create price_alerts table
CREATE TABLE public.price_alerts (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  symbol TEXT NOT NULL,
  alert_type TEXT NOT NULL CHECK (alert_type IN ('price_above', 'price_below', 'change_percent_above', 'change_percent_below')),
  target_value NUMERIC NOT NULL,
  current_value NUMERIC,
  is_active BOOLEAN NOT NULL DEFAULT true,
  is_triggered BOOLEAN NOT NULL DEFAULT false,
  triggered_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  notes TEXT
);

-- Enable Row Level Security
ALTER TABLE public.price_alerts ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (no auth required for this demo)
CREATE POLICY "Allow public read access to price alerts"
ON public.price_alerts
FOR SELECT
USING (true);

CREATE POLICY "Allow public insert to price alerts"
ON public.price_alerts
FOR INSERT
WITH CHECK (true);

CREATE POLICY "Allow public update to price alerts"
ON public.price_alerts
FOR UPDATE
USING (true);

CREATE POLICY "Allow public delete to price alerts"
ON public.price_alerts
FOR DELETE
USING (true);

-- Create index for faster queries
CREATE INDEX idx_price_alerts_symbol ON public.price_alerts(symbol);
CREATE INDEX idx_price_alerts_active ON public.price_alerts(is_active, is_triggered);