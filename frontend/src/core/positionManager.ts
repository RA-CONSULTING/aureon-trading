/**
 * Position Manager
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Tracks active positions with TP/SL and trailing stops
 * Like Python aureon_unified_ecosystem.py position management
 */

import { unifiedBus } from './unifiedBus';
import { temporalLadder, SYSTEMS } from './temporalLadder';
import { elephantMemory } from './elephantMemory';
import { trailingStopManager } from './trailingStopManager';
import { supabase } from '@/integrations/supabase/client';

export interface Position {
  id: string;
  symbol: string;
  exchange: string;
  side: 'LONG' | 'SHORT';
  entryPrice: number;
  quantity: number;
  positionSizeUsd: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
  takeProfitPrice: number;
  stopLossPrice: number;
  trailingStopActive: boolean;
  trailingStopPrice: number | null;
  entryTime: number;
  holdDurationMs: number;
  exchange_order_id?: string;
  coherenceAtEntry: number;
  qgitaTierAtEntry: number;
}

export interface PositionManagerState {
  positions: Position[];
  totalPositions: number;
  totalExposureUsd: number;
  totalUnrealizedPnl: number;
  maxPositions: number;
  positionsAtRisk: number; // Positions near stop loss
}

const MAX_POSITIONS = 15;
const DEFAULT_TP_PCT = 1.5;  // 1.5% take profit
const DEFAULT_SL_PCT = 0.8;  // 0.8% stop loss
const TRAILING_ACTIVATION_PCT = 0.5; // Activate trailing at 0.5% profit

class PositionManager {
  private positions: Map<string, Position> = new Map();
  private isInitialized: boolean = false;

  constructor() {
    temporalLadder.registerSystem(SYSTEMS.POSITION_MANAGER);
    console.log('📈 Position Manager initialized');
  }

  /**
   * Initialize and load existing positions from DB
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Load open positions from trading_positions table
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const { data, error } = await supabase
        .from('trading_positions')
        .select('*')
        .eq('user_id', session.user.id)
        .eq('status', 'open');

      if (!error && data) {
        for (const row of data) {
          const position: Position = {
            id: row.id,
            symbol: row.symbol,
            exchange: 'binance', // Default exchange
            side: row.side as 'LONG' | 'SHORT',
            entryPrice: row.entry_price,
            quantity: row.quantity,
            positionSizeUsd: row.position_value_usdt || row.entry_price * row.quantity,
            currentPrice: row.entry_price,
            unrealizedPnl: 0,
            unrealizedPnlPct: 0,
            takeProfitPrice: row.take_profit_price || row.entry_price * (1 + DEFAULT_TP_PCT / 100),
            stopLossPrice: row.stop_loss_price || row.entry_price * (1 - DEFAULT_SL_PCT / 100),
            trailingStopActive: false,
            trailingStopPrice: null,
            entryTime: new Date(row.opened_at).getTime(),
            holdDurationMs: Date.now() - new Date(row.opened_at).getTime(),
            coherenceAtEntry: 0,
            qgitaTierAtEntry: 3,
          };
          this.positions.set(position.id, position);
        }
        console.log(`[PositionManager] Loaded ${data.length} open positions`);
      }
    } catch (error) {
      console.error('[PositionManager] Init error:', error);
    }

    this.isInitialized = true;
  }

  /**
   * Open a new position
   */
  public async openPosition(params: {
    symbol: string;
    exchange: string;
    side: 'LONG' | 'SHORT';
    entryPrice: number;
    quantity: number;
    positionSizeUsd: number;
    coherenceAtEntry: number;
    qgitaTierAtEntry: number;
    exchangeOrderId?: string;
    takeProfitPct?: number;
    stopLossPct?: number;
  }): Promise<Position | null> {
    // Check max positions
    if (this.positions.size >= MAX_POSITIONS) {
      console.warn('[PositionManager] Max positions reached');
      return null;
    }

    // Check if already have position in this symbol
    for (const pos of this.positions.values()) {
      if (pos.symbol === params.symbol) {
        console.warn(`[PositionManager] Already have position in ${params.symbol}`);
        return null;
      }
    }

    const tpPct = params.takeProfitPct || DEFAULT_TP_PCT;
    const slPct = params.stopLossPct || DEFAULT_SL_PCT;

    const position: Position = {
      id: crypto.randomUUID(),
      symbol: params.symbol,
      exchange: params.exchange,
      side: params.side,
      entryPrice: params.entryPrice,
      quantity: params.quantity,
      positionSizeUsd: params.positionSizeUsd,
      currentPrice: params.entryPrice,
      unrealizedPnl: 0,
      unrealizedPnlPct: 0,
      takeProfitPrice: params.side === 'LONG' 
        ? params.entryPrice * (1 + tpPct / 100)
        : params.entryPrice * (1 - tpPct / 100),
      stopLossPrice: params.side === 'LONG'
        ? params.entryPrice * (1 - slPct / 100)
        : params.entryPrice * (1 + slPct / 100),
      trailingStopActive: false,
      trailingStopPrice: null,
      entryTime: Date.now(),
      holdDurationMs: 0,
      exchange_order_id: params.exchangeOrderId,
      coherenceAtEntry: params.coherenceAtEntry,
      qgitaTierAtEntry: params.qgitaTierAtEntry,
    };

    this.positions.set(position.id, position);

    // Create trailing stop in trailing stop manager
    trailingStopManager.createStop(params.symbol, params.entryPrice, params.entryPrice);

    // Persist to database
    await this.persistPosition(position);

    console.log(`[PositionManager] 📈 Opened ${params.side} ${params.symbol} @ ${params.entryPrice}`);

    this.publishToUnifiedBus();
    return position;
  }

