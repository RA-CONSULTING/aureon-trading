// Background Services Layer
// Runs silently on login, only surfaces alerts when issues arise

import { dataStreamMonitor } from './dataStreamMonitor';

export interface BackgroundServiceState {
  smokeTestPassed: boolean;
  dataIntegrityScore: number;
  exchangeConnectivity: Record<string, 'live' | 'demo' | 'offline'>;
  lastHealthCheck: Date | null;
  alerts: BackgroundAlert[];
}

export interface BackgroundAlert {
  id: string;
  type: 'error' | 'warning' | 'info';
  source: string;
  message: string;
  timestamp: Date;
  dismissed: boolean;
}

type AlertListener = (alerts: BackgroundAlert[]) => void;

class BackgroundServicesCore {
  private state: BackgroundServiceState = {
    smokeTestPassed: false,
    dataIntegrityScore: 100,
    exchangeConnectivity: {},
    lastHealthCheck: null,
    alerts: [],
  };
  
  private listeners: Set<AlertListener> = new Set();
  private healthCheckInterval: NodeJS.Timeout | null = null;
  private alertIdCounter = 0;

  start() {
    console.log('[BackgroundServices] Starting silent monitoring...');
    
    // Start health check loop
    this.healthCheckInterval = setInterval(() => {
      this.runHealthCheck();
    }, 10000); // Every 10 seconds
    
    // Initial check
    this.runHealthCheck();
  }

  stop() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
    console.log('[BackgroundServices] Stopped');
  }

  private runHealthCheck() {
    this.state.lastHealthCheck = new Date();
    
    // Check data stream health
    const streamState = dataStreamMonitor.getState();
    const unhealthyEndpoints = dataStreamMonitor.getUnhealthyEndpoints();
    
    // Clear old stream-related alerts and add new ones if needed
    this.state.alerts = this.state.alerts.filter(a => a.source !== 'data-stream');
    
    if (unhealthyEndpoints.length > 3) {
      this.addAlert('warning', 'data-stream', `${unhealthyEndpoints.length} API endpoints are unhealthy`);
    }
    
    if (streamState.overallHealth === 'down') {
      this.addAlert('error', 'data-stream', 'Data stream is DOWN - no API responses');
    }
    
    // Notify listeners
    this.notifyListeners();
  }

  updateSmokeTestStatus(passed: boolean, failedSystems?: string[]) {
    this.state.smokeTestPassed = passed;
    this.state.alerts = this.state.alerts.filter(a => a.source !== 'smoke-test');
    
    if (!passed && failedSystems && failedSystems.length > 0) {
      this.addAlert('error', 'smoke-test', `Smoke test failed: ${failedSystems.join(', ')}`);
    }
    
    this.notifyListeners();
  }

  updateDataIntegrity(score: number) {
    this.state.dataIntegrityScore = score;
    this.state.alerts = this.state.alerts.filter(a => a.source !== 'data-integrity');
    
    if (score < 80) {
      this.addAlert('warning', 'data-integrity', `Data integrity at ${score.toFixed(0)}% - below threshold`);
    }
    if (score < 50) {
      this.addAlert('error', 'data-integrity', `Critical: Data integrity at ${score.toFixed(0)}%`);
    }
    
    this.notifyListeners();
  }

  updateExchangeConnectivity(exchange: string, status: 'live' | 'demo' | 'offline') {
    this.state.exchangeConnectivity[exchange] = status;
    this.state.alerts = this.state.alerts.filter(a => a.source !== `exchange-${exchange}`);
    
    if (status === 'offline') {
      this.addAlert('error', `exchange-${exchange}`, `${exchange} is OFFLINE`);
    } else if (status === 'demo') {
      this.addAlert('warning', `exchange-${exchange}`, `${exchange} using DEMO data`);
    }
    
    this.notifyListeners();
  }

  private addAlert(type: 'error' | 'warning' | 'info', source: string, message: string) {
    this.state.alerts.push({
      id: `alert-${++this.alertIdCounter}`,
      type,
      source,
      message,
      timestamp: new Date(),
      dismissed: false,
    });
  }

  dismissAlert(alertId: string) {
    const alert = this.state.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.dismissed = true;
      this.notifyListeners();
    }
  }

  getActiveAlerts(): BackgroundAlert[] {
    return this.state.alerts.filter(a => !a.dismissed);
  }

  getState(): BackgroundServiceState {
    return { ...this.state };
  }

  subscribe(listener: AlertListener): () => void {
    this.listeners.add(listener);
    listener(this.getActiveAlerts());
    return () => this.listeners.delete(listener);
  }

  private notifyListeners() {
    const alerts = this.getActiveAlerts();
    this.listeners.forEach(l => l(alerts));
  }
}

export const backgroundServices = new BackgroundServicesCore();
