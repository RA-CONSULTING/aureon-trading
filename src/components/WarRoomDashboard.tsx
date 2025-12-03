import { useQuantumWarRoom } from '@/hooks/useQuantumWarRoom';
import { QuantumStatePanel } from './warroom/QuantumStatePanel';
import { HistoricalTimeline } from './warroom/HistoricalTimeline';
import { LiveStrikeStream } from './warroom/LiveStrikeStream';
import { AurisNodesOrbit } from './warroom/AurisNodesOrbit';
import { ProjectionHorizon } from './warroom/ProjectionHorizon';
import { GasTankDisplay } from './warroom/GasTankDisplay';
import { UnifiedBusStatus } from './warroom/UnifiedBusStatus';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function WarRoomDashboard() {
  const { state, launchAssault, emergencyStop } = useQuantumWarRoom();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <div className="container mx-auto p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-destructive to-primary bg-clip-text text-transparent">
              🦆 QUANTUM QUACKERS WAR ROOM
            </h1>
            <p className="text-muted-foreground mt-1">
              Autonomous Trading • Real Quantum Data • Temporal Ladder Connected
            </p>
          </div>
        </div>

        {/* Status & Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="bg-card/50 backdrop-blur border-primary/20 lg:col-span-2">
            <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Status</p>
                    <p className="text-2xl font-bold">
                      {state.status === 'idle' && '⏸️ IDLE'}
                      {state.status === 'active' && '🔥 ACTIVE ASSAULT'}
                      {state.status === 'emergency_stopped' && '🚨 EMERGENCY STOP'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Balance</p>
                    <p className="text-2xl font-bold text-green-500">
                      ${state.currentBalance.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Trades</p>
                    <p className="text-2xl font-bold text-blue-500">
                      {state.tradesExecuted}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Net P&L</p>
                    <p className={`text-2xl font-bold ${state.netPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      ${state.netPnL.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                {state.status === 'idle' && (
                  <Button
                    size="lg"
                    onClick={launchAssault}
                    className="bg-gradient-to-r from-destructive to-primary hover:from-destructive/90 hover:to-primary/90 text-white font-bold text-lg px-8"
                  >
                    🚀 LAUNCH ASSAULT
                  </Button>
                )}
                {state.status === 'active' && (
                  <Button
                    size="lg"
                    variant="destructive"
                    onClick={emergencyStop}
                    className="font-bold text-lg px-8"
                  >
                    🚨 EMERGENCY STOP
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Gas Tank Display */}
        <GasTankDisplay 
          userId="demo-user" 
          onEmpty={emergencyStop}
        />
      </div>

        {/* Quantum State */}
        <QuantumStatePanel 
          quantumState={state.quantumState} 
          hiveMindCoherence={state.hiveMindCoherence}
        />

        {/* Historical + Live Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <HistoricalTimeline />
          <LiveStrikeStream />
        </div>

        {/* Unified Bus Status */}
        <UnifiedBusStatus />

        {/* Auris Nodes Orbit */}
        <AurisNodesOrbit quantumState={state.quantumState} />

        {/* Projection Horizon */}
        <ProjectionHorizon />
      </div>
    </div>
  );
}
