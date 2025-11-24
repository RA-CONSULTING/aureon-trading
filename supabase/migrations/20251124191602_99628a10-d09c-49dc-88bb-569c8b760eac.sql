-- Initialize trading_config table with default configuration
INSERT INTO public.trading_config (
  id,
  is_enabled,
  trading_mode,
  base_position_size_usdt,
  max_position_size_usdt,
  stop_loss_percentage,
  take_profit_percentage,
  max_daily_loss_usdt,
  max_daily_trades,
  min_coherence,
  min_lighthouse_confidence,
  min_prism_level,
  require_lhe,
  position_size_mode,
  allowed_symbols
)
VALUES (
  gen_random_uuid(),
  false,
  'paper',
  100.0,
  1000.0,
  2.0,
  5.0,
  500.0,
  50,
  0.85,
  0.70,
  3,
  false,
  'fixed',
  ARRAY['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'XRPUSDT', 'DOTUSDT', 'UNIUSDT', 'SOLUSDT', 'MATICUSDT']
)
ON CONFLICT (id) DO NOTHING;