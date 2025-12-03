/**
 * Systems Integration Dashboard
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Displays real-time status of all Temporal Ladder systems
 * and their hive mind coherence.
 */

import React, { useEffect, useState } from 'react';
import { useSystemsIntegration, useTemporalLadder, useQueenHiveBrowser } from '../hooks/useSystemsIntegration';

const SystemStatusCard: React.FC<{
  name: string;
  active: boolean;
  health: number;
  icon: string;
}> = ({ name, active, health, icon }) => {
  const healthColor = health > 0.7 ? '#22c55e' : health > 0.4 ? '#eab308' : '#ef4444';
  const statusText = active ? 'ONLINE' : 'OFFLINE';
  const statusColor = active ? '#22c55e' : '#6b7280';

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span
          className="text-xs font-bold px-2 py-1 rounded"
          style={{ backgroundColor: statusColor, color: 'white' }}
        >
          {statusText}
        </span>
      </div>
      <h3 className="text-white font-semibold text-sm mb-2">{name}</h3>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-300"
          style={{
            width: `${health * 100}%`,
            backgroundColor: healthColor,
          }}
        />
      </div>
      <span className="text-xs text-gray-400 mt-1 block">
        Health: {(health * 100).toFixed(0)}%
      </span>
    </div>
  );
};

const SYSTEM_ICONS: Record<string, string> = {
  'harmonic-nexus': '🌌',
  'master-equation': '📐',
  'earth-integration': '🌍',
  'nexus-feed': '📡',
  'quantum-quackers': '🦆',
  'akashic-mapper': '📜',
  'zero-point': '⚡',
  'dimensional-dialler': '🎛️',
};

const SYSTEM_DISPLAY_NAMES: Record<string, string> = {
  'harmonic-nexus': 'Harmonic Nexus Core',
  'master-equation': 'Master Equation',
  'earth-integration': 'Earth Integration',
  'nexus-feed': 'Nexus Live Feed',
  'quantum-quackers': 'Quantum Quackers',
  'akashic-mapper': 'Akashic Mapper',
  'zero-point': 'Zero Point Detector',
  'dimensional-dialler': 'Dimensional Dialler',
};

