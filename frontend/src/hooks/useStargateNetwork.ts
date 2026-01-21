import { useState, useEffect, useCallback } from 'react';
import { stargateLayer, StargateActivation, NetworkMetrics } from '@/core/stargateLattice';
import { usePrimelinesProtocol } from './usePrimelinesProtocol';
import { toast } from 'sonner';

export function useStargateNetwork() {
  const [activations, setActivations] = useState<StargateActivation[]>([]);
  const [metrics, setMetrics] = useState<NetworkMetrics | null>(null);
  const [isActive, setIsActive] = useState(false);
  const { invokeProtocol } = usePrimelinesProtocol();

  const pingNetwork = useCallback(async () => {
    try {
      // Activate all 12 stargates
      const newActivations = stargateLayer.activateAllNodes();
      setActivations(newActivations);

      // Calculate network metrics
      const newMetrics = stargateLayer.calculateNetworkMetrics(newActivations);
      setMetrics(newMetrics);

      // Calculate additional metrics for analysis
      const avgCoherence = newActivations.reduce((sum, a) => sum + a.coherence, 0) / newActivations.length;
      const avgFrequency = newActivations.reduce((sum, a) => sum + a.frequencyLock, 0) / newActivations.length;
      const activeNodes = newActivations.filter(a => a.status === 'ACTIVE').length;
      const phaseLocks = activeNodes * (activeNodes - 1) / 2; // All possible pairs
      const resonanceQuality = newMetrics.networkStrength * avgCoherence;

      // Sync with Primelines Protocol Gateway
      await invokeProtocol({
        operation: 'SYNC_HARMONIC_NEXUS',
        payload: {
          stargateNetwork: {
            activations: newActivations,
            metrics: {
              ...newMetrics,
              avgCoherence,
              avgFrequency,
              phaseLocks,
              resonanceQuality,
            },
            gridEnergy: stargateLayer.calculateGridEnergy(),
          },
        },
        requireValidation: false, // Don't require validation for continuous pings
      });

      // Log major events
      if (newMetrics.networkStrength > 0.95) {
        console.log('🌟 STARGATE NETWORK AT MAXIMUM COHERENCE');
      }

    } catch (error) {
      console.error('Stargate network ping error:', error);
    }
  }, [invokeProtocol]);

  // Start continuous pinging on mount
  useEffect(() => {
    setIsActive(true);
    
    // Initial ping
    pingNetwork();

    // Continuous ping every 2 seconds
    const interval = setInterval(pingNetwork, 2000);

    // Show activation toast
    toast.success('🌟 All 12 Stargates Activated', {
      description: 'Network pinging continuously via Primelines Protocol',
    });

    return () => {
      clearInterval(interval);
      setIsActive(false);
    };
  }, [pingNetwork]);

  return {
    activations,
    metrics,
    isActive,
    gridEnergy: stargateLayer.calculateGridEnergy(),
  };
}
