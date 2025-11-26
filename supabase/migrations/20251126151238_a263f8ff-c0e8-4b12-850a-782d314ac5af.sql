-- Switch to PAPER trading mode for safe demo
UPDATE public.trading_config
SET trading_mode = 'paper'
WHERE id IS NOT NULL;