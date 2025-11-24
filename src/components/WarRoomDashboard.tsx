import { useWarRoom } from '@/hooks/useWarRoom';
import { useStrikeFeed } from '@/hooks/useStrikeFeed';
import { useWarMetrics } from '@/hooks/useWarMetrics';
import { CommandCenter } from './warroom/CommandCenter';
import { BattleMap } from './warroom/BattleMap';
import { StrikeFeed } from './warroom/StrikeFeed';
import { MetricsHQ } from './warroom/MetricsHQ';
import { AurisNodesPanel } from './warroom/AurisNodesPanel';

export default function WarRoomDashboard() {
  const warRoom = useWarRoom();
  const strikeFeed = useStrikeFeed();
  const { metrics } = useWarMetrics(warRoom.totals.totalUSDValue);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-destructive/5">
      <div className="container mx-auto p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-destructive via-primary to-destructive bg-clip-text text-transparent">
              🔥 TOTAL WAR COMMAND CENTER
            </h1>
            <p className="text-muted-foreground mt-1">
              GENERAL QUACKERS: MAXIMUM AGGRESSION MODE
            </p>
          </div>
        </div>

        {/* Command Center */}
        <CommandCenter 
          warState={warRoom.warState}
          onLaunch={warRoom.launchWar}
          onPause={warRoom.pauseWar}
          onResume={warRoom.resumeWar}
          onStop={warRoom.stopWar}
          onEmergencyHalt={warRoom.emergencyHalt}
          onConfigUpdate={warRoom.updateConfig}
        />

        {/* Metrics HQ */}
        <MetricsHQ 
          metrics={metrics}
          totals={warRoom.totals}
          isScanning={warRoom.isScanning}
        />

        {/* Main Grid - Battle Map & Strike Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BattleMap 
            opportunities={warRoom.opportunities}
            accounts={warRoom.accounts}
          />
          <StrikeFeed 
            events={strikeFeed.events}
            executionCount={strikeFeed.executionCount}
            onClear={strikeFeed.clearEvents}
          />
        </div>

        {/* Auris Nodes Panel */}
        <AurisNodesPanel 
          coherence={metrics.currentCoherence}
          lighthouse={metrics.currentLighthouse}
        />
      </div>
    </div>
  );
}
