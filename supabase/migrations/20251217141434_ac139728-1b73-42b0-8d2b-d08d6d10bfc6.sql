-- Add pnl and is_win columns to trade_records for Python terminal sync
ALTER TABLE public.trade_records 
ADD COLUMN IF NOT EXISTS pnl numeric DEFAULT NULL,
ADD COLUMN IF NOT EXISTS is_win boolean DEFAULT NULL;