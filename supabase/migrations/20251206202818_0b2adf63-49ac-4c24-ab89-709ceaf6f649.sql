-- Add validation tracking columns to trading_executions
ALTER TABLE public.trading_executions 
ADD COLUMN IF NOT EXISTS is_forced_validation boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS validation_trace jsonb DEFAULT NULL;

-- Create index for forced validation queries
CREATE INDEX IF NOT EXISTS idx_trading_executions_forced_validation 
ON public.trading_executions(is_forced_validation) 
WHERE is_forced_validation = true;