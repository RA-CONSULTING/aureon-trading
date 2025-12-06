-- 1. 6D Harmonic Waveform States
CREATE TABLE public.harmonic_6d_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  d1_price JSONB NOT NULL DEFAULT '{}',
  d2_volume JSONB NOT NULL DEFAULT '{}',
  d3_time JSONB NOT NULL DEFAULT '{}',
  d4_correlation JSONB NOT NULL DEFAULT '{}',
  d5_momentum JSONB NOT NULL DEFAULT '{}',
  d6_frequency JSONB NOT NULL DEFAULT '{}',
  dimensional_coherence NUMERIC NOT NULL DEFAULT 0,
  phase_alignment NUMERIC NOT NULL DEFAULT 0,
  energy_density NUMERIC NOT NULL DEFAULT 0,
  resonance_score NUMERIC NOT NULL DEFAULT 0,
  wave_state TEXT NOT NULL DEFAULT 'FORMING',
  market_phase TEXT NOT NULL DEFAULT 'ACCUMULATION',
  harmonic_lock BOOLEAN DEFAULT false,
  probability_field NUMERIC NOT NULL DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Probability Matrix States
CREATE TABLE public.probability_matrix_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  six_d_probability NUMERIC NOT NULL DEFAULT 0,
  hnc_probability NUMERIC NOT NULL DEFAULT 0,
  fused_probability NUMERIC NOT NULL DEFAULT 0,
  dynamic_weight NUMERIC NOT NULL DEFAULT 0.5,
  trading_action TEXT NOT NULL DEFAULT 'HOLD',
  confidence NUMERIC NOT NULL DEFAULT 0,
  wave_state TEXT DEFAULT 'FORMING',
  harmonic_lock BOOLEAN DEFAULT false,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Integral AQAL States
CREATE TABLE public.integral_aqal_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  upper_left NUMERIC NOT NULL DEFAULT 0,
  upper_right NUMERIC NOT NULL DEFAULT 0,
  lower_left NUMERIC NOT NULL DEFAULT 0,
  lower_right NUMERIC NOT NULL DEFAULT 0,
  quadrant_balance NUMERIC NOT NULL DEFAULT 0,
  dominant_quadrant TEXT NOT NULL DEFAULT 'UPPER_RIGHT',
  integration_level NUMERIC NOT NULL DEFAULT 0,
  spiral_stage TEXT NOT NULL DEFAULT 'ORANGE',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. FTCP Detector States
CREATE TABLE public.ftcp_detector_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  curvature NUMERIC NOT NULL DEFAULT 0,
  curvature_direction TEXT NOT NULL DEFAULT 'FLAT',
  is_fibonacci_level BOOLEAN DEFAULT false,
  nearest_fib_ratio NUMERIC,
  divergence_from_fib NUMERIC,
  trend_strength NUMERIC NOT NULL DEFAULT 0,
  phase TEXT NOT NULL DEFAULT 'NEUTRAL',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. QGITA Signal States  
CREATE TABLE public.qgita_signal_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  signal_type TEXT NOT NULL DEFAULT 'HOLD',
  strength NUMERIC NOT NULL DEFAULT 0,
  confidence NUMERIC NOT NULL DEFAULT 0,
  coherence_boost NUMERIC NOT NULL DEFAULT 0,
  phase TEXT NOT NULL DEFAULT 'NEUTRAL',
  frequency NUMERIC NOT NULL DEFAULT 528,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. HNC Imperial Detection States
CREATE TABLE public.hnc_detection_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  is_lighthouse_detected BOOLEAN DEFAULT false,
  schumann_power NUMERIC DEFAULT 0,
  anchor_power NUMERIC DEFAULT 0,
  love_power NUMERIC DEFAULT 0,
  unity_power NUMERIC DEFAULT 0,
  distortion_power NUMERIC DEFAULT 0,
  imperial_yield NUMERIC NOT NULL DEFAULT 0,
  harmonic_fidelity NUMERIC NOT NULL DEFAULT 0,
  bridge_status TEXT NOT NULL DEFAULT 'CLOSED',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 7. Smart Order Router States
CREATE TABLE public.smart_router_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  selected_exchange TEXT NOT NULL DEFAULT 'binance',
  binance_fee NUMERIC DEFAULT 0.001,
  kraken_fee NUMERIC DEFAULT 0.0026,
  fee_savings NUMERIC DEFAULT 0,
  routing_reason TEXT NOT NULL DEFAULT 'DEFAULT',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 8. Decision Fusion States
