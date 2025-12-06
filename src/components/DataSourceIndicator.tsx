import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Wifi, Radio, WifiOff, AlertTriangle } from 'lucide-react';
import { useExchangeDataVerification } from '@/hooks/useExchangeDataVerification';

interface DataSourceIndicatorProps {
  compact?: boolean;
  showDetails?: boolean;
}

/**
 * DATA SOURCE INDICATOR
 * 
 * Shows whether the system is receiving LIVE or DEMO data
 * Prominently displays warning when running on simulated data
 */
export const DataSourceIndicator: React.FC<DataSourceIndicatorProps> = ({
  compact = false,
  showDetails = true,
}) => {
  const { 
    verification, 
    isLiveData, 
    isDemoMode, 
    liveExchangeCount, 
    totalExchangeCount,
    isLoading 
  } = useExchangeDataVerification();

  if (isLoading && !verification) {
    return (
      <Badge variant="outline" className="animate-pulse">
        <Wifi className="h-3 w-3 mr-1" />
        Checking...
      </Badge>
    );
  }

  if (isLiveData) {
    return (
      <Badge className="bg-green-500/20 text-green-400 border-green-500/50">
        <Wifi className="h-3 w-3 mr-1" />
        {compact ? 'LIVE' : 'LIVE DATA'}
        {showDetails && !compact && (
          <span className="ml-1 text-green-300">
            ({liveExchangeCount}/{totalExchangeCount})
          </span>
        )}
      </Badge>
    );
  }

  if (isDemoMode) {
    return (
      <div className="flex items-center gap-2">
        <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/50 animate-pulse">
          <Radio className="h-3 w-3 mr-1 animate-pulse" />
          {compact ? '⚠️ DEMO' : '⚠️ SIMULATED DATA'}
        </Badge>
        {!compact && (
          <span className="text-xs text-yellow-500 animate-pulse">
            Not real trading data!
          </span>
        )}
      </div>
    );
  }

  if (verification?.overallStatus === 'PARTIAL_LIVE') {
    return (
      <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/50">
        <AlertTriangle className="h-3 w-3 mr-1" />
        {compact ? 'PARTIAL' : 'PARTIAL LIVE'}
        {showDetails && !compact && (
          <span className="ml-1 text-orange-300">
            ({liveExchangeCount}/{totalExchangeCount})
          </span>
        )}
      </Badge>
    );
  }

  return (
    <Badge variant="destructive">
      <WifiOff className="h-3 w-3 mr-1" />
      {compact ? 'OFFLINE' : 'NO DATA'}
    </Badge>
  );
};

/**
 * Prominent demo mode warning banner
 */
export const DemoModeWarningBanner: React.FC = () => {
  const { isDemoMode, hasGhostData } = useExchangeDataVerification();

  if (!isDemoMode && !hasGhostData) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-500/90 text-black px-4 py-2 text-center">
      <div className="flex items-center justify-center gap-2">
        <Radio className="h-4 w-4 animate-pulse" />
        <span className="font-bold">
          ⚠️ DEMO MODE - SIMULATED DATA ONLY - NOT CONNECTED TO REAL EXCHANGES ⚠️
        </span>
        <Radio className="h-4 w-4 animate-pulse" />
      </div>
    </div>
  );
};
