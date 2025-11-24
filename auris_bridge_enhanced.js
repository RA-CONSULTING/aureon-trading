// auris_bridge_enhanced.js — Enhanced WS bridge for Solar Harmonics + Lattice
const fs = require('fs');
const path = require('path');
const chokidar = require('chokidar');
const WebSocket = require('ws');

const PORT = process.env.PORT || 8787;
const FILES = {
  auris: path.resolve('validation/auris_metrics.csv'),
  aura: path.resolve('validation/aura_features.csv'),
  solar: path.resolve('validation/solar_harmonics.csv')
};

// Solar harmonics state
let solarChain = [];
let harmonicState = { isLive: false, activeFrequencies: [] };

function lastRow(fp) {
  if (!fs.existsSync(fp)) return null;
  const text = fs.readFileSync(fp, 'utf8').trim();
  const nl = text.lastIndexOf('\n');
  const header = text.slice(0, text.indexOf('\n')).split(',');
  const line = text.slice(nl + 1);
  const cols = line.split(',');
  if (cols.length !== header.length) return null;
  const obj = {};
  header.forEach((h, i) => { obj[h] = isNaN(+cols[i]) ? cols[i] : +cols[i]; });
  return obj;
}

const wss = new WebSocket.Server({ port: PORT }, () => {
  console.log(`[auris-bridge-enhanced] ws://localhost:${PORT}`);
});

function broadcast(type, data) {
  const msg = JSON.stringify({ type, data, timestamp: Date.now() });
  wss.clients.forEach(c => { if (c.readyState === 1) c.send(msg); });
}

function pushIfNew(kind, fp) {
  const row = lastRow(fp);
  if (!row) return;
  broadcast(kind, row);
}

// Watch CSV files
['auris', 'aura', 'solar'].forEach(kind => {
  const fp = FILES[kind];
  if (fs.existsSync(path.dirname(fp))) {
    chokidar.watch(fp, { ignoreInitial: false })
      .on('add', () => pushIfNew(kind === 'auris' ? 'auris_metrics' : kind === 'aura' ? 'aura_features' : 'solar_harmonics', fp))
      .on('change', () => pushIfNew(kind === 'auris' ? 'auris_metrics' : kind === 'aura' ? 'aura_features' : 'solar_harmonics', fp));
  }
});

wss.on('connection', (ws) => {
  console.log('[auris-bridge] Client connected');
  
  // Send current snapshots
  const a = lastRow(FILES.auris);
  const b = lastRow(FILES.aura);
  const s = lastRow(FILES.solar);
  
  if (a) ws.send(JSON.stringify({ type: 'auris_metrics', data: a }));
  if (b) ws.send(JSON.stringify({ type: 'aura_features', data: b }));
  if (s) ws.send(JSON.stringify({ type: 'solar_harmonics', data: s }));
  
  // Send current harmonic state
  ws.send(JSON.stringify({ 
    type: 'harmonic_state', 
    data: { ...harmonicState, solarChain } 
  }));

  ws.on('message', (message) => {
    try {
      const { type, data } = JSON.parse(message);
      
      switch (type) {
        case 'solar_chain_update':
          solarChain = data.chain || [];
          broadcast('solar_chain_update', { chain: solarChain });
          break;
          
        case 'harmonic_control':
          harmonicState = { ...harmonicState, ...data };
          broadcast('harmonic_state', { ...harmonicState, solarChain });
          break;
          
        case 'waveform_data':
          // Broadcast waveform to all clients for visualization
          broadcast('waveform_data', data);
          break;
      }
    } catch (err) {
      console.error('[auris-bridge] Message parse error:', err);
    }
  });

  ws.on('close', () => {
    console.log('[auris-bridge] Client disconnected');
  });
});