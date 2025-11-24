// Enhanced WebSocket bridge with ping/pong heartbeat and snapshot functionality
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

const wss = new WebSocket.Server({ port: 8787 });
const SNAP_DIR = path.join(process.cwd(), 'validation', 'snapshots');
if (!fs.existsSync(SNAP_DIR)) fs.mkdirSync(SNAP_DIR, {recursive:true});

function broadcast(type, data){
  const msg = JSON.stringify({type, ...data});
  wss.clients.forEach(c => { try{ c.send(msg) }catch{} });
}

let lastAuris = {};
let lastAura = {};

function watchFile(file, type, parser) {
  if (!fs.existsSync(file)) return;
  
  fs.watchFile(file, { interval: 500 }, () => {
    try {
      const content = fs.readFileSync(file, 'utf8');
      const lines = content.trim().split('\n').filter(line => !line.startsWith('#'));
      if (lines.length < 2) return;
      
      const headers = lines[0].split(',');
      const lastRow = lines[lines.length - 1].split(',');
      
      const data = {};
      headers.forEach((header, i) => {
        const val = lastRow[i];
        data[header.trim()] = isNaN(val) ? val : Number(val);
      });
      
      if (type === 'auris_metrics') lastAuris = data;
      if (type === 'aura_features') lastAura = data;
      
      broadcast(type, { data });
    } catch (err) {
      console.error(`Error reading ${file}:`, err.message);
    }
  });
}

wss.on('connection', (ws) => {
  console.log('Client connected');
  
  // Send current data immediately
  if (Object.keys(lastAuris).length) ws.send(JSON.stringify({type: 'auris_metrics', data: lastAuris}));
  if (Object.keys(lastAura).length) ws.send(JSON.stringify({type: 'aura_features', data: lastAura}));
  
  ws.on('message', (buf) => {
    let pkt; 
    try { pkt = JSON.parse(buf.toString()) } catch { return; }

    if (pkt.type === 'ping') { // heartbeat round-trip
      ws.send(JSON.stringify({type:"pong", t0: pkt.t0}));
      return;
    }

    if (pkt.type === 'control') {
      fs.writeFileSync('validation/control_hints.json', JSON.stringify({
        gain: pkt.gain, targets_hz: pkt.targets_hz, ts: new Date().toISOString()
      }, null, 2));
      broadcast('control', pkt);
      return;
    }

    if (pkt.type === 'snapshot') {
      const fname = path.join(SNAP_DIR, `snap_${Date.now()}.json`);
      fs.writeFileSync(fname, JSON.stringify(pkt, null, 2));
      // pin markers in CSVs
      try {
        fs.appendFileSync('validation/auris_metrics.csv', `# SNAPSHOT ${pkt.at}\n`);
        fs.appendFileSync('validation/aura_features.csv', `# SNAPSHOT ${pkt.at}\n`);
      } catch {}
      broadcast('snapshot', {at: pkt.at});
      return;
    }
  });

  ws.on('close', () => console.log('Client disconnected'));
});

// Watch for CSV file changes
watchFile('validation/auris_metrics.csv', 'auris_metrics');
watchFile('validation/aura_features.csv', 'aura_features');

console.log('Enhanced WebSocket bridge running on port 8787');
console.log('Features: ping/pong heartbeat, snapshot saving, CSV markers');
console.log('Watching: validation/auris_metrics.csv, validation/aura_features.csv');
