-- Create payment_transactions table to track SumUp payments
CREATE TABLE IF NOT EXISTS public.payment_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  amount NUMERIC NOT NULL,
  currency TEXT NOT NULL DEFAULT 'EUR',
  payment_provider TEXT NOT NULL DEFAULT 'sumup',
  payment_status TEXT NOT NULL DEFAULT 'pending',
  payment_url TEXT,
  transaction_reference TEXT,
  paid_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable RLS
ALTER TABLE public.payment_transactions ENABLE ROW LEVEL SECURITY;

-- Users can view their own payment transactions
CREATE POLICY "Users can view own payments"
  ON public.payment_transactions
  FOR SELECT
  USING (auth.uid() = user_id);

-- Service role can insert payment transactions
CREATE POLICY "Service can insert payments"
  ON public.payment_transactions
  FOR INSERT
  WITH CHECK (true);

-- Service role can update payment transactions
CREATE POLICY "Service can update payments"
  ON public.payment_transactions
  FOR UPDATE
  USING (true);

-- Add payment_completed column to profiles table
ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS payment_completed BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS payment_completed_at TIMESTAMP WITH TIME ZONE;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id 
  ON public.payment_transactions(user_id);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_status 
  ON public.payment_transactions(payment_status);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_payment_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER payment_transactions_updated_at
  BEFORE UPDATE ON public.payment_transactions
  FOR EACH ROW
  EXECUTE FUNCTION update_payment_updated_at();