CREATE TABLE public.decision_fusion_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  final_action TEXT NOT NULL DEFAULT 'HOLD',
  position_size NUMERIC NOT NULL DEFAULT 0,
  confidence NUMERIC NOT NULL DEFAULT 0,
  ensemble_score NUMERIC NOT NULL DEFAULT 0,
  sentiment_score NUMERIC NOT NULL DEFAULT 0,
  qgita_boost NUMERIC NOT NULL DEFAULT 0,
  harmonic_6d_score NUMERIC NOT NULL DEFAULT 0,
  wave_state TEXT DEFAULT 'FORMING',
  harmonic_lock BOOLEAN DEFAULT false,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 9. Full Ecosystem Snapshots
CREATE TABLE public.ecosystem_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  systems_online INTEGER NOT NULL DEFAULT 0,
  total_systems INTEGER NOT NULL DEFAULT 25,
  hive_mind_coherence NUMERIC NOT NULL DEFAULT 0,
  bus_consensus TEXT NOT NULL DEFAULT 'HOLD',
  bus_confidence NUMERIC NOT NULL DEFAULT 0,
  json_enhancements_loaded BOOLEAN DEFAULT false,
  system_states JSONB NOT NULL DEFAULT '{}',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 10. Temporal Anchor States
CREATE TABLE public.temporal_anchor_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  is_valid BOOLEAN DEFAULT true,
  drift_detected BOOLEAN DEFAULT false,
  drift_amount_ms NUMERIC DEFAULT 0,
  registered_systems INTEGER NOT NULL DEFAULT 0,
  verified_systems INTEGER NOT NULL DEFAULT 0,
  anchor_strength NUMERIC NOT NULL DEFAULT 1,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS on all tables
ALTER TABLE public.harmonic_6d_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.probability_matrix_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.integral_aqal_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ftcp_detector_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.qgita_signal_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hnc_detection_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.smart_router_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.decision_fusion_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ecosystem_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.temporal_anchor_states ENABLE ROW LEVEL SECURITY;

-- RLS Policies for authenticated users to read
CREATE POLICY "Authenticated users can read harmonic_6d_states" ON public.harmonic_6d_states FOR SELECT USING (true);
CREATE POLICY "Service can insert harmonic_6d_states" ON public.harmonic_6d_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read probability_matrix_states" ON public.probability_matrix_states FOR SELECT USING (true);
CREATE POLICY "Service can insert probability_matrix_states" ON public.probability_matrix_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read integral_aqal_states" ON public.integral_aqal_states FOR SELECT USING (true);
CREATE POLICY "Service can insert integral_aqal_states" ON public.integral_aqal_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read ftcp_detector_states" ON public.ftcp_detector_states FOR SELECT USING (true);
CREATE POLICY "Service can insert ftcp_detector_states" ON public.ftcp_detector_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read qgita_signal_states" ON public.qgita_signal_states FOR SELECT USING (true);
CREATE POLICY "Service can insert qgita_signal_states" ON public.qgita_signal_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read hnc_detection_states" ON public.hnc_detection_states FOR SELECT USING (true);
CREATE POLICY "Service can insert hnc_detection_states" ON public.hnc_detection_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read smart_router_states" ON public.smart_router_states FOR SELECT USING (true);
CREATE POLICY "Service can insert smart_router_states" ON public.smart_router_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read decision_fusion_states" ON public.decision_fusion_states FOR SELECT USING (true);
CREATE POLICY "Service can insert decision_fusion_states" ON public.decision_fusion_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read ecosystem_snapshots" ON public.ecosystem_snapshots FOR SELECT USING (true);
CREATE POLICY "Service can insert ecosystem_snapshots" ON public.ecosystem_snapshots FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read temporal_anchor_states" ON public.temporal_anchor_states FOR SELECT USING (true);
CREATE POLICY "Service can insert temporal_anchor_states" ON public.temporal_anchor_states FOR INSERT WITH CHECK (true);

-- Enable realtime for key tables
ALTER PUBLICATION supabase_realtime ADD TABLE public.harmonic_6d_states;
ALTER PUBLICATION supabase_realtime ADD TABLE public.probability_matrix_states;
ALTER PUBLICATION supabase_realtime ADD TABLE public.decision_fusion_states;
ALTER PUBLICATION supabase_realtime ADD TABLE public.ecosystem_snapshots;