-- Allow authenticated users to insert their own trading signals
DROP POLICY IF EXISTS "Service role can insert trading signals" ON public.trading_signals;

CREATE POLICY "Authenticated users can insert trading signals"
ON public.trading_signals
FOR INSERT
TO authenticated
WITH CHECK (true);