-- Update lighthouse_events table to align with ablation study (remove metric_cphi)
-- The ablation study uses 4 metrics: Clin, Cnonlin, Geff, Q (not Cphi)

ALTER TABLE lighthouse_events DROP COLUMN IF EXISTS metric_cphi;