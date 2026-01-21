import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { supabase } from '@/integrations/supabase/client';
import { TrendingUp, Target, Zap, Activity } from 'lucide-react';

type Stats = {
  totalSignals: number;
  longSignals: number;
  shortSignals: number;
  optimalSignals: number;
  averageStrength: number;
  lheCount: number;
  averageCoherence: number;
  highestStrength: number;
};

export const OptimalEntryStats = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();

    const interval = setInterval(fetchStats, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      // Fetch signal statistics
      const { data: signals, error: signalsError } = await supabase
        .from('trading_signals')
        .select('signal_type, strength, reason, coherence')
        .gte('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());

      if (signalsError) throw signalsError;

      // Fetch LHE count
      const { data: lheData, error: lheError } = await supabase
        .from('lighthouse_events')
        .select('is_lhe')
        .gte('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
        .eq('is_lhe', true);

      if (lheError) throw lheError;

      const signalArray = signals || [];
      const longCount = signalArray.filter(s => s.signal_type === 'LONG').length;
      const shortCount = signalArray.filter(s => s.signal_type === 'SHORT').length;
      const optimalCount = signalArray.filter(s => s.reason.startsWith('🎯 OPTIMAL')).length;
      const avgStrength = signalArray.length > 0
        ? signalArray.reduce((sum, s) => sum + Number(s.strength), 0) / signalArray.length
        : 0;
      const avgCoherence = signalArray.length > 0
        ? signalArray.reduce((sum, s) => sum + Number(s.coherence), 0) / signalArray.length
        : 0;
      const highestStrength = signalArray.length > 0
        ? Math.max(...signalArray.map(s => Number(s.strength)))
        : 0;

      setStats({
        totalSignals: signalArray.length,
        longSignals: longCount,
        shortSignals: shortCount,
        optimalSignals: optimalCount,
        averageStrength: avgStrength,
        lheCount: lheData?.length || 0,
        averageCoherence: avgCoherence,
        highestStrength,
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Optimal Entry Statistics</h3>
        <p className="text-muted-foreground">Loading statistics...</p>
      </Card>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-2">
          <Target className="h-5 w-5 text-muted-foreground" />
          <Badge style={{ backgroundColor: '#00FF88' }}>24h</Badge>
        </div>
        <p className="text-sm text-muted-foreground">Optimal Signals</p>
        <p className="text-3xl font-bold mt-1">{stats.optimalSignals}</p>
        <p className="text-xs text-muted-foreground mt-2">
          {stats.totalSignals > 0 
            ? `${((stats.optimalSignals / stats.totalSignals) * 100).toFixed(1)}% of total`
            : 'No signals yet'}
        </p>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-2">
          <TrendingUp className="h-5 w-5 text-muted-foreground" />
          <Badge style={{ backgroundColor: '#4169E1' }}>LONG</Badge>
        </div>
        <p className="text-sm text-muted-foreground">Long Signals</p>
        <p className="text-3xl font-bold mt-1">{stats.longSignals}</p>
        <p className="text-xs text-muted-foreground mt-2">
          Avg Strength: {(stats.averageStrength * 100).toFixed(0)}%
        </p>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-2">
          <Zap className="h-5 w-5 text-muted-foreground" />
          <Badge style={{ backgroundColor: '#FFD700' }}>LHE</Badge>
        </div>
        <p className="text-sm text-muted-foreground">Lighthouse Events</p>
        <p className="text-3xl font-bold mt-1">{stats.lheCount}</p>
        <p className="text-xs text-muted-foreground mt-2">
          High coherence detections
        </p>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-2">
          <Activity className="h-5 w-5 text-muted-foreground" />
          <Badge variant="secondary">Γ</Badge>
        </div>
        <p className="text-sm text-muted-foreground">Avg Coherence</p>
        <p className="text-3xl font-bold mt-1">{stats.averageCoherence.toFixed(3)}</p>
        <p className="text-xs text-muted-foreground mt-2">
          Peak: {stats.highestStrength.toFixed(3)}
        </p>
      </Card>
    </div>
  );
};
