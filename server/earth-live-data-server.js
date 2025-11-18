#!/usr/bin/env node

/**
 * Earth Live Data WebSocket Server
 * Simulates Schumann Resonance and Biometric sensor data
 * 
 * Run: node server/earth-live-data-server.js
 * or: npm install -g ws && node server/earth-live-data-server.js
 */

const WebSocket = require('ws');

// Create WebSocket servers for each sensor type
const schumannServer = new WebSocket.Server({ port: 8787, path: '/schumann' });
const biometricServer = new WebSocket.Server({ port: 8788, path: '/biometrics' });

console.log('🌍 Earth Live Data Server Starting...\n');

// Schumann Resonance Simulation
schumannServer.on('connection', (ws) => {
  console.log('✅ Schumann Resonance sensor connected');
  
  const sendSchumannData = () => {
    // Simulate Schumann resonance with natural variation
    const baseFreq = 7.83;
    const variation = (Math.sin(Date.now() / 10000) * 0.1) + (Math.random() * 0.05 - 0.025);
    const frequency = baseFreq + variation;
    
    // Amplitude varies between 0.3 and 1.2
    const amplitude = 0.6 + Math.sin(Date.now() / 5000) * 0.3 + Math.random() * 0.2;
    
    // Quality indicator (0-1)
    const quality = 0.7 + Math.sin(Date.now() / 8000) * 0.15 + Math.random() * 0.1;
    
    // Variance in measurements
    const variance = 0.02 + Math.random() * 0.05;
    
    // Generate harmonics (7 harmonics of Schumann Resonance)
    const harmonics = [
      { frequency: 7.83, amplitude: amplitude, name: 'Fundamental' },
      { frequency: 14.3, amplitude: amplitude * (0.6 + Math.random() * 0.2), name: '2nd Harmonic' },
      { frequency: 20.8, amplitude: amplitude * (0.4 + Math.random() * 0.2), name: '3rd Harmonic' },
      { frequency: 27.3, amplitude: amplitude * (0.3 + Math.random() * 0.15), name: '4th Harmonic' },
      { frequency: 33.8, amplitude: amplitude * (0.2 + Math.random() * 0.1), name: '5th Harmonic' },
      { frequency: 39.0, amplitude: amplitude * (0.15 + Math.random() * 0.08), name: '6th Harmonic' },
      { frequency: 45.0, amplitude: amplitude * (0.1 + Math.random() * 0.05), name: '7th Harmonic' },
    ];
    
    const data = {
      frequency,
      amplitude,
      quality,
      variance,
      harmonics,
      timestamp: new Date().toISOString()
    };
    
    ws.send(JSON.stringify(data));
  };
  
  // Send data every 2 seconds
  const interval = setInterval(sendSchumannData, 2000);
  sendSchumannData(); // Send immediately on connect
  
  ws.on('close', () => {
    console.log('❌ Schumann Resonance sensor disconnected');
    clearInterval(interval);
  });
  
  ws.on('error', (error) => {
    console.error('⚠️ Schumann sensor error:', error.message);
  });
});

// Biometric Sensors Simulation
biometricServer.on('connection', (ws) => {
  console.log('✅ Biometric sensors connected');
  
  const sendBiometricData = () => {
    // Simulate heart rate variability (30-120 ms typical range)
    const baseHRV = 60;
    const hrv = baseHRV + Math.sin(Date.now() / 15000) * 20 + Math.random() * 10;
    
    // Heart rate (60-100 BPM normal resting)
    const heartRate = 72 + Math.sin(Date.now() / 20000) * 8 + Math.random() * 4;
    
    // EEG wave percentages (should sum to ~1.0)
    const totalPhase = Date.now() / 10000;
    const alpha = 0.35 + Math.sin(totalPhase) * 0.15 + Math.random() * 0.05; // 8-13 Hz
    const theta = 0.25 + Math.cos(totalPhase * 1.3) * 0.1 + Math.random() * 0.05; // 4-8 Hz
    const delta = 0.15 + Math.sin(totalPhase * 0.7) * 0.05 + Math.random() * 0.03; // 0.5-4 Hz
    const beta = 0.25 + Math.cos(totalPhase * 1.7) * 0.1 + Math.random() * 0.05; // 13-30 Hz
    
    // Normalize to ensure they sum to 1.0
    const total = alpha + theta + delta + beta;
    
    // Coherence index (0-1) - measures synchronization
    const coherenceIndex = 0.5 + Math.sin(Date.now() / 12000) * 0.25 + Math.random() * 0.1;
    
    const data = {
      hrv: Math.max(30, Math.min(120, hrv)),
      heartRate: Math.max(60, Math.min(100, heartRate)),
      alpha: alpha / total,
      theta: theta / total,
      delta: delta / total,
      beta: beta / total,
      coherenceIndex: Math.max(0, Math.min(1, coherenceIndex)),
      sensorStatus: 'connected',
      timestamp: new Date().toISOString()
    };
    
    ws.send(JSON.stringify(data));
  };
  
  // Send data every 1 second
  const interval = setInterval(sendBiometricData, 1000);
  sendBiometricData(); // Send immediately on connect
  
  ws.on('close', () => {
    console.log('❌ Biometric sensors disconnected');
    clearInterval(interval);
  });
  
  ws.on('error', (error) => {
    console.error('⚠️ Biometric sensor error:', error.message);
  });
});

schumannServer.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    console.error('❌ Port 8787 is already in use. Please stop any other servers using this port.');
  } else {
    console.error('❌ Schumann server error:', error.message);
  }
  process.exit(1);
});

biometricServer.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    console.error('❌ Port 8788 is already in use. Please stop any other servers using this port.');
  } else {
    console.error('❌ Biometric server error:', error.message);
  }
  process.exit(1);
});

console.log('📡 Schumann Resonance server: ws://localhost:8787/schumann');
console.log('💓 Biometric sensors server: ws://localhost:8788/biometrics');
console.log('\n🎯 Ready to accept connections...\n');

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n🛑 Shutting down Earth Live Data Server...');
  schumannServer.close();
  biometricServer.close();
  process.exit(0);
});
