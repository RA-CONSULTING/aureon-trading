import { useQuantumWarRoom } from '@/hooks/useQuantumWarRoom';
import { useGlobalState } from '@/hooks/useGlobalState';
import { QuantumStatePanel } from './warroom/QuantumStatePanel';
import { HistoricalTimeline } from './warroom/HistoricalTimeline';
import { LiveStrikeStream } from './warroom/LiveStrikeStream';
import { AurisNodesOrbit } from './warroom/AurisNodesOrbit';
import { ProjectionHorizon } from './warroom/ProjectionHorizon';
import { GasTankDisplay } from './warroom/GasTankDisplay';
import { UnifiedBusStatus } from './warroom/UnifiedBusStatus';
import { MultiExchangePanel } from './warroom/MultiExchangePanel';
import { SystemHealthPanel } from './SystemHealthPanel';
import { PrimeSealStatusPanel } from './warroom/PrimeSealStatusPanel';
import { PrismFrequencyPanel } from './warroom/PrismFrequencyPanel';
import { ProbabilityFusionPanel } from './warroom/ProbabilityFusionPanel';
import { TemporalLadderStatus } from './warroom/TemporalLadderStatus';
import { FullEcosystemStatus } from './warroom/FullEcosystemStatus';
import { TradeControlsHeader } from './warroom/TradeControlsHeader';
import { CredentialStatusPanel } from './warroom/CredentialStatusPanel';
import { ActivePositionsPanel } from './warroom/ActivePositionsPanel';
import { TradingReadinessCheck } from './warroom/TradingReadinessCheck';
import { Badge } from '@/components/ui/badge';

export default function WarRoomDashboard() {
  const { state, launchAssault, emergencyStop } = useQuantumWarRoom();
  const globalState = useGlobalState();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <div className="container mx-auto p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-destructive to-primary bg-clip-text text-transparent">
              🦆 QUANTUM QUACKERS WAR ROOM
            </h1>
            <p className="text-muted-foreground mt-1 flex items-center gap-2">
              Autonomous Trading • Real Quantum Data • Temporal Ladder Connected
              {globalState.isRunning && (
                <Badge variant="default" className="bg-green-500 animate-pulse">
                  SYSTEMS ONLINE
                </Badge>
              )}
            </p>
          </div>
        </div>

        {/* Trade Controls Header with Mode Toggle */}
        <TradeControlsHeader
          onLaunchAssault={launchAssault}
          onEmergencyStop={emergencyStop}
          status={state.status}
          tradesExecuted={state.tradesExecuted}
          netPnL={state.netPnL}
          currentBalance={state.currentBalance}
        />

        {/* Readiness + Credentials + Gas Tank */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <TradingReadinessCheck />
          <CredentialStatusPanel userId={globalState.userId} />
          <GasTankDisplay 
            userId={globalState.userId || 'demo-user'} 
            onEmpty={emergencyStop}
          />
        </div>

        {/* Quantum State */}
        <QuantumStatePanel 
          quantumState={state.quantumState} 
          hiveMindCoherence={state.hiveMindCoherence}
        />

        {/* Prime Seal + Prism + Probability Fusion */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <PrimeSealStatusPanel />
          <PrismFrequencyPanel />
          <ProbabilityFusionPanel />
        </div>

        {/* Active Positions + Live Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ActivePositionsPanel />
          <LiveStrikeStream />
        </div>

        {/* Historical Timeline */}
        <HistoricalTimeline />

        {/* Unified Bus Status */}
        <UnifiedBusStatus />

        {/* Temporal Ladder + Full Ecosystem */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <TemporalLadderStatus />
          <FullEcosystemStatus />
        </div>

        {/* Multi-Exchange Panel */}
        <MultiExchangePanel />

        {/* System Health Panel */}
        <SystemHealthPanel />

        {/* Auris Nodes Orbit */}
        <AurisNodesOrbit quantumState={state.quantumState} />

        {/* Projection Horizon */}
        <ProjectionHorizon />
      </div>
    </div>
  );
}
