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
import { TradingStatusPanel } from './warroom/TradingStatusPanel';
import { LiveTradeStream } from './warroom/LiveTradeStream';
import { LaunchButton } from './warroom/LaunchButton';
import { Badge } from '@/components/ui/badge';
// 🦆 DUCK COMMANDOS - IRA SNIPER MODE
import { KillConfirmationBanner } from './warroom/KillConfirmationBanner';
import { SniperLeaderboard } from './warroom/SniperLeaderboard';
import { DuckCommandoIntel } from './warroom/DuckCommandoIntel';

export default function WarRoomDashboard() {
  const { state, launchAssault, emergencyStop } = useQuantumWarRoom();
  const globalState = useGlobalState();

  // 🦆 DUCK COMMANDOS - Mock data for demo (replace with real data from hooks)
  const mockKill = null; // Set to actual kill data when a profitable SELL happens
  const mockSymbolStats = [
    { symbol: 'BTC/USD', totalKills: 156, totalPnl: 12.45, avgPnl: 0.08, quickKillRate: 0.94, avgBarsToProfit: 1.8, winRate: 0.98, byExchange: { kraken: { kills: 80, pnl: 6.4 }, binance: { kills: 76, pnl: 6.05 } } },
    { symbol: 'ETH/USD', totalKills: 142, totalPnl: 10.22, avgPnl: 0.07, quickKillRate: 0.91, avgBarsToProfit: 2.1, winRate: 0.96, byExchange: { kraken: { kills: 70, pnl: 5.1 }, alpaca: { kills: 72, pnl: 5.12 } } },
    { symbol: 'SOL/USD', totalKills: 98, totalPnl: 8.76, avgPnl: 0.09, quickKillRate: 0.96, avgBarsToProfit: 1.4, winRate: 0.99, byExchange: { binance: { kills: 98, pnl: 8.76 } } },
    { symbol: 'INJ/USD', totalKills: 87, totalPnl: 7.82, avgPnl: 0.09, quickKillRate: 0.98, avgBarsToProfit: 1.2, winRate: 0.99, byExchange: { kraken: { kills: 45, pnl: 4.05 }, capital: { kills: 42, pnl: 3.77 } } },
  ];
  const mockExchangeStatuses = [
    { exchange: 'kraken', connected: true, activePositions: 3, todayKills: 24, todayPnl: 2.45 },
    { exchange: 'binance', connected: true, activePositions: 5, todayKills: 31, todayPnl: 3.12 },
    { exchange: 'alpaca', connected: false, activePositions: 0, todayKills: 0, todayPnl: 0 },
    { exchange: 'capital', connected: true, activePositions: 2, todayKills: 18, todayPnl: 1.87 },
  ];

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

        {/* MAIN LAUNCH BUTTON */}
        <LaunchButton 
          onLaunch={launchAssault}
          onStop={emergencyStop}
          status={state.status}
        />

        {/* Trade Controls Header with Mode Toggle */}
        <TradeControlsHeader
          onLaunchAssault={launchAssault}
          onEmergencyStop={emergencyStop}
          status={state.status}
          tradesExecuted={state.tradesExecuted}
          netPnL={state.netPnL}
          currentBalance={state.currentBalance}
        />

        {/* Trading Status + Readiness */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <TradingStatusPanel />
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

        {/* Active Positions + Live Trade Stream */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ActivePositionsPanel />
          <LiveTradeStream />
        </div>

        {/* 🦆 DUCK COMMANDOS - IRA SNIPER MODE 🦆 */}
        <div className="space-y-4">
          {/* Kill Confirmation Banner (shows when a profitable SELL happens) */}
          {mockKill && <KillConfirmationBanner kill={mockKill} />}
          
          {/* Duck Intel + Sniper Leaderboard */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <DuckCommandoIntel exchangeStatuses={mockExchangeStatuses} showLore={true} />
            <SniperLeaderboard symbolStats={mockSymbolStats} sortBy="kills" maxDisplay={10} />
          </div>
        </div>

        {/* Live Strike Stream */}
        <LiveStrikeStream />

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
