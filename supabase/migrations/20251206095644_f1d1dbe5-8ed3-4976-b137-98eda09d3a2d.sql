-- 1. Omega Equation States
CREATE TABLE omega_equation_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  omega NUMERIC NOT NULL DEFAULT 0,
  psi NUMERIC NOT NULL DEFAULT 0,
  love NUMERIC NOT NULL DEFAULT 0,
  observer NUMERIC NOT NULL DEFAULT 0,
  lambda NUMERIC NOT NULL DEFAULT 0,
  substrate NUMERIC NOT NULL DEFAULT 0,
  echo NUMERIC NOT NULL DEFAULT 0,
  coherence NUMERIC NOT NULL DEFAULT 0,
  theta NUMERIC NOT NULL DEFAULT 0,
  unity NUMERIC NOT NULL DEFAULT 0,
  dominant_node TEXT NOT NULL DEFAULT 'Tiger',
  spiral_phase NUMERIC NOT NULL DEFAULT 0,
  fibonacci_level INTEGER NOT NULL DEFAULT 0,
  celestial_boost NUMERIC DEFAULT 0,
  schumann_boost NUMERIC DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Unity Event States
CREATE TABLE unity_event_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  theta NUMERIC NOT NULL DEFAULT 0,
  coherence NUMERIC NOT NULL DEFAULT 0,
  omega NUMERIC NOT NULL DEFAULT 0,
  unity NUMERIC NOT NULL DEFAULT 0,
  duration_ms INTEGER NOT NULL DEFAULT 0,
  is_peak BOOLEAN DEFAULT false,
  event_type TEXT NOT NULL DEFAULT 'forming',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Eckoushic Cascade States
CREATE TABLE eckoushic_cascade_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  eckoushic NUMERIC NOT NULL DEFAULT 0,
  akashic NUMERIC NOT NULL DEFAULT 0,
  harmonic_nexus NUMERIC NOT NULL DEFAULT 0,
  heart_wave NUMERIC NOT NULL DEFAULT 0,
  frequency NUMERIC NOT NULL DEFAULT 528,
  cascade_level INTEGER NOT NULL DEFAULT 1,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Akashic Attunement States
CREATE TABLE akashic_attunement_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  final_frequency NUMERIC NOT NULL DEFAULT 528,
  convergence_rate NUMERIC NOT NULL DEFAULT 0,
  stability_index NUMERIC NOT NULL DEFAULT 0,
  cycles_performed INTEGER NOT NULL DEFAULT 0,
  attunement_quality TEXT NOT NULL DEFAULT 'MODERATE',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Stargate Harmonizer States
CREATE TABLE stargate_harmonizer_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  dominant_frequency NUMERIC NOT NULL DEFAULT 528,
  coherence_boost NUMERIC NOT NULL DEFAULT 0,
  signal_amplification NUMERIC NOT NULL DEFAULT 1,
  trading_bias TEXT NOT NULL DEFAULT 'NEUTRAL',
  confidence_modifier NUMERIC NOT NULL DEFAULT 0,
  optimal_entry_window BOOLEAN DEFAULT false,
  resonance_quality NUMERIC NOT NULL DEFAULT 0,
  harmonics JSONB DEFAULT '[]',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. Planetary Modulation States (Song of Spheres)
CREATE TABLE planetary_modulation_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  harmonic_weight_modulation JSONB NOT NULL DEFAULT '{}',
  color_palette_shift NUMERIC NOT NULL DEFAULT 0,
  coherence_nudge NUMERIC NOT NULL DEFAULT 0,
  phase_bias JSONB NOT NULL DEFAULT '{}',
  planetary_states JSONB NOT NULL DEFAULT '[]',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 7. Performance Tracker States
CREATE TABLE performance_tracker_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  realized_pnl NUMERIC NOT NULL DEFAULT 0,
  unrealized_pnl NUMERIC NOT NULL DEFAULT 0,
  total_trades INTEGER NOT NULL DEFAULT 0,
  wins INTEGER NOT NULL DEFAULT 0,
  sharpe NUMERIC NOT NULL DEFAULT 0,
  max_drawdown NUMERIC NOT NULL DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 8. Risk Manager States
CREATE TABLE risk_manager_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  temporal_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),
  equity NUMERIC NOT NULL DEFAULT 0,
  max_drawdown NUMERIC NOT NULL DEFAULT 0,
  open_positions_count INTEGER NOT NULL DEFAULT 0,
  open_positions JSONB DEFAULT '[]',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS on all tables
ALTER TABLE omega_equation_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE unity_event_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE eckoushic_cascade_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE akashic_attunement_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE stargate_harmonizer_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE planetary_modulation_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_tracker_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_manager_states ENABLE ROW LEVEL SECURITY;

-- RLS policies for authenticated users to read
CREATE POLICY "Authenticated users can read omega_equation_states" ON omega_equation_states FOR SELECT USING (true);
CREATE POLICY "Service can insert omega_equation_states" ON omega_equation_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read unity_event_states" ON unity_event_states FOR SELECT USING (true);
CREATE POLICY "Service can insert unity_event_states" ON unity_event_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read eckoushic_cascade_states" ON eckoushic_cascade_states FOR SELECT USING (true);
CREATE POLICY "Service can insert eckoushic_cascade_states" ON eckoushic_cascade_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read akashic_attunement_states" ON akashic_attunement_states FOR SELECT USING (true);
CREATE POLICY "Service can insert akashic_attunement_states" ON akashic_attunement_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read stargate_harmonizer_states" ON stargate_harmonizer_states FOR SELECT USING (true);
CREATE POLICY "Service can insert stargate_harmonizer_states" ON stargate_harmonizer_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read planetary_modulation_states" ON planetary_modulation_states FOR SELECT USING (true);
CREATE POLICY "Service can insert planetary_modulation_states" ON planetary_modulation_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read performance_tracker_states" ON performance_tracker_states FOR SELECT USING (true);
CREATE POLICY "Service can insert performance_tracker_states" ON performance_tracker_states FOR INSERT WITH CHECK (true);

CREATE POLICY "Authenticated users can read risk_manager_states" ON risk_manager_states FOR SELECT USING (true);
CREATE POLICY "Service can insert risk_manager_states" ON risk_manager_states FOR INSERT WITH CHECK (true);

-- Enable realtime for key tables
ALTER PUBLICATION supabase_realtime ADD TABLE omega_equation_states;
ALTER PUBLICATION supabase_realtime ADD TABLE unity_event_states;
ALTER PUBLICATION supabase_realtime ADD TABLE eckoushic_cascade_states;
ALTER PUBLICATION supabase_realtime ADD TABLE performance_tracker_states;