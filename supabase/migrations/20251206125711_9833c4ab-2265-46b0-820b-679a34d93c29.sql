-- Add unique constraint on symbol for elephant_memory upsert operations
ALTER TABLE public.elephant_memory 
ADD CONSTRAINT elephant_memory_symbol_unique UNIQUE (symbol);