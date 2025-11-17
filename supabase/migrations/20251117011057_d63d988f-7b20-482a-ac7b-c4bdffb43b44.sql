-- Add symbol column to coherence_history for multi-asset tracking
ALTER TABLE public.coherence_history 
ADD COLUMN IF NOT EXISTS symbol TEXT NOT NULL DEFAULT 'BTCUSDT';

-- Create index for symbol-based queries
CREATE INDEX IF NOT EXISTS idx_coherence_history_symbol ON public.coherence_history(symbol);

-- Create composite index for symbol + time queries
CREATE INDEX IF NOT EXISTS idx_coherence_history_symbol_timestamp 
ON public.coherence_history(symbol, timestamp DESC);

-- Add comment
COMMENT ON COLUMN public.coherence_history.symbol IS 'Trading pair symbol (e.g., BTCUSDT, ETHUSDT)';
