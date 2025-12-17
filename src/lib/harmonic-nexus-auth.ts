import { supabase } from '@/integrations/supabase/client';

export interface HarmonicNexusSession {
  session_token: string;
  charter_id: string;
  permissions: {
    live_data: boolean;
    validation: boolean;
    admin: boolean;
    realtime: boolean;
  };
  expires_at: string;
}

export class HarmonicNexusAuth {
  private static instance: HarmonicNexusAuth;
  private session: HarmonicNexusSession | null = null;

  static getInstance(): HarmonicNexusAuth {
    if (!HarmonicNexusAuth.instance) {
      HarmonicNexusAuth.instance = new HarmonicNexusAuth();
    }
    return HarmonicNexusAuth.instance;
  }

  async autoLogin(charterId: string = 'nexus-charter-prime'): Promise<HarmonicNexusSession> {
    try {
      const { data, error } = await supabase.functions.invoke('harmonic-nexus-auth', {
        body: { 
          charter_id: charterId,
          action: 'login'
        }
      });

      if (error || !data.success) {
        throw new Error(data?.error || 'Authentication failed');
      }

      this.session = data;
      localStorage.setItem('hnc_session', JSON.stringify(this.session));
      
      console.log('🌟 Harmonic Nexus Charter - Auto-login successful');
      return this.session;
    } catch (error) {
      console.error('❌ Auto-login failed:', error);
      throw error;
    }
  }

  async validateSession(): Promise<boolean> {
    if (!this.session) {
      const stored = localStorage.getItem('hnc_session');
      if (stored) {
        this.session = JSON.parse(stored);
      } else {
        return false;
      }
    }

    try {
      const { data, error } = await supabase.functions.invoke('harmonic-nexus-auth', {
        body: { 
          session_token: this.session.session_token,
          action: 'validate'
        }
      });

      if (error || !data.valid) {
        this.session = null;
        localStorage.removeItem('hnc_session');
        return false;
      }

      return true;
    } catch (error) {
      console.error('Session validation failed:', error);
      return false;
    }
  }

  getSession(): HarmonicNexusSession | null {
    return this.session;
  }

  hasPermission(permission: keyof HarmonicNexusSession['permissions']): boolean {
    return this.session?.permissions[permission] || false;
  }

  getAuthHeaders(): Record<string, string> {
    if (!this.session) {
      throw new Error('No active session');
    }
    
    return {
      'Authorization': `Bearer ${this.session.session_token}`,
      'X-Charter-ID': this.session.charter_id
    };
  }

  logout(): void {
    this.session = null;
    localStorage.removeItem('hnc_session');
  }
}

export const harmonicAuth = HarmonicNexusAuth.getInstance();