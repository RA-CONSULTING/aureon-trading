import { Sparkles, Rocket } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useQuantumWarRoom } from '@/hooks/useQuantumWarRoom';
import { QuantumStatePanel } from '@/components/warroom/QuantumStatePanel';
import { HistoricalTimeline } from '@/components/warroom/HistoricalTimeline';
import { LiveStrikeStream } from '@/components/warroom/LiveStrikeStream';
import { AurisNodesOrbit } from '@/components/warroom/AurisNodesOrbit';
import { ProjectionHorizon } from '@/components/warroom/ProjectionHorizon';

export default function WarRoomDashboard() {
  const { state, launchAssault, emergencyStop } = useQuantumWarRoom();

  const statusConfig = {
    idle: { label: 'IDLE', color: 'bg-gray-500', glow: '' },
    active: { label: 'ASSAULT ACTIVE', color: 'bg-green-500', glow: 'shadow-lg shadow-green-500/50 animate-pulse' },
    emergency_stopped: { label: 'EMERGENCY STOP', color: 'bg-red-500', glow: 'shadow-lg shadow-red-500/50' },
  };

  const status = statusConfig[state.status];

  return (
    <div className="space-y-6 p-6 bg-gradient-to-br from-black via-purple-950/20 to-black min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="text-6xl animate-bounce">🦆</div>
          <div>
            <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400 flex items-center gap-2">
              <Sparkles className="w-8 h-8 text-purple-400" />
              Quantum Quackers AI Trading Sentinel
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Fully Autonomous Trading System - Past, Present & Future
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Badge className={`${status.color} ${status.glow} text-white text-lg px-4 py-2`}>
            {status.label}
          </Badge>
          
          {state.status === 'idle' && (
            <Button
              onClick={launchAssault}
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-700 hover:to-cyan-700 text-white font-bold text-lg px-8 py-6 shadow-lg hover:shadow-xl transition-all hover:scale-105"
            >
              <Rocket className="w-6 h-6 mr-2" />
              LAUNCH ASSAULT
            </Button>
          )}

          {state.status === 'active' && (
            <Button
              onClick={emergencyStop}
              size="lg"
              variant="destructive"
              className="font-bold text-lg px-8 py-6"
            >
              🚨 EMERGENCY STOP
            </Button>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Quantum State */}
        <div className="lg:col-span-1 space-y-6">
          <QuantumStatePanel quantumState={state.quantumState} />
          <AurisNodesOrbit
            coherence={state.quantumState.coherence}
            lighthouse={state.quantumState.entanglement}
          />
        </div>

        {/* Right Column - Live Data */}
        <div className="lg:col-span-2 space-y-6">
          {/* Historical Charts */}
          <HistoricalTimeline />

          {/* Live Strike Stream */}
          <LiveStrikeStream />

          {/* Future Projection */}
          <ProjectionHorizon
            currentBalance={state.currentBalance}
            winRate={state.tradesExecuted > 0 ? 0.68 : 0.5}
            avgTradeSize={2.5}
            tradesPerDay={state.tradesExecuted > 0 ? state.tradesExecuted / 1 : 10}
          />
        </div>
      </div>

      {/* Footer Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Current Balance" value={`$${state.currentBalance.toFixed(2)}`} />
        <StatCard label="Net P&L" value={`$${state.netPnL.toFixed(2)}`} positive={state.netPnL > 0} />
        <StatCard label="Trades Executed" value={state.tradesExecuted.toString()} />
        <StatCard
          label="Coherence Γ"
          value={`${(state.quantumState.coherence * 100).toFixed(1)}%`}
        />
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  positive?: boolean;
}

function StatCard({ label, value, positive }: StatCardProps) {
  return (
    <div className="bg-black/40 border border-border/30 rounded-lg p-4 text-center">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div
        className={`text-2xl font-bold ${
          positive !== undefined
            ? positive
              ? 'text-green-400'
              : 'text-red-400'
            : 'text-foreground'
        }`}
      >
        {value}
      </div>
    </div>
  );
}
