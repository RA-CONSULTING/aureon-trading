// ElephantMemory Database Sync
// Persists elephant memory to Supabase elephant_memory table

import { supabase } from '@/integrations/supabase/client';
import type { SymbolMemory } from './elephantMemory';

/**
 * Load all elephant memory records from database
 */
export async function loadFromDatabase(): Promise<Record<string, SymbolMemory>> {
  try {
    const { data, error } = await supabase
      .from('elephant_memory')
      .select('*');

    if (error) {
      console.warn('[ElephantMemoryDB] Failed to load from database:', error);
      return {};
    }

    const memories: Record<string, SymbolMemory> = {};
    
    for (const row of data || []) {
      memories[row.symbol] = {
        symbol: row.symbol,
        trades: row.trades || 0,
        wins: row.wins || 0,
        losses: row.losses || 0,
        profit: Number(row.profit) || 0,
        lastTrade: row.last_trade ? new Date(row.last_trade).getTime() : null,
        lossStreak: row.loss_streak || 0,
        blacklisted: row.blacklisted || false,
        cooldownUntil: row.cooldown_until ? new Date(row.cooldown_until).getTime() : null,
      };
    }

    console.log(`[ElephantMemoryDB] Loaded ${Object.keys(memories).length} symbols from database`);
    return memories;
  } catch (e) {
    console.error('[ElephantMemoryDB] Error loading from database:', e);
    return {};
  }
}

/**
 * Save a single symbol memory to database (upsert)
 */
export async function saveToDatabase(memory: SymbolMemory): Promise<void> {
  try {
    const { error } = await supabase
      .from('elephant_memory')
      .upsert({
        symbol: memory.symbol,
        trades: memory.trades,
        wins: memory.wins,
        losses: memory.losses,
        profit: memory.profit,
        last_trade: memory.lastTrade ? new Date(memory.lastTrade).toISOString() : null,
        loss_streak: memory.lossStreak,
        blacklisted: memory.blacklisted,
        cooldown_until: memory.cooldownUntil ? new Date(memory.cooldownUntil).toISOString() : null,
        updated_at: new Date().toISOString(),
      }, {
        onConflict: 'symbol',
      });

    if (error) {
      console.warn('[ElephantMemoryDB] Failed to save to database:', error);
    }
  } catch (e) {
    console.error('[ElephantMemoryDB] Error saving to database:', e);
  }
}

/**
 * Sync all memories to database (batch upsert)
 */
export async function syncAllToDatabase(memories: Record<string, SymbolMemory>): Promise<void> {
  try {
    const records = Object.values(memories).map(memory => ({
      symbol: memory.symbol,
      trades: memory.trades,
      wins: memory.wins,
      losses: memory.losses,
      profit: memory.profit,
      last_trade: memory.lastTrade ? new Date(memory.lastTrade).toISOString() : null,
      loss_streak: memory.lossStreak,
      blacklisted: memory.blacklisted,
      cooldown_until: memory.cooldownUntil ? new Date(memory.cooldownUntil).toISOString() : null,
      updated_at: new Date().toISOString(),
    }));

    if (records.length === 0) return;

    const { error } = await supabase
      .from('elephant_memory')
      .upsert(records, {
        onConflict: 'symbol',
      });

    if (error) {
      console.warn('[ElephantMemoryDB] Failed to sync all to database:', error);
    } else {
      console.log(`[ElephantMemoryDB] Synced ${records.length} symbols to database`);
    }
  } catch (e) {
    console.error('[ElephantMemoryDB] Error syncing to database:', e);
  }
}