#!/usr/bin/env node

/**
 * Earth live data WebSocket server.
 *
 * This server does not synthesize Schumann or biometric readings. Until a real
 * source is connected, it emits no_data payloads so consumers cannot mistake
 * generated values for operational telemetry.
 */

const WebSocket = require('ws');

const schumannServer = new WebSocket.Server({ port: 8787, path: '/schumann' });
const biometricServer = new WebSocket.Server({ port: 8788, path: '/biometrics' });

function noDataMetric(name, sourceId, sourceName, sourceUrl, blocker) {
  return {
    name,
    truth_status: 'no_data',
    source_id: sourceId,
    source_name: sourceName,
    source_url: sourceUrl,
    collected_at: Date.now() / 1000,
    freshness_ttl_sec: 60,
    derived_from: [],
    derivation_method: '',
    is_operational_metric: true,
    blocker,
    value: null,
    unit: '',
  };
}

function sendEvery(ws, payloadFactory, intervalMs) {
  const send = () => ws.send(JSON.stringify(payloadFactory()));
  const interval = setInterval(send, intervalMs);
  send();
  ws.on('close', () => clearInterval(interval));
  ws.on('error', () => clearInterval(interval));
}

schumannServer.on('connection', (ws) => {
  sendEvery(ws, () => ({
    frequency: null,
    amplitude: null,
    quality: null,
    variance: null,
    harmonics: [],
    timestamp: new Date().toISOString(),
    real_data: noDataMetric(
      'earth_server.schumann',
      'noaa_swpc',
      'NOAA Space Weather Prediction Center',
      'https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json',
      'direct_schumann_sensor_not_configured',
    ),
  }), 2000);
});

biometricServer.on('connection', (ws) => {
  sendEvery(ws, () => ({
    hrv: null,
    heartRate: null,
    alpha: null,
    theta: null,
    delta: null,
    beta: null,
    coherenceIndex: null,
    sensorStatus: 'no_data',
    timestamp: new Date().toISOString(),
    real_data: noDataMetric(
      'earth_server.biometrics',
      'biometric_sensor',
      'Biometric Sensor',
      'local:biometric-sensor',
      'real_biometric_sensor_not_configured',
    ),
  }), 1000);
});

for (const [label, server] of [['Schumann', schumannServer], ['Biometric', biometricServer]]) {
  server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
      console.error(`${label} server port is already in use.`);
    } else {
      console.error(`${label} server error:`, error.message);
    }
    process.exit(1);
  });
}

console.log('Earth live data server ready: ws://localhost:8787/schumann and ws://localhost:8788/biometrics');