  /**
   * Update position with new price
   */
  public updatePrice(symbol: string, currentPrice: number): Position | null {
    for (const position of this.positions.values()) {
      if (position.symbol !== symbol) continue;

      // Calculate unrealized P&L
      const priceDiff = position.side === 'LONG'
        ? currentPrice - position.entryPrice
        : position.entryPrice - currentPrice;

      position.currentPrice = currentPrice;
      position.unrealizedPnl = priceDiff * position.quantity;
      position.unrealizedPnlPct = (priceDiff / position.entryPrice) * 100;
      position.holdDurationMs = Date.now() - position.entryTime;

      // Check for trailing stop activation
      if (!position.trailingStopActive && position.unrealizedPnlPct >= TRAILING_ACTIVATION_PCT) {
        position.trailingStopActive = true;
        console.log(`[PositionManager] 🎯 Trailing stop activated for ${symbol} at ${position.unrealizedPnlPct.toFixed(2)}% profit`);
      }

      // Update trailing stop price
      if (position.trailingStopActive) {
        const trailingUpdate = trailingStopManager.updateStop(symbol, currentPrice);
        if (trailingUpdate.stop) {
          position.trailingStopPrice = trailingUpdate.stop.trailPrice;
          position.stopLossPrice = trailingUpdate.stop.trailPrice;
        }

        if (trailingUpdate.triggered) {
          console.log(`[PositionManager] ⚠️ Trailing stop triggered for ${symbol}`);
          return position;
        }
      }

      // Check take profit / stop loss
      if (this.shouldClose(position, currentPrice)) {
        return position;
      }

      return position;
    }
    return null;
  }

  /**
   * Check if position should be closed
   */
  private shouldClose(position: Position, currentPrice: number): boolean {
    if (position.side === 'LONG') {
      // Take profit hit
      if (currentPrice >= position.takeProfitPrice) {
        console.log(`[PositionManager] 🎯 TP HIT: ${position.symbol} @ ${currentPrice}`);
        return true;
      }
      // Stop loss hit
      if (currentPrice <= position.stopLossPrice) {
        console.log(`[PositionManager] 🛑 SL HIT: ${position.symbol} @ ${currentPrice}`);
        return true;
      }
    } else {
      // Short position - inverted
      if (currentPrice <= position.takeProfitPrice) {
        console.log(`[PositionManager] 🎯 TP HIT: ${position.symbol} @ ${currentPrice}`);
        return true;
      }
      if (currentPrice >= position.stopLossPrice) {
        console.log(`[PositionManager] 🛑 SL HIT: ${position.symbol} @ ${currentPrice}`);
        return true;
      }
    }
    return false;
  }

