import { useEffect, useState } from 'react';
import { newsEmotionStore, type StationStats, type RegionStats } from '../state/newsEmotionStore';

export function useNewsEmotion() {
  const [stationStats, setStationStats] = useState<StationStats[]>([]);
  const [regionStats, setRegionStats] = useState<RegionStats[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    const updateStats = () => {
      setStationStats(newsEmotionStore.getStationStats());
      setRegionStats(newsEmotionStore.getRegionStats());
      setLastUpdate(new Date());
    };

    // Initial load
    updateStats();

    // Subscribe to updates
    const unsubscribe = newsEmotionStore.subscribe(updateStats);

    return unsubscribe;
  }, []);

  return {
    stationStats,
    regionStats,
    lastUpdate
  };
}