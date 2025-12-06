/**
 * useSmokeTestStartup hook
 * 
 * Ensures all system families pass Lighthouse validation
 * before trading can begin. Prevents trading with ghost systems.
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  smokeTestPhaseValidator, 
  SmokeTestState 
} from '@/core/smokeTestPhaseValidator';
import { toast } from 'sonner';

export interface SmokeTestStartupResult {
  state: SmokeTestState | null;
  isValidated: boolean;
  hasGhosts: boolean;
  runSmokeTest: () => void;
  waitForValidation: () => Promise<boolean>;
}

export function useSmokeTestStartup(): SmokeTestStartupResult {
  const [state, setState] = useState<SmokeTestState | null>(null);
  const [isValidated, setIsValidated] = useState(false);
  const [hasGhosts, setHasGhosts] = useState(false);

  useEffect(() => {
    const unsubscribe = smokeTestPhaseValidator.subscribe((newState) => {
      setState(newState);
      setIsValidated(newState.lighthouseValidated);
      setHasGhosts(newState.overallStatus === 'GHOST_ALERT');
      
      // Toast notifications for state changes
      if (newState.overallStatus === 'PASSED' && !isValidated) {
        toast.success('Lighthouse Smoke Test PASSED - All systems validated');
      } else if (newState.overallStatus === 'GHOST_ALERT') {
        toast.error('GHOST SYSTEMS DETECTED - Trading blocked');
      }
    });

    return unsubscribe;
  }, [isValidated]);

  const runSmokeTest = useCallback(() => {
    smokeTestPhaseValidator.start();
    toast.info('Running Lighthouse Smoke Test...');
  }, []);

  const waitForValidation = useCallback((): Promise<boolean> => {
    return new Promise((resolve) => {
      // If already validated, resolve immediately
      const currentState = smokeTestPhaseValidator.getState();
      if (currentState.lighthouseValidated) {
        resolve(true);
        return;
      }
      
      if (currentState.overallStatus === 'GHOST_ALERT' || currentState.overallStatus === 'FAILED') {
        resolve(false);
        return;
      }

      // Start the test if not running
      if (currentState.overallStatus === 'INITIALIZING') {
        smokeTestPhaseValidator.start();
      }

      // Subscribe and wait for completion
      const unsubscribe = smokeTestPhaseValidator.subscribe((newState) => {
        if (newState.overallStatus === 'PASSED') {
          unsubscribe();
          resolve(true);
        } else if (newState.overallStatus === 'FAILED' || newState.overallStatus === 'GHOST_ALERT') {
          unsubscribe();
          resolve(false);
        }
      });

      // Timeout after 60 seconds
      setTimeout(() => {
        unsubscribe();
        resolve(false);
      }, 60000);
    });
  }, []);

  return {
    state,
    isValidated,
    hasGhosts,
    runSmokeTest,
    waitForValidation,
  };
}
