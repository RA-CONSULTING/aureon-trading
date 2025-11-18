-- Fix function search path security warning
DROP FUNCTION IF EXISTS public.update_sentinel_updated_at() CASCADE;

CREATE OR REPLACE FUNCTION public.update_sentinel_updated_at()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER update_sentinel_config_updated_at
  BEFORE UPDATE ON public.sentinel_config
  FOR EACH ROW
  EXECUTE FUNCTION public.update_sentinel_updated_at();