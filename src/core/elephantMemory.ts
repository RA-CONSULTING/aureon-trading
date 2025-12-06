// ElephantMemory - The elephant never forgets
// Trade persistence, cooldowns, and loss streak tracking
// Browser-safe implementation using localStorage + Supabase sync

import { unifiedBus, type SignalType } from './unifiedBus';
import { loadFromDatabase, saveToDatabase, syncAllToDatabase } from './elephantMemoryDB';

export interface SymbolMemory {
  symbol: string;
  trades: number;
  wins: number;
  losses: number;
  profit: number;
  lastTrade: number | null;
  lossStreak: number;
  blacklisted: boolean;
  cooldownUntil: number | null;
}

export interface ElephantState {
  memories: Record<string, SymbolMemory>;
  overallWinRate: number;
  totalTrades: number;
  totalProfit: number;
  blacklistedSymbols: string[];
  cooldownSymbols: string[];
}

const STORAGE_KEY = 'aureon_elephant_memory';
const DEFAULT_COOLDOWN_MS = 15 * 60 * 1000; // 15 minutes
const LOSS_STREAK_LIMIT = 3;

class ElephantMemory {
  private memories: Map<string, SymbolMemory> = new Map();
  private cooldownMs: number = DEFAULT_COOLDOWN_MS;
  private lossStreakLimit: number = LOSS_STREAK_LIMIT;
  private dbInitialized: boolean = false;
  
  constructor() {
    this.loadFromStorage();
    this.publishState();
    // Load from database async (will merge with localStorage)
    this.initFromDatabase();
  }
  
  /**
   * Initialize from database (async, called after constructor)
   */
  private async initFromDatabase(): Promise<void> {
    try {
      const dbMemories = await loadFromDatabase();
      
      // Merge database memories with local (database takes precedence for conflicts)
      Object.entries(dbMemories).forEach(([symbol, memory]) => {
        const local = this.memories.get(symbol);
        // If DB has more trades, it's more recent - use it
        if (!local || memory.trades > local.trades) {
          this.memories.set(symbol, memory);
        }
      });
      
      this.dbInitialized = true;
      this.saveToStorage(); // Sync merged state back to localStorage
      this.publishState();
      console.log('[ElephantMemory] Initialized from database');
    } catch (e) {
      console.warn('[ElephantMemory] Failed to init from database:', e);
    }
  }
  
  /**
   * Record a trade result
   */
  recordTrade(symbol: string, profit: number, side: 'BUY' | 'SELL'): void {
    const memory = this.getOrCreate(symbol);
    
    memory.trades += 1;
    memory.profit += profit;
    memory.lastTrade = Date.now();
    
    if (profit > 0) {
      memory.wins += 1;
      memory.lossStreak = 0;
    } else if (profit < 0) {
      memory.losses += 1;
      memory.lossStreak += 1;
      
      // Check for blacklist
      if (memory.lossStreak >= this.lossStreakLimit) {
        memory.blacklisted = true;
        console.warn(`[ElephantMemory] ${symbol} blacklisted after ${memory.lossStreak} consecutive losses`);
      }
    }
    
    // Set cooldown
    memory.cooldownUntil = Date.now() + this.cooldownMs;
    
    this.memories.set(symbol, memory);
    this.saveToStorage();
    this.publishState();
    
    // Persist to database
    saveToDatabase(memory);
  }
  
  /**
   * Check if a symbol should be avoided
   */
  shouldAvoid(symbol: string): { avoid: boolean; reason: string | null } {
    const memory = this.memories.get(symbol);
    
    if (!memory) {
      return { avoid: false, reason: null };
    }
    
    // Check blacklist
    if (memory.blacklisted) {
      return { avoid: true, reason: `Blacklisted (${memory.lossStreak} consecutive losses)` };
    }
    
    // Check cooldown
    if (memory.cooldownUntil && Date.now() < memory.cooldownUntil) {
      const remaining = Math.ceil((memory.cooldownUntil - Date.now()) / 1000 / 60);
      return { avoid: true, reason: `Cooldown (${remaining}m remaining)` };
    }
    
    return { avoid: false, reason: null };
  }
  
  /**
   * Get overall win rate
   */
  getOverallWinRate(): number {
    let totalWins = 0;
    let totalTrades = 0;
    
    this.memories.forEach(memory => {
      totalWins += memory.wins;
      totalTrades += memory.trades;
    });
    
    return totalTrades > 0 ? totalWins / totalTrades : 0;
  }
  
