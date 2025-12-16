-- Add unique constraint on transaction_id for upsert to work
ALTER TABLE public.trade_records 
ADD CONSTRAINT trade_records_transaction_id_unique UNIQUE (transaction_id);