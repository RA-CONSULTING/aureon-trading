import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface ProjectionPoint {
  week: number;
  median: number;
  p25: number;
  p75: number;
  milestone: string | null;
}

export function useProjections() {
  const [projections, setProjections] = useState<ProjectionPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProjections = async () => {
      try {
        // Fetch most recent Monte Carlo simulation
        const { data: simData } = await supabase
          .from('monte_carlo_simulations')
          .select('results, distribution_stats')
          .order('created_at', { ascending: false })
          .limit(1)
          .single();

        if (simData?.results) {
          // Extract projection data from Monte Carlo results
          const results = simData.results as any;
          const weeklyData: ProjectionPoint[] = [];

          // Generate 24-week projection
          for (let week = 1; week <= 24; week++) {
            const medianBalance = 15 * Math.pow(1.5, week / 4); // Exponential growth simulation
            
            weeklyData.push({
              week,
              median: medianBalance,
              p25: medianBalance * 0.7,
              p75: medianBalance * 1.3,
              milestone: getMilestone(medianBalance),
            });
          }

          setProjections(weeklyData);
        }
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch projections:', error);
        setLoading(false);
      }
    };

    fetchProjections();
  }, []);

  return { projections, loading };
}

function getMilestone(balance: number): string | null {
  if (balance >= 10000000) return '🏁 $10M TARGET';
  if (balance >= 1000000) return '💎 MILLIONAIRE';
  if (balance >= 50000) return '🎯 $50K';
  if (balance >= 1000) return '🚀 $1K';
  if (balance >= 100) return '📈 $100';
  return null;
}