export const SystemsIntegrationDashboard: React.FC = () => {
  const { state, isInitialized, refreshAkashic } = useSystemsIntegration();
  const { systemStatuses, hiveMindCoherence } = useTemporalLadder();
  const { state: queenState, step: queenStep, simulate, reset } = useQueenHiveBrowser();

  const [autoSimulate, setAutoSimulate] = useState(false);

  useEffect(() => {
    let interval: number | null = null;
    if (autoSimulate) {
      interval = window.setInterval(() => {
        queenStep();
      }, 500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoSimulate, queenStep]);

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-white text-lg">🌌 Initializing Hive Mind...</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-900 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">
          🌌 Temporal Ladder - Hive Mind Integration
        </h1>
        <p className="text-gray-400">
          Prime Sentinel: GARY LECKEY 02111991
        </p>
      </div>

      {/* Hive Mind Coherence */}
      <div className="mb-8 bg-gray-800 rounded-xl p-6 border border-purple-500/30">
        <h2 className="text-xl font-bold text-white mb-4">
          🧠 Hive Mind Coherence
        </h2>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="w-full bg-gray-700 rounded-full h-4">
              <div
                className="h-4 rounded-full transition-all duration-500"
                style={{
                  width: `${hiveMindCoherence * 100}%`,
                  background: `linear-gradient(90deg, #8b5cf6, #06b6d4)`,
                }}
              />
            </div>
          </div>
          <span className="text-2xl font-bold text-white">
            {(hiveMindCoherence * 100).toFixed(1)}%
          </span>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div className="text-gray-400">
            Active Systems: <span className="text-white font-bold">{state?.systemsActive || 0}</span>/{state?.systemsTotal || 8}
          </div>
          <div className="text-gray-400">
            Integration Health: <span className="text-white font-bold">{((state?.integrationHealth || 0) * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* System Grid */}
      <div className="mb-8">
        <h2 className="text-xl font-bold text-white mb-4">
          📡 System Status
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {systemStatuses.map((system) => (
            <SystemStatusCard
              key={system.name}
              name={SYSTEM_DISPLAY_NAMES[system.name] || system.name}
              active={system.active}
              health={system.health}
              icon={SYSTEM_ICONS[system.name] || '⚙️'}
            />
          ))}
        </div>
      </div>

      {/* Akashic Attunement */}
      {state?.akashic && (
        <div className="mb-8 bg-gray-800 rounded-xl p-6 border border-amber-500/30">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">
              📜 Akashic Attunement
            </h2>
            <button
              onClick={() => refreshAkashic(7)}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-semibold transition"
            >
              Refresh Attunement
            </button>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-amber-400">
                {state.akashic.finalFrequency.toFixed(4)} Hz
              </div>
              <div className="text-gray-400 text-sm">Final Frequency</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-400">
                {(state.akashic.convergenceRate * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Convergence Rate</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-cyan-400">
                {(state.akashic.stabilityIndex * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Stability Index</div>
            </div>
          </div>
        </div>
      )}

      {/* Zero Point Field */}
      {state?.zeroPoint && (
        <div className="mb-8 bg-gray-800 rounded-xl p-6 border border-blue-500/30">
          <h2 className="text-xl font-bold text-white mb-4">
            ⚡ Zero Point Field
          </h2>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-400">
                {(state.zeroPoint.zeroPointCoherence * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Coherence</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-400">
                {(state.zeroPoint.phaseLockStrength * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Phase Lock</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-400">
                {(state.zeroPoint.cavityResonance * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Cavity Resonance</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-amber-400">
                {state.zeroPoint.activeSeal?.name || 'None'}
              </div>
              <div className="text-gray-400 text-sm">Active Seal</div>
            </div>
          </div>
        </div>
      )}

      {/* Dimensional Dialler */}
      {state?.dimensional && (
        <div className="mb-8 bg-gray-800 rounded-xl p-6 border border-green-500/30">
          <h2 className="text-xl font-bold text-white mb-4">
            🎛️ Dimensional Dialler
          </h2>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-400">
                {(state.dimensional.stability.overall * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Overall Stability</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-400">
                {(state.dimensional.stability.primeAlignment * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Prime Alignment</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-400">
                {(state.dimensional.stability.schumannHold * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Schumann Hold</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-cyan-400">
                {(state.dimensional.temporalSync * 100).toFixed(1)}%
              </div>
              <div className="text-gray-400 text-sm">Temporal Sync</div>
            </div>
          </div>
        </div>
      )}

      {/* Queen Hive */}
      {queenState && (
        <div className="mb-8 bg-gray-800 rounded-xl p-6 border border-yellow-500/30">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">
              👑 Queen Hive - 10-9-1 Model
            </h2>
            <div className="flex gap-2">
              <button
                onClick={queenStep}
                className="px-4 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg text-sm font-semibold transition"
              >
                Step
              </button>
              <button
                onClick={() => simulate(10)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-semibold transition"
              >
                +10 Steps
              </button>
              <button
                onClick={() => setAutoSimulate(!autoSimulate)}
                className={`px-4 py-2 ${autoSimulate ? 'bg-red-600 hover:bg-red-500' : 'bg-green-600 hover:bg-green-500'} text-white rounded-lg text-sm font-semibold transition`}
              >
                {autoSimulate ? 'Stop' : 'Auto'}
              </button>
              <button
                onClick={reset}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg text-sm font-semibold transition"
              >
                Reset
              </button>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4 text-center mb-4">
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-400">
                {queenState.totalHives}
              </div>
              <div className="text-gray-400 text-sm">Total Hives</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-400">
                £{queenState.totalEquity.toFixed(2)}
              </div>
              <div className="text-gray-400 text-sm">Total Equity</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-400">
                {queenState.totalAgents}
              </div>
              <div className="text-gray-400 text-sm">Total Agents</div>
            </div>
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-400">
                G{queenState.generation}
              </div>
              <div className="text-gray-400 text-sm">Generation</div>
            </div>
          </div>
          {queenState.hives.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-gray-300">
                <thead className="text-xs text-gray-400 uppercase bg-gray-700/50">
                  <tr>
                    <th className="px-4 py-2">Hive</th>
                    <th className="px-4 py-2">Gen</th>
                    <th className="px-4 py-2">Agents</th>
                    <th className="px-4 py-2">Equity</th>
                    <th className="px-4 py-2">Stage</th>
                    <th className="px-4 py-2">Multiplier</th>
                  </tr>
                </thead>
                <tbody>
                  {queenState.hives.slice(0, 10).map((hive) => (
                    <tr key={hive.id} className="border-b border-gray-700">
                      <td className="px-4 py-2 font-medium text-white">{hive.id}</td>
                      <td className="px-4 py-2">{hive.generation}</td>
                      <td className="px-4 py-2">{hive.agents}</td>
                      <td className="px-4 py-2">£{hive.equity.toFixed(2)}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          hive.stage === 'dominant' ? 'bg-green-600' :
                          hive.stage === 'thriving' ? 'bg-blue-600' :
                          hive.stage === 'growing' ? 'bg-cyan-600' :
                          hive.stage === 'recovering' ? 'bg-yellow-600' :
                          'bg-red-600'
                        }`}>
                          {hive.stage}
                        </span>
                      </td>
                      <td className="px-4 py-2">{hive.profitMultiplier.toFixed(2)}×</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SystemsIntegrationDashboard;
