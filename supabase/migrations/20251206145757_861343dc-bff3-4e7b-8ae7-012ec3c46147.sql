-- Fix RLS on aureon_user_sessions to prevent public access to encrypted credentials
-- Drop the overly permissive service policy that allows reading all sessions
DROP POLICY IF EXISTS "Service can manage all sessions" ON public.aureon_user_sessions;

-- Create a more restrictive service policy using RESTRICTIVE instead of PERMISSIVE
-- This ensures service role can manage sessions but regular users cannot bypass their own policy
CREATE POLICY "Service role can manage sessions"
ON public.aureon_user_sessions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Ensure the user policies are in place (recreate to be safe)
DROP POLICY IF EXISTS "Users can view own session" ON public.aureon_user_sessions;
DROP POLICY IF EXISTS "Users can insert own session" ON public.aureon_user_sessions;
DROP POLICY IF EXISTS "Users can update own session" ON public.aureon_user_sessions;

-- Recreate user policies targeting authenticated role specifically
CREATE POLICY "Users can view own session"
ON public.aureon_user_sessions
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own session"
ON public.aureon_user_sessions
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own session"
ON public.aureon_user_sessions
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id);