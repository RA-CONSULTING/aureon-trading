-- =====================================================
-- AUREON Security Fix: Authentication & RLS Policies
-- =====================================================

-- 1. Create app_role enum for user roles
CREATE TYPE public.app_role AS ENUM ('admin', 'user');

-- 2. Create user_roles table (separate from profiles to prevent privilege escalation)
CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role public.app_role NOT NULL DEFAULT 'user',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, role)
);

-- Enable RLS on user_roles
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- 3. Create security definer function to check roles (prevents RLS recursion)
CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role public.app_role)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.user_roles
    WHERE user_id = _user_id AND role = _role
  );
$$;

-- 4. Create profiles table for user data
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  full_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 5. DROP all existing public RLS policies
DROP POLICY IF EXISTS "Allow public read access to backtest results" ON public.backtest_results;
DROP POLICY IF EXISTS "Allow public insert to backtest results" ON public.backtest_results;
DROP POLICY IF EXISTS "Allow public read access to coherence history" ON public.coherence_history;
DROP POLICY IF EXISTS "Allow public insert to coherence history" ON public.coherence_history;
DROP POLICY IF EXISTS "Allow public read access to consciousness history" ON public.consciousness_field_history;
DROP POLICY IF EXISTS "Allow public insert to consciousness history" ON public.consciousness_field_history;
DROP POLICY IF EXISTS "Allow public read access to harmonic nexus states" ON public.harmonic_nexus_states;
DROP POLICY IF EXISTS "Allow public insert to harmonic nexus states" ON public.harmonic_nexus_states;
DROP POLICY IF EXISTS "Allow public read access to lighthouse events" ON public.lighthouse_events;
DROP POLICY IF EXISTS "Allow public insert to lighthouse events" ON public.lighthouse_events;
DROP POLICY IF EXISTS "Allow public read access to monte carlo simulations" ON public.monte_carlo_simulations;
DROP POLICY IF EXISTS "Allow public insert to monte carlo simulations" ON public.monte_carlo_simulations;
DROP POLICY IF EXISTS "Allow public read access to price alerts" ON public.price_alerts;
DROP POLICY IF EXISTS "Allow public insert to price alerts" ON public.price_alerts;
DROP POLICY IF EXISTS "Allow public update to price alerts" ON public.price_alerts;
DROP POLICY IF EXISTS "Allow public delete to price alerts" ON public.price_alerts;
DROP POLICY IF EXISTS "Allow public read access to sentinel config" ON public.sentinel_config;
DROP POLICY IF EXISTS "Allow public read access to solar flare correlations" ON public.solar_flare_correlations;
DROP POLICY IF EXISTS "Allow public insert to solar flare correlations" ON public.solar_flare_correlations;
DROP POLICY IF EXISTS "Allow public update to solar flare correlations" ON public.solar_flare_correlations;
DROP POLICY IF EXISTS "Allow public read access to stargate network states" ON public.stargate_network_states;
DROP POLICY IF EXISTS "Allow public insert to stargate network states" ON public.stargate_network_states;
DROP POLICY IF EXISTS "Allow public read trading config" ON public.trading_config;
DROP POLICY IF EXISTS "Allow public insert trading config" ON public.trading_config;
DROP POLICY IF EXISTS "Allow public update trading config" ON public.trading_config;
DROP POLICY IF EXISTS "Allow public read executions" ON public.trading_executions;
DROP POLICY IF EXISTS "Allow public insert executions" ON public.trading_executions;
DROP POLICY IF EXISTS "Allow public read positions" ON public.trading_positions;
DROP POLICY IF EXISTS "Allow public insert positions" ON public.trading_positions;
DROP POLICY IF EXISTS "Allow public update positions" ON public.trading_positions;
DROP POLICY IF EXISTS "Allow public read access to trading signals" ON public.trading_signals;
DROP POLICY IF EXISTS "Allow public insert to trading signals" ON public.trading_signals;

-- 6. Create SECURE RLS policies for all tables

-- Profiles: Users can read all, only update their own
CREATE POLICY "Users can view all profiles" ON public.profiles FOR SELECT TO authenticated USING (true);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE TO authenticated USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT TO authenticated WITH CHECK (auth.uid() = id);

