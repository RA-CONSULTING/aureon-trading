-- Add user_id column to trading_positions for user isolation
ALTER TABLE public.trading_positions 
ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_trading_positions_user_id ON public.trading_positions(user_id);

-- Drop the overly permissive SELECT policy
DROP POLICY IF EXISTS "Authenticated users can read positions" ON public.trading_positions;

-- Create user-specific SELECT policy
CREATE POLICY "Users can view own positions"
ON public.trading_positions
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Update INSERT policy to require user_id match
DROP POLICY IF EXISTS "Service role can insert positions" ON public.trading_positions;

CREATE POLICY "Service role can insert positions"
ON public.trading_positions
FOR INSERT
TO service_role
WITH CHECK (true);

-- Update UPDATE policy to be service role only
DROP POLICY IF EXISTS "Service role can update positions" ON public.trading_positions;

CREATE POLICY "Service role can update positions"
ON public.trading_positions
FOR UPDATE
TO service_role
USING (true);