import React, { useState } from 'react';
import type { StreamSource } from '@/services/websocketService';

interface TradeControlsProps {
  onExecuteTrade: (tradeDetails: { pair: string; side: 'LONG' | 'SHORT'; size: string; price: string }) => Promise<void> | void;
  isApiActive: boolean;
  onUnifiedConfigChange?: (config: UnifiedExecutionConfig) => void;
}

export interface UnifiedExecutionConfig {
  streamSource: StreamSource;
  streamSymbol: string;
  targetPrice: string;
  etaHourUtc: string;
  prepositionMinutes: string;
  validationMinutes: string;
  cooldownMinutes: string;
}

const TradeControls: React.FC<TradeControlsProps> = ({ onExecuteTrade, isApiActive, onUnifiedConfigChange }) => {
  const [pair, setPair] = useState('ETH/USD');
  const [side, setSide] = useState<'LONG' | 'SHORT'>('LONG');
  const [size, setSize] = useState('1.5');
  const [price, setPrice] = useState('3500.00');
  const [streamSource, setStreamSource] = useState<StreamSource>('nexus_command');
  const [streamSymbol, setStreamSymbol] = useState('ETHUSDT');
  const [targetPrice, setTargetPrice] = useState('3000');
  const [etaHourUtc, setEtaHourUtc] = useState('20:00');
  const [prepositionMinutes, setPrepositionMinutes] = useState('120');
  const [validationMinutes, setValidationMinutes] = useState('15');
  const [cooldownMinutes, setCooldownMinutes] = useState('15');

  const handleExecute = async () => {
    if (!pair || !size || !price) {
      alert('Please fill in all trade details.');
      return;
    }

    try {
      await onExecuteTrade({ pair, side, size, price });
    } catch (error) {
      console.error('Trade execution failed:', error);
      alert('Trade execution failed. Check console for details.');
    }
  };

  const emitUnifiedConfig = () => {
    const config: UnifiedExecutionConfig = {
      streamSource,
      streamSymbol,
      targetPrice,
      etaHourUtc,
      prepositionMinutes,
      validationMinutes,
      cooldownMinutes,
    };
    onUnifiedConfigChange?.(config);
  };

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg shadow-lg p-6 h-full flex flex-col">
      <div className="flex-grow">
          <h3 className="text-xl font-semibold text-gray-200 mb-1">Layer 5: Manual Trade Execution</h3>
          <p className="text-sm text-gray-400 mb-6">Execute manual orders. Requires active API key.</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="pair" className="block text-sm font-medium text-gray-400 mb-1">Pair</label>
              <input
                type="text"
                id="pair"
                value={pair}
                onChange={(e) => setPair(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label htmlFor="side" className="block text-sm font-medium text-gray-400 mb-1">Side</label>
              <select
                id="side"
                value={side}
                onChange={(e) => setSide(e.target.value as 'LONG' | 'SHORT')}
                className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                <option value="LONG">LONG</option>
                <option value="SHORT">SHORT</option>
              </select>
            </div>
            <div>
              <label htmlFor="size" className="block text-sm font-medium text-gray-400 mb-1">Size</label>
              <input
                type="number"
                id="size"
                step="0.01"
                value={size}
                onChange={(e) => setSize(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label htmlFor="price" className="block text-sm font-medium text-gray-400 mb-1">Price</label>
              <input
                type="number"
                id="price"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          <div className="mt-6 border-t border-gray-700 pt-4">
            <h4 className="text-sm font-semibold text-cyan-300 mb-1">Unified Pre-Positioning Form</h4>
            <p className="text-xs text-gray-400 mb-4">
              Configure live stream source + ETA/cooldown so bids can be staged before projected order-book swings.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="streamSource" className="block text-sm font-medium text-gray-400 mb-1">WebSocket Source</label>
                <select
                  id="streamSource"
                  value={streamSource}
                  onChange={(e) => setStreamSource(e.target.value as StreamSource)}
                  className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  <option value="nexus_command">Nexus Command Stream</option>
                  <option value="binance_orderbook">Binance Order Book (Depth)</option>
                </select>
              </div>
              <div>
                <label htmlFor="streamSymbol" className="block text-sm font-medium text-gray-400 mb-1">Stream Symbol</label>
                <input
                  type="text"
                  id="streamSymbol"
                  value={streamSymbol}
                  onChange={(e) => setStreamSymbol(e.target.value)}
                  placeholder="ETHUSDT"
                  className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              <div>
                <label htmlFor="targetPrice" className="block text-sm font-medium text-gray-400 mb-1">Target Bid Level</label>
                <input
                  type="number"
                  id="targetPrice"
                  step="0.01"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              <div>
                <label htmlFor="etaHourUtc" className="block text-sm font-medium text-gray-400 mb-1">Projected ETA (UTC)</label>
                <input
                  type="time"
                  id="etaHourUtc"
                  value={etaHourUtc}
                  onChange={(e) => setEtaHourUtc(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              <div>
                <label htmlFor="prepositionMinutes" className="block text-sm font-medium text-gray-400 mb-1">Pre-Position Lead (min)</label>
                <input
                  type="number"
                  id="prepositionMinutes"
                  value={prepositionMinutes}
                  onChange={(e) => setPrepositionMinutes(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              <div>
                <label htmlFor="validationMinutes" className="block text-sm font-medium text-gray-400 mb-1">Trajectory Validation (min)</label>
                <input
                  type="number"
                  id="validationMinutes"
                  value={validationMinutes}
                  onChange={(e) => setValidationMinutes(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
              <div>
                <label htmlFor="cooldownMinutes" className="block text-sm font-medium text-gray-400 mb-1">Cooldown (min)</label>
                <input
                  type="number"
                  id="cooldownMinutes"
                  value={cooldownMinutes}
                  onChange={(e) => setCooldownMinutes(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-600 rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                />
              </div>
            </div>
            <button
              type="button"
              onClick={emitUnifiedConfig}
              className="mt-4 w-full rounded-md border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-100 hover:bg-cyan-500/20"
            >
              Apply Unified Stream Plan
            </button>
          </div>
      </div>

      <button
        onClick={handleExecute}
        disabled={!isApiActive}
        className="mt-6 w-full font-bold py-3 px-8 rounded-lg shadow-lg transition-transform transform hover:scale-105 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-600 hover:to-indigo-700 disabled:bg-gray-600 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed disabled:transform-none disabled:scale-100"
      >
        {isApiActive ? 'EXECUTE TRADE' : 'API INACTIVE'}
      </button>
    </div>
  );
};

export default TradeControls;
