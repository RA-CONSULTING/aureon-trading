-- Add multi-exchange credential columns to aureon_user_sessions
ALTER TABLE public.aureon_user_sessions
ADD COLUMN IF NOT EXISTS kraken_api_key_encrypted text,
ADD COLUMN IF NOT EXISTS kraken_api_secret_encrypted text,
ADD COLUMN IF NOT EXISTS kraken_iv text,
ADD COLUMN IF NOT EXISTS alpaca_api_key_encrypted text,
ADD COLUMN IF NOT EXISTS alpaca_secret_key_encrypted text,
ADD COLUMN IF NOT EXISTS alpaca_iv text,
ADD COLUMN IF NOT EXISTS capital_api_key_encrypted text,
ADD COLUMN IF NOT EXISTS capital_password_encrypted text,
ADD COLUMN IF NOT EXISTS capital_identifier_encrypted text,
ADD COLUMN IF NOT EXISTS capital_iv text;