import { useState, useEffect } from 'react';
import { harmonicAuth, HarmonicNexusSession } from '@/lib/harmonic-nexus-auth';

export function useHarmonicAuth() {
  const [session, setSession] = useState<HarmonicNexusSession | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Try to validate existing session first
        const isValid = await harmonicAuth.validateSession();
        
        if (isValid) {
          setSession(harmonicAuth.getSession());
          setIsAuthenticated(true);
        } else {
          // Auto-login with default charter
          const newSession = await harmonicAuth.autoLogin();
          setSession(newSession);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Authentication initialization failed:', error);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (charterId?: string) => {
    setIsLoading(true);
    try {
      const newSession = await harmonicAuth.autoLogin(charterId);
      setSession(newSession);
      setIsAuthenticated(true);
      return newSession;
    } catch (error) {
      setIsAuthenticated(false);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    harmonicAuth.logout();
    setSession(null);
    setIsAuthenticated(false);
  };

  const hasPermission = (permission: keyof HarmonicNexusSession['permissions']) => {
    return harmonicAuth.hasPermission(permission);
  };

  const getAuthHeaders = () => {
    return harmonicAuth.getAuthHeaders();
  };

  return {
    session,
    isAuthenticated,
    isLoading,
    login,
    logout,
    hasPermission,
    getAuthHeaders
  };
}