-- Create brain_states table to store AUREON Brain cognitive output
CREATE TABLE public.brain_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  
  -- Market Data
  fear_greed INTEGER DEFAULT 50,
  fear_greed_class TEXT DEFAULT 'Neutral',
  btc_price NUMERIC DEFAULT 0,
  btc_dominance NUMERIC DEFAULT 0,
  btc_change_24h NUMERIC DEFAULT 0,
  
  -- Skeptical Analysis
  manipulation_probability NUMERIC DEFAULT 0,
  red_flags TEXT[] DEFAULT '{}',
  green_flags TEXT[] DEFAULT '{}',
  
  -- Truth Council
  council_consensus TEXT DEFAULT 'UNKNOWN',
  council_action TEXT DEFAULT 'HOLD',
  truth_score NUMERIC DEFAULT 0.5,
  spoof_score NUMERIC DEFAULT 0.5,
  council_arguments TEXT[] DEFAULT '{}',
  
  -- Brain Synthesis
  brain_directive TEXT,
  learning_directive TEXT DEFAULT 'NEUTRAL',
  
  -- Prediction
  prediction_direction TEXT DEFAULT 'NEUTRAL',
  prediction_confidence NUMERIC DEFAULT 0,
  
  -- Accuracy (Self-Learning)
  overall_accuracy NUMERIC DEFAULT 0,
  total_predictions INTEGER DEFAULT 0,
  bullish_accuracy NUMERIC DEFAULT 0,
  bearish_accuracy NUMERIC DEFAULT 0,
  self_critique TEXT[] DEFAULT '{}',
  
  -- Speculations
  speculations TEXT[] DEFAULT '{}',
  
  -- Wisdom Consensus (7 civilizations)
  wisdom_consensus JSONB DEFAULT '{}',
  
  -- Sandbox Evolution
  evolved_generation INTEGER DEFAULT 0,
  evolved_win_rate NUMERIC DEFAULT 0,
  
  -- Full state payload
  full_state JSONB DEFAULT '{}',
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.brain_states ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read brain states (public live feed)
CREATE POLICY "Anyone can read brain states"
ON public.brain_states
FOR SELECT
USING (true);

-- Service can insert brain states
CREATE POLICY "Service can insert brain states"
ON public.brain_states
FOR INSERT
WITH CHECK (true);

-- Create index for efficient queries
CREATE INDEX idx_brain_states_user_timestamp ON public.brain_states(user_id, timestamp DESC);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.brain_states;