  /**
   * Get symbol statistics
   */
  getSymbolStats(symbol: string): SymbolMemory | null {
    return this.memories.get(symbol) ?? null;
  }
  
  /**
   * Get all blacklisted symbols
   */
  getBlacklistedSymbols(): string[] {
    const blacklisted: string[] = [];
    this.memories.forEach((memory, symbol) => {
      if (memory.blacklisted) {
        blacklisted.push(symbol);
      }
    });
    return blacklisted;
  }
  
  /**
   * Get all symbols on cooldown
   */
  getCooldownSymbols(): string[] {
    const now = Date.now();
    const cooldown: string[] = [];
    this.memories.forEach((memory, symbol) => {
      if (memory.cooldownUntil && now < memory.cooldownUntil) {
        cooldown.push(symbol);
      }
    });
    return cooldown;
  }
  
  /**
   * Remove a symbol from blacklist
   */
  unblacklist(symbol: string): void {
    const memory = this.memories.get(symbol);
    if (memory) {
      memory.blacklisted = false;
      memory.lossStreak = 0;
      this.memories.set(symbol, memory);
      this.saveToStorage();
      this.publishState();
      
      // Persist to database
      saveToDatabase(memory);
    }
  }
  
  /**
   * Get full state
   */
  getState(): ElephantState {
    const memories: Record<string, SymbolMemory> = {};
    let totalTrades = 0;
    let totalProfit = 0;
    
    this.memories.forEach((memory, symbol) => {
      memories[symbol] = memory;
      totalTrades += memory.trades;
      totalProfit += memory.profit;
    });
    
    return {
      memories,
      overallWinRate: this.getOverallWinRate(),
      totalTrades,
      totalProfit,
      blacklistedSymbols: this.getBlacklistedSymbols(),
      cooldownSymbols: this.getCooldownSymbols(),
    };
  }
  
  /**
   * Publish state to UnifiedBus
   */
  private publishState(): void {
    const state = this.getState();
    const winRate = state.overallWinRate;
    
    // Determine signal based on win rate
    let signal: SignalType = 'NEUTRAL';
    if (winRate > 0.6) signal = 'BUY';
    else if (winRate < 0.4 && state.totalTrades > 10) signal = 'SELL';
    
    unifiedBus.publish({
      systemName: 'ElephantMemory',
      timestamp: Date.now(),
      ready: true,
      coherence: winRate,
      confidence: Math.min(state.totalTrades / 100, 1), // Confidence grows with trades
      signal,
      data: {
        totalTrades: state.totalTrades,
        totalProfit: state.totalProfit,
        winRate,
        blacklistedCount: state.blacklistedSymbols.length,
        cooldownCount: state.cooldownSymbols.length,
      },
    });
  }
  
  /**
   * Get or create a symbol memory
   */
  private getOrCreate(symbol: string): SymbolMemory {
    let memory = this.memories.get(symbol);
    if (!memory) {
      memory = {
        symbol,
        trades: 0,
        wins: 0,
        losses: 0,
        profit: 0,
        lastTrade: null,
        lossStreak: 0,
        blacklisted: false,
        cooldownUntil: null,
      };
      this.memories.set(symbol, memory);
    }
    return memory;
  }
  
  /**
   * Load from localStorage
   */
  private loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored) as Record<string, SymbolMemory>;
        Object.entries(data).forEach(([symbol, memory]) => {
          this.memories.set(symbol, memory);
        });
      }
    } catch (e) {
      console.warn('[ElephantMemory] Failed to load from storage:', e);
    }
  }
  
  /**
   * Save to localStorage
   */
  private saveToStorage(): void {
    try {
      const data: Record<string, SymbolMemory> = {};
      this.memories.forEach((memory, symbol) => {
        data[symbol] = memory;
      });
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
      console.warn('[ElephantMemory] Failed to save to storage:', e);
    }
  }
  
  /**
   * Clear all memories (for testing)
   */
  clear(): void {
    this.memories.clear();
    localStorage.removeItem(STORAGE_KEY);
    this.publishState();
  }
  
  /**
   * Force sync all memories to database
   */
  async syncToDatabase(): Promise<void> {
    const memories: Record<string, SymbolMemory> = {};
    this.memories.forEach((memory, symbol) => {
      memories[symbol] = memory;
    });
    await syncAllToDatabase(memories);
  }
}

// Singleton instance
export const elephantMemory = new ElephantMemory();
