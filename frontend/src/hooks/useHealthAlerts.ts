import { useEffect, useState } from 'react';
import { toast } from 'sonner';

interface HealthReport {
  timestamp: string;
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    [key: string]: {
      status: string;
      message: string;
      timestamp: string;
    };
  };
  warnings: string[];
  errors: string[];
}

interface AlertConfig {
  enabled: boolean;
  notifyOnDegraded: boolean;
  notifyOnUnhealthy: boolean;
  emailNotifications: boolean;
  soundAlerts: boolean;
  minTimeBetweenAlerts: number; // milliseconds
}

const DEFAULT_CONFIG: AlertConfig = {
  enabled: true,
  notifyOnDegraded: true,
  notifyOnUnhealthy: true,
  emailNotifications: false,
  soundAlerts: true,
  minTimeBetweenAlerts: 300000, // 5 minutes
};

export function useHealthAlerts(healthReport: HealthReport | null) {
  const [config, setConfig] = useState<AlertConfig>(() => {
    const saved = localStorage.getItem('health_alert_config');
    return saved ? JSON.parse(saved) : DEFAULT_CONFIG;
  });
  
  const [lastAlertTime, setLastAlertTime] = useState<{ [key: string]: number }>({});
  const [previousStatus, setPreviousStatus] = useState<string | null>(null);

  // Save config to localStorage
  useEffect(() => {
    localStorage.setItem('health_alert_config', JSON.stringify(config));
  }, [config]);

  // Monitor health changes
  useEffect(() => {
    if (!healthReport || !config.enabled) return;

    const currentStatus = healthReport.overall_status;
    
    // Check if status changed
    if (previousStatus && currentStatus !== previousStatus) {
      handleStatusChange(previousStatus, currentStatus, healthReport);
    }
    
    setPreviousStatus(currentStatus);
  }, [healthReport, config, previousStatus]);

  const handleStatusChange = (
    oldStatus: string,
    newStatus: string,
    report: HealthReport
  ) => {
    const now = Date.now();
    const alertKey = `status_${newStatus}`;
    
    // Check if enough time has passed since last alert
    if (lastAlertTime[alertKey] && now - lastAlertTime[alertKey] < config.minTimeBetweenAlerts) {
      return;
    }

    // Determine if we should alert
    let shouldAlert = false;
    let severity: 'default' | 'warning' | 'error' = 'default';
    let title = '';
    let description = '';

    if (newStatus === 'degraded' && config.notifyOnDegraded) {
      shouldAlert = true;
      severity = 'warning';
      title = '⚠️ Backend Health Degraded';
      description = report.warnings.length > 0 
        ? report.warnings[0] 
        : 'System performance has degraded';
    } else if (newStatus === 'unhealthy' && config.notifyOnUnhealthy) {
      shouldAlert = true;
      severity = 'error';
      title = '🚨 Backend Health Critical';
      description = report.errors.length > 0 
        ? report.errors[0] 
        : 'Critical system issues detected';
    } else if (newStatus === 'healthy' && oldStatus !== 'healthy') {
      shouldAlert = true;
      severity = 'default';
      title = '✅ Backend Health Restored';
      description = 'All systems operating normally';
    }

    if (shouldAlert) {
      // Show toast notification
      switch (severity) {
        case 'error':
          toast.error(title, { description });
          break;
        case 'warning':
          toast.warning(title, { description });
          break;
        default:
          toast.success(title, { description });
      }

      // Play sound alert
      if (config.soundAlerts && severity !== 'default') {
        playAlertSound(severity);
      }

      // Update last alert time
      setLastAlertTime(prev => ({ ...prev, [alertKey]: now }));

      // Log alert to console
      console.log(`[Health Alert] ${title}: ${description}`, report);
    }
  };

  const playAlertSound = (severity: 'warning' | 'error') => {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      // Different tones for different severities
      oscillator.frequency.value = severity === 'error' ? 800 : 600;
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.error('[Health Alert] Failed to play alert sound:', error);
    }
  };

  const updateConfig = (updates: Partial<AlertConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  };

  const clearAlertHistory = () => {
    setLastAlertTime({});
  };

  return {
    config,
    updateConfig,
    clearAlertHistory,
    lastAlertTime,
  };
}