-- User roles: Only admins can manage, users can read their own
CREATE POLICY "Users can view own roles" ON public.user_roles FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "Admins can manage all roles" ON public.user_roles FOR ALL TO authenticated USING (public.has_role(auth.uid(), 'admin'));

-- Trading Config: Admin-only access
CREATE POLICY "Admins can read trading config" ON public.trading_config FOR SELECT TO authenticated USING (public.has_role(auth.uid(), 'admin'));
CREATE POLICY "Admins can update trading config" ON public.trading_config FOR UPDATE TO authenticated USING (public.has_role(auth.uid(), 'admin'));
CREATE POLICY "Admins can insert trading config" ON public.trading_config FOR INSERT TO authenticated WITH CHECK (public.has_role(auth.uid(), 'admin'));

-- Sentinel Config: Admin-only access (contains personal data)
CREATE POLICY "Admins can read sentinel config" ON public.sentinel_config FOR SELECT TO authenticated USING (public.has_role(auth.uid(), 'admin'));

-- Trading Positions: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read positions" ON public.trading_positions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert positions" ON public.trading_positions FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update positions" ON public.trading_positions FOR UPDATE TO service_role USING (true);

-- Trading Executions: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read executions" ON public.trading_executions FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert executions" ON public.trading_executions FOR INSERT TO service_role WITH CHECK (true);

-- Trading Signals: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read trading signals" ON public.trading_signals FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert trading signals" ON public.trading_signals FOR INSERT TO service_role WITH CHECK (true);

-- Lighthouse Events: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read lighthouse events" ON public.lighthouse_events FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert lighthouse events" ON public.lighthouse_events FOR INSERT TO service_role WITH CHECK (true);

-- Harmonic Nexus States: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read harmonic states" ON public.harmonic_nexus_states FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert harmonic states" ON public.harmonic_nexus_states FOR INSERT TO service_role WITH CHECK (true);

-- Stargate Network States: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read stargate states" ON public.stargate_network_states FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert stargate states" ON public.stargate_network_states FOR INSERT TO service_role WITH CHECK (true);

-- Coherence History: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read coherence history" ON public.coherence_history FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert coherence history" ON public.coherence_history FOR INSERT TO service_role WITH CHECK (true);

-- Consciousness Field History: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read consciousness history" ON public.consciousness_field_history FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert consciousness history" ON public.consciousness_field_history FOR INSERT TO service_role WITH CHECK (true);

-- Backtest Results: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read backtest results" ON public.backtest_results FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert backtest results" ON public.backtest_results FOR INSERT TO service_role WITH CHECK (true);

-- Monte Carlo Simulations: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read monte carlo" ON public.monte_carlo_simulations FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert monte carlo" ON public.monte_carlo_simulations FOR INSERT TO service_role WITH CHECK (true);

-- Solar Flare Correlations: Authenticated users can read, service role can write
CREATE POLICY "Authenticated users can read solar correlations" ON public.solar_flare_correlations FOR SELECT TO authenticated USING (true);
CREATE POLICY "Service role can insert solar correlations" ON public.solar_flare_correlations FOR INSERT TO service_role WITH CHECK (true);
CREATE POLICY "Service role can update solar correlations" ON public.solar_flare_correlations FOR UPDATE TO service_role USING (true);

-- Price Alerts: Users can manage their own alerts (when we add user_id column later)
-- For now, authenticated users can manage all
CREATE POLICY "Authenticated users can read price alerts" ON public.price_alerts FOR SELECT TO authenticated USING (true);
CREATE POLICY "Authenticated users can insert price alerts" ON public.price_alerts FOR INSERT TO authenticated WITH CHECK (true);
CREATE POLICY "Authenticated users can update price alerts" ON public.price_alerts FOR UPDATE TO authenticated USING (true);
CREATE POLICY "Authenticated users can delete price alerts" ON public.price_alerts FOR DELETE TO authenticated USING (true);

-- 7. Create trigger to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
  
  -- Assign default 'user' role
  INSERT INTO public.user_roles (user_id, role)
  VALUES (NEW.id, 'user');
  
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- 8. Create function for updated_at trigger
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();