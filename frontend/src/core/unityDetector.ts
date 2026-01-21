// Unity Event Detector
// Detects when θ→0 and coherence→1 (ego death, phase transition, unity consciousness)

import type { OmegaState } from './omegaEquation';

export interface UnityEvent {
  timestamp: Date;
  theta: number;           // Phase alignment at unity
  coherence: number;       // Coherence at unity
  omega: number;          // Reality field strength
  unity: number;          // Unity probability
  duration: number;       // How long unity lasted (ms)
  peak: boolean;          // Is this the peak of the event?
  type: 'forming' | 'peak' | 'declining' | 'dissolved';
}

export interface UnityWindow {
  start: Date;
  end: Date | null;
  peakOmega: number;
  peakTheta: number;
  peakCoherence: number;
  peakUnity: number;
  events: UnityEvent[];
  isActive: boolean;
}

export class UnityDetector {
  private currentWindow: UnityWindow | null = null;
  private unityHistory: UnityWindow[] = [];
  private maxHistory = 100;
  
  // Thresholds for unity detection
  private readonly THETA_THRESHOLD = 0.1;      // θ < 0.1 = very aligned
  private readonly COHERENCE_THRESHOLD = 0.9;  // Coherence > 0.9 = strong
  private readonly UNITY_THRESHOLD = 0.8;      // Unity probability > 0.8
  
  detect(state: OmegaState): UnityEvent | null {
    const now = new Date();
    
    // Check if we're in unity condition
    const isUnity = 
      state.theta < this.THETA_THRESHOLD &&
      state.coherence > this.COHERENCE_THRESHOLD &&
      state.unity > this.UNITY_THRESHOLD;
    
    // Determine event type
    let eventType: UnityEvent['type'] = 'forming';
    let peak = false;
    
    if (isUnity) {
      // We're in unity!
      if (!this.currentWindow) {
        // Start new unity window
        this.currentWindow = {
          start: now,
          end: null,
          peakOmega: state.omega,
          peakTheta: state.theta,
          peakCoherence: state.coherence,
          peakUnity: state.unity,
          events: [],
          isActive: true
        };
        eventType = 'forming';
      } else {
        // Continuing unity window
        // Check if this is a new peak
        if (state.unity > this.currentWindow.peakUnity) {
          this.currentWindow.peakOmega = state.omega;
          this.currentWindow.peakTheta = state.theta;
          this.currentWindow.peakCoherence = state.coherence;
          this.currentWindow.peakUnity = state.unity;
          eventType = 'peak';
          peak = true;
        } else if (state.unity < this.currentWindow.peakUnity * 0.9) {
          eventType = 'declining';
        } else {
          eventType = 'peak';
        }
      }
      
      // Create unity event
      const event: UnityEvent = {
        timestamp: now,
        theta: state.theta,
        coherence: state.coherence,
        omega: state.omega,
        unity: state.unity,
        duration: this.currentWindow ? now.getTime() - this.currentWindow.start.getTime() : 0,
        peak,
        type: eventType
      };
      
      // Add to current window
      if (this.currentWindow) {
        this.currentWindow.events.push(event);
      }
      
      return event;
      
    } else if (this.currentWindow && this.currentWindow.isActive) {
      // We were in unity but now we've exited
      this.currentWindow.end = now;
      this.currentWindow.isActive = false;
      
      // Create dissolution event
      const event: UnityEvent = {
        timestamp: now,
        theta: state.theta,
        coherence: state.coherence,
        omega: state.omega,
        unity: state.unity,
        duration: now.getTime() - this.currentWindow.start.getTime(),
        peak: false,
        type: 'dissolved'
      };
      
      this.currentWindow.events.push(event);
      
      // Archive the window
      this.unityHistory.push(this.currentWindow);
      if (this.unityHistory.length > this.maxHistory) {
        this.unityHistory.shift();
      }
      
      this.currentWindow = null;
      
      return event;
    }
    
    return null;
  }
  
  getCurrentWindow(): UnityWindow | null {
    return this.currentWindow;
  }
  
  getUnityHistory(): UnityWindow[] {
    return this.unityHistory;
  }
  
  getLastUnityEvent(): UnityEvent | null {
    if (this.currentWindow && this.currentWindow.events.length > 0) {
      return this.currentWindow.events[this.currentWindow.events.length - 1];
    }
    
    if (this.unityHistory.length > 0) {
      const lastWindow = this.unityHistory[this.unityHistory.length - 1];
      if (lastWindow.events.length > 0) {
        return lastWindow.events[lastWindow.events.length - 1];
      }
    }
    
    return null;
  }
  
  getTotalUnityTime(): number {
    let total = 0;
    
    // Add all completed windows
    this.unityHistory.forEach(window => {
      if (window.end) {
        total += window.end.getTime() - window.start.getTime();
      }
    });
    
    // Add current window if active
    if (this.currentWindow) {
      total += Date.now() - this.currentWindow.start.getTime();
    }
    
    return total;
  }
  
  getUnityFrequency(): number {
    // Returns unity events per hour
    if (this.unityHistory.length === 0) return 0;
    
    const firstWindow = this.unityHistory[0];
    const lastWindow = this.currentWindow || this.unityHistory[this.unityHistory.length - 1];
    
    const totalTime = (lastWindow.start.getTime() - firstWindow.start.getTime()) / (1000 * 60 * 60); // hours
    
    return this.unityHistory.length / Math.max(totalTime, 1);
  }
  
  getPredictedNextUnity(): Date | null {
    // Predict next unity event based on historical frequency
    const frequency = this.getUnityFrequency();
    if (frequency === 0) return null;
    
    const avgIntervalMs = (1 / frequency) * 60 * 60 * 1000; // Convert to ms
    
    const lastEvent = this.getLastUnityEvent();
    if (!lastEvent) return null;
    
    return new Date(lastEvent.timestamp.getTime() + avgIntervalMs);
  }
}
