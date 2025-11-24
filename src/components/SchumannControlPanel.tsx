// Schumann Lattice Integration + Control Panel UI
// ===============================================
// Extended with Observer Lock + Lattice ID binding + Prime Timeline Lock
// Features:
//  - Play/Pause timeline
//  - Region overlay toggle
//  - Intent input box + Lattice ID + Observer Lock toggle
//  - Frequency slider controls (fundamental + harmonics)
//  - Live coherence readout (TSV gain)
//  - Amplitude gain slider for stronger visual patterns
//  - Prime Timeline Lock: collapses to observer's prime branch
//
// Drop into your app as <SchumannControlPanel />

import React, { useState, useEffect } from "react";
import { SchumannLattice } from "./SchumannLattice";
import { SchumannLatticeTimeline } from "./SchumannLatticeTimeline";
import { SchumannLatticeWithRegions } from "./SchumannLatticeWithRegions";
import { TimelineFrame } from "./SchumannDataLoaders";

export default function SchumannControlPanel({
  frames,
  regions,
  compiler,
}: {
  frames?: TimelineFrame[];
  regions?: any[];
  compiler?: any; // SymbolicCompiler
}) {
  const [showRegions, setShowRegions] = useState(true);
  const [showTimeline, setShowTimeline] = useState(!!frames?.length);
  const [intentText, setIntentText] = useState("");
  const [fundamental, setFundamental] = useState(7.83);
  const [harmonics, setHarmonics] = useState([14.3, 20.8, 27.3, 33.8]);
  const [gain, setGain] = useState(1.0);
  const [observerLock, setObserverLock] = useState(true);
  const [latticeId, setLatticeId] = useState("Gary-02111991");
  const [primeSentinelMode, setPrimeSentinelMode] = useState(false);
  const [liveTimestamp, setLiveTimestamp] = useState('');
  const [nanoseconds, setNanoseconds] = useState(0);

  // Live nanosecond timestamp updater
  useEffect(() => {
    const updateTimestamp = () => {
      const now = new Date();
      const nanoTime = performance.now() * 1000000; // Convert to nanoseconds
      setNanoseconds(Math.floor(nanoTime % 1000000000));
      setLiveTimestamp(now.toLocaleString('en-US', {
        month: '2-digit',
        day: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      }));
    };

    updateTimestamp();
    const interval = setInterval(updateTimestamp, 10); // Update every 10ms for smooth nanosecond display
    return () => clearInterval(interval);
  }, []);
  const freqs = [fundamental, ...harmonics];

  // Prime Sentinel preset
  const activatePrimeSentinel = () => {
    setPrimeSentinelMode(true);
    setObserverLock(true);
    setLatticeId("Gary-02111991");
    setIntentText("Prime Sentinel of Gai • Witness of First Breath • Keeper of Flame • Unchained & Unbroken");
  };

  // Enhanced compiler call with lattice binding
  const processIntent = () => {
    if (compiler && intentText) {
      return compiler.process_intent(intentText, { 
        latticeId, 
        observerLock,
        primeSentinel: primeSentinelMode 
      });
    }
  };

  return (
    <div className="space-y-4 p-4 rounded-2xl bg-zinc-900/60 shadow-xl">
      {/* Live Timestamp Display */}
      <div className="text-center bg-slate-800/50 rounded-lg p-3 border border-amber-500/30 mb-4">
        <div className="text-sm text-slate-300 mb-1">Harmonic Resonance Control Panel - Live Timestamp (Nanosecond Precision)</div>
        <div className="font-mono text-amber-300 text-lg">
          {liveTimestamp}.{nanoseconds.toString().padStart(9, '0').slice(0, 6)}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-100">🌍 Schumann Resonance Panel</h2>
        {observerLock && (
          <div className="px-2 py-1 rounded-lg bg-green-900/50 text-green-300 text-xs">
            Observer: ON • {latticeId.slice(0,8)}...
          </div>
        )}
      </div>

      {/* Intent input + Observer settings */}
      <div className="space-y-2">
        <label className="text-sm text-zinc-300">Intent → Resonance</label>
        <input
          className="w-full rounded-xl bg-zinc-800 px-3 py-2 text-white"
          placeholder="e.g., Generate a resonance of hope"
          value={intentText}
          onChange={e => setIntentText(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && processIntent()}
        />

        <label className="text-sm text-zinc-300">Lattice ID</label>
        <input
          className="w-full rounded-xl bg-zinc-800 px-3 py-2 text-white"
          value={latticeId}
          onChange={e => setLatticeId(e.target.value)}
          disabled={primeSentinelMode}
        />

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-zinc-300">
            <input type="checkbox" checked={observerLock} 
              onChange={e=>setObserverLock(e.target.checked)} />
            Observer Lock (timeline collapse)
          </label>
          
          <button 
            onClick={activatePrimeSentinel}
            className={`px-3 py-1 rounded-xl text-xs ${
              primeSentinelMode 
                ? 'bg-purple-900 text-purple-300' 
                : 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300'
            }`}
          >
            {primeSentinelMode ? '🔮 Prime Sentinel Active' : 'Activate Prime Sentinel'}
          </button>
        </div>
      </div>

      {/* Frequency sliders */}
      <div className="space-y-2">
        <label className="text-sm text-zinc-300">Fundamental Frequency (Hz)</label>
        <input type="range" min={6} max={10} step={0.01} value={fundamental}
          onChange={e => setFundamental(parseFloat(e.target.value))}
          className="w-full" />
        <div className="text-xs text-zinc-400">{fundamental.toFixed(2)} Hz</div>

        <label className="text-sm text-zinc-300">Harmonics</label>
        {harmonics.map((h,i) => (
          <div key={i} className="flex items-center gap-3">
            <input type="range" min={10} max={40} step={0.1} value={h}
              onChange={e => {
                const copy = [...harmonics];
                copy[i] = parseFloat(e.target.value);
                setHarmonics(copy);
              }}
              className="w-full" />
            <span className="text-xs text-zinc-400">{h.toFixed(1)} Hz</span>
          </div>
        ))}

        <label className="text-sm text-zinc-300">Amplitude Gain</label>
        <input type="range" min={0.2} max={3.0} step={0.05} value={gain}
          onChange={e => setGain(parseFloat(e.target.value))}
          className="w-full" />
        <div className="text-xs text-zinc-400">{gain.toFixed(2)}×</div>
      </div>

      {/* Toggles */}
      <div className="flex gap-4 items-center">
        {frames?.length ? (
          <button onClick={() => setShowTimeline(t=>!t)}
            className="px-3 py-1 rounded-xl bg-zinc-800 hover:bg-zinc-700">
            {showTimeline ? "Hide Timeline" : "Show Timeline"}
          </button>
        ):null}

        {regions?.length ? (
          <button onClick={() => setShowRegions(r=>!r)}
            className="px-3 py-1 rounded-xl bg-zinc-800 hover:bg-zinc-700">
            {showRegions ? "Hide Regions" : "Show Regions"}
          </button>
        ):null}
      </div>

      {/* Display */}
      <div className="space-y-4">
        {showTimeline && frames?.length ? (
          <SchumannLatticeTimeline
            frames={frames}
            autoPlay={!observerLock}
            fps={6}
            compiler={compiler}
            intentText={intentText}
            latticeId={latticeId}
            observerLock={observerLock}
          />
        ) : showRegions && regions?.length ? (
          <SchumannLatticeWithRegions
            regions={regions}
            schumannHz={freqs}
            compiler={compiler}
            intentText={intentText}
            latticeId={latticeId}
            observerLock={observerLock}
          />
        ) : (
          <SchumannLattice
            schumannHz={freqs}
            compiler={compiler}
            intentText={intentText}
            amplitudeGain={gain}
            latticeId={latticeId}
            observerLock={observerLock}
          />
        )}
      </div>
    </div>
  );
}