  /**
   * Close a position
   */
  public async closePosition(positionId: string, exitPrice: number, reason: string = 'manual'): Promise<Position | null> {
    const position = this.positions.get(positionId);
    if (!position) return null;

    // Calculate final P&L
    const priceDiff = position.side === 'LONG'
      ? exitPrice - position.entryPrice
      : position.entryPrice - exitPrice;

    const realizedPnl = priceDiff * position.quantity;
    const realizedPnlPct = (priceDiff / position.entryPrice) * 100;
    const isWin = realizedPnl > 0;

    // Update Elephant Memory
    elephantMemory.recordTrade(position.symbol, realizedPnl, position.side === 'LONG' ? 'BUY' : 'SELL');

    // Remove from active positions
    this.positions.delete(positionId);

    // Remove trailing stop
    trailingStopManager.removeStop(position.symbol);

    console.log(`[PositionManager] 📤 Closed ${position.side} ${position.symbol} @ ${exitPrice} | P&L: ${realizedPnlPct.toFixed(2)}% ($${realizedPnl.toFixed(2)}) | ${reason}`);

    // Update database
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        await supabase
          .from('trading_positions')
          .update({
            status: 'closed',
            exit_price: exitPrice,
            realized_pnl: realizedPnl,
            realized_pnl_pct: realizedPnlPct,
            close_reason: reason,
            closed_at: new Date().toISOString(),
          })
          .eq('id', positionId);
      }
    } catch (error) {
      console.error('[PositionManager] DB update error:', error);
    }

    this.publishToUnifiedBus();

    return { ...position, unrealizedPnl: realizedPnl, unrealizedPnlPct: realizedPnlPct };
  }

  /**
   * Check all positions for TP/SL exits
   * Returns positions that should be closed
   */
  public checkAllPositions(): Position[] {
    const toClose: Position[] = [];
    
    for (const position of this.positions.values()) {
      const updated = this.updatePrice(position.symbol, position.currentPrice);
      if (updated && this.shouldClose(updated, updated.currentPrice)) {
        toClose.push(updated);
      }
    }
    
    return toClose;
  }

  /**
   * Get all positions
   */
  public getPositions(): Position[] {
    return Array.from(this.positions.values());
  }

  /**
   * Get position by symbol
   */
  public getPosition(symbol: string): Position | undefined {
    for (const pos of this.positions.values()) {
      if (pos.symbol === symbol) return pos;
    }
    return undefined;
  }

  /**
   * Get position count
   */
  public getPositionCount(): number {
    return this.positions.size;
  }

  /**
   * Check if can open new position
   */
  public canOpenPosition(): boolean {
    return this.positions.size < MAX_POSITIONS;
  }

  /**
   * Get state
   */
  public getState(): PositionManagerState {
    const positions = this.getPositions();
    const totalExposureUsd = positions.reduce((sum, p) => sum + p.positionSizeUsd, 0);
    const totalUnrealizedPnl = positions.reduce((sum, p) => sum + p.unrealizedPnl, 0);
    const positionsAtRisk = positions.filter(p => p.unrealizedPnlPct < -0.5).length;

    return {
      positions,
      totalPositions: positions.length,
      totalExposureUsd,
      totalUnrealizedPnl,
      maxPositions: MAX_POSITIONS,
      positionsAtRisk,
    };
  }

  private async persistPosition(position: Position): Promise<void> {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      await supabase.from('trading_positions').insert({
        user_id: session.user.id,
        symbol: position.symbol,
        side: position.side,
        entry_price: position.entryPrice,
        quantity: position.quantity,
        position_value_usdt: position.positionSizeUsd,
        take_profit_price: position.takeProfitPrice,
        stop_loss_price: position.stopLossPrice,
        status: 'open',
      });
    } catch (error) {
      console.error('[PositionManager] Persist error:', error);
    }
  }

  private publishToUnifiedBus(): void {
    const state = this.getState();

    unifiedBus.publish({
      systemName: 'PositionManager',
      timestamp: Date.now(),
      ready: true,
      coherence: state.totalPositions > 0 ? 0.85 : 0.5,
      confidence: 0.9,
      signal: state.totalUnrealizedPnl > 0 ? 'BUY' : state.totalUnrealizedPnl < 0 ? 'SELL' : 'NEUTRAL',
      data: {
        totalPositions: state.totalPositions,
        maxPositions: state.maxPositions,
        canOpenNew: this.canOpenPosition(),
        totalExposureUsd: state.totalExposureUsd,
        totalUnrealizedPnl: state.totalUnrealizedPnl,
        positionsAtRisk: state.positionsAtRisk,
        symbols: state.positions.map(p => p.symbol),
      },
    });
  }
}

export const positionManager = new PositionManager();
