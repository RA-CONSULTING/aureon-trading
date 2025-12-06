import { useState, useEffect } from 'react';
import { dataStreamMonitor, DataStreamMonitorState } from '@/core/dataStreamMonitor';

export function useDataStreamMonitor() {
  const [state, setState] = useState<DataStreamMonitorState>(dataStreamMonitor.getState());

  useEffect(() => {
    const unsubscribe = dataStreamMonitor.subscribe(setState);
    return unsubscribe;
  }, []);

  return {
    streams: state.streams,
    stats: state.stats,
    totalRequests: state.totalRequests,
    totalErrors: state.totalErrors,
    overallHealth: state.overallHealth,
    lastUpdate: state.lastUpdate,
    healthyEndpoints: dataStreamMonitor.getHealthyEndpoints(),
    unhealthyEndpoints: dataStreamMonitor.getUnhealthyEndpoints(),
    clearHistory: () => dataStreamMonitor.clearHistory(),
  };
}
