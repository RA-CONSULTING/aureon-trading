-- Add missing columns to qgita_signal_states table for enhanced QGITA signal persistence
ALTER TABLE public.qgita_signal_states 
ADD COLUMN IF NOT EXISTS tier integer DEFAULT 3,
ADD COLUMN IF NOT EXISTS curvature numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS curvature_direction text DEFAULT 'NEUTRAL',
ADD COLUMN IF NOT EXISTS ftcp_detected boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS golden_ratio_score numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS lighthouse_l numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_lhe boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS lighthouse_threshold numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS linear_coherence numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS nonlinear_coherence numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS cross_scale_coherence numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS anomaly_pointer numeric DEFAULT 0,
ADD COLUMN IF NOT EXISTS reasoning text DEFAULT '';