-- Add initialization vector column to user_binance_credentials table for AES-256-GCM encryption
ALTER TABLE public.user_binance_credentials
ADD COLUMN IF NOT EXISTS iv TEXT;