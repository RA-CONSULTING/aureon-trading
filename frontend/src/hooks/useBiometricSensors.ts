import { useState, useEffect } from 'react';

export interface BiometricData {
  hrv: number; // Heart Rate Variability (ms)
  alpha: number; // Alpha brain waves (8-13 Hz) as percentage
  theta: number; // Theta brain waves (4-8 Hz) as percentage
  delta: number; // Delta brain waves (0.5-4 Hz) as percentage
  beta: number; // Beta brain waves (13-30 Hz) as percentage
  heartRate: number; // BPM
  coherenceIndex: number; // 0-1 scale
  timestamp: Date;
  sensorStatus: 'connected' | 'disconnected' | 'calibrating';
}

export function useBiometricSensors() {
  const [biometricData, setBiometricData] = useState<BiometricData | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      try {
        // Connect to Earth Live Data WebSocket server for biometric sensors
        ws = new WebSocket('ws://localhost:8788/biometrics');
        
        ws.onopen = () => {
          console.log('💓 Connected to Earth Live Data - Biometric Sensors');
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('📊 Biometric data received:', data);
            
            // Parse incoming data from HRV monitors and EEG headsets
            setBiometricData({
              hrv: data.hrv || 50,
              alpha: data.alpha || 0.4,
              theta: data.theta || 0.3,
              delta: data.delta || 0.2,
              beta: data.beta || 0.1,
              heartRate: data.heartRate || 72,
              coherenceIndex: data.coherenceIndex || 0.5,
              timestamp: new Date(),
              sensorStatus: data.sensorStatus || 'connected'
            });
          } catch (error) {
            console.error('❌ Error parsing biometric data:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          setIsConnected(false);
        };

        ws.onclose = () => {
          console.log('🔌 Disconnected from Biometric Sensors');
          setIsConnected(false);
          
          // Attempt to reconnect after 5 seconds
          reconnectTimeout = setTimeout(() => {
            console.log('🔄 Attempting to reconnect...');
            connect();
          }, 5000);
        };
      } catch (error) {
        console.error('❌ Failed to connect to Biometric Sensors:', error);
        setIsConnected(false);
        
        // Retry connection
        reconnectTimeout = setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, []);

  return { biometricData, isConnected };
}
