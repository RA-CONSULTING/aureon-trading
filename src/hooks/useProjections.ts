import { useState, useEffect } from 'react';

export interface Milestone {
  amount: number;
  label: string;
  eta: string | null;
}

export interface ProjectionData {
  currentBalance: number;
  projectedBalance: number[];
  timestamps: string[];
  milestones: Milestone[];
  confidenceBand: { min: number[]; max: number[] };
}

const MILESTONES = [
  { amount: 100, label: '$100' },
  { amount: 1000, label: '$1K' },
  { amount: 50000, label: '$50K' },
  { amount: 1000000, label: '$1M' },
  { amount: 13620000, label: '$13.6M' },
];

export function useProjections(
  currentBalance: number,
  winRate: number,
  avgTradeSize: number,
  tradesPerDay: number
) {
  const [projection, setProjection] = useState<ProjectionData>({
    currentBalance,
    projectedBalance: [],
    timestamps: [],
    milestones: [],
    confidenceBand: { min: [], max: [] },
  });

  useEffect(() => {
    if (currentBalance === 0 || winRate === 0 || tradesPerDay === 0) {
      return;
    }

    const simulate = () => {
      const days = 180; // Project 6 months
      const simulations = 100;
      const results: number[][] = [];

      // Run Monte Carlo simulations
      for (let sim = 0; sim < simulations; sim++) {
        const path = [currentBalance];
        let balance = currentBalance;

        for (let day = 1; day <= days; day++) {
          const trades = Math.floor(tradesPerDay + (Math.random() - 0.5) * tradesPerDay * 0.2);
          
          for (let t = 0; t < trades; t++) {
            const isWin = Math.random() < winRate;
            const tradeReturn = isWin
              ? avgTradeSize * (1 + Math.random() * 0.5)
              : avgTradeSize * (0.5 + Math.random() * 0.3);
            
            balance = isWin ? balance * (1 + tradeReturn / 100) : balance * (1 - tradeReturn / 100);
          }

          path.push(balance);
        }

        results.push(path);
      }

      // Calculate median, min, max
      const median: number[] = [];
      const min: number[] = [];
      const max: number[] = [];

      for (let day = 0; day <= days; day++) {
        const values = results.map(r => r[day]).sort((a, b) => a - b);
        median.push(values[Math.floor(simulations / 2)]);
        min.push(values[Math.floor(simulations * 0.1)]);
        max.push(values[Math.floor(simulations * 0.9)]);
      }

      // Generate timestamps
      const timestamps = Array.from({ length: days + 1 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() + i);
        return date.toISOString();
      });

      // Calculate milestone ETAs
      const milestones = MILESTONES.map(m => {
        const dayIndex = median.findIndex(b => b >= m.amount);
        const eta = dayIndex > 0 ? `${dayIndex} days` : null;
        return { ...m, eta };
      });

      setProjection({
        currentBalance,
        projectedBalance: median,
        timestamps,
        milestones,
        confidenceBand: { min, max },
      });
    };

    simulate();
  }, [currentBalance, winRate, avgTradeSize, tradesPerDay]);

  return projection;
}
