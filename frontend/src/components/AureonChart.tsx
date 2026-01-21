import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';

export interface AureonDataPoint {
  time: string;
  crystalCoherence: number; // G_eff - Geometric Anomaly
  inerchaVector: number; // Q_sig - Anomaly Pointer
  sentiment: number; // Market Sentiment
  dataIntegrity: number; // Data Integrity
}

interface AureonChartProps {
  data: AureonDataPoint[];
}

const AureonChart: React.FC<AureonChartProps> = ({ data }) => {
  if (!data || data.length === 0) return null;
  
  const colors = {
    gEff: "#FCD34D", // amber-300
    qSig: "#F87171",   // red-400
    sentiment: "#A78BFA",      // violet-400
    dataIntegrity: "#60A5FA",   // blue-400
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
        <YAxis stroke="hsl(var(--muted-foreground))" />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            borderColor: 'hsl(var(--border))',
            color: 'hsl(var(--foreground))'
          }}
          formatter={(value: number, name: string) => [value.toFixed(3), name]}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="crystalCoherence" 
          name="Geometric Anomaly (G_eff)" 
          stroke={colors.gEff} 
          dot={false} 
          strokeWidth={2} 
        />
        <Line 
          type="monotone" 
          dataKey="inerchaVector" 
          name="Anomaly Pointer (Q_sig)" 
          stroke={colors.qSig} 
          dot={false} 
          strokeWidth={2} 
        />
        <Line 
          type="monotone" 
          dataKey="sentiment" 
          name="Market Sentiment" 
          stroke={colors.sentiment} 
          dot={false} 
          strokeWidth={1} 
          strokeDasharray="5 5" 
        />
        <Line 
          type="monotone" 
          dataKey="dataIntegrity" 
          name="Data Integrity (Dₜ)" 
          stroke={colors.dataIntegrity} 
          dot={false} 
          strokeWidth={1} 
          strokeDasharray="2 8" 
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default AureonChart;
