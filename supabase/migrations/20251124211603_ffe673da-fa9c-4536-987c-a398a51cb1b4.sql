-- Enable realtime for War Room tables
ALTER PUBLICATION supabase_realtime ADD TABLE lighthouse_events;
ALTER PUBLICATION supabase_realtime ADD TABLE trading_executions;
ALTER PUBLICATION supabase_realtime ADD TABLE trading_positions;
ALTER PUBLICATION supabase_realtime ADD TABLE trading_signals;
ALTER PUBLICATION supabase_realtime ADD TABLE oms_order_queue;