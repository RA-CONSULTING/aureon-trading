interface NewsEmotionData {
  id: string;
  title: string;
  sourceId: string;
  sourceName: string;
  region: string;
  timestamp: number;
  valence: number;
  arousal: number;
  isNegative: boolean;
}

interface StationStats {
  sourceId: string;
  sourceName: string;
  region: string;
  total24h: number;
  negative24h: number;
  negShare24h: number;
}

interface RegionStats {
  region: string;
  total24h: number;
  negative24h: number;
  negShare24h: number;
  topStation: string;
}

class NewsEmotionStore {
  private data: NewsEmotionData[] = [];
  private listeners: Set<() => void> = new Set();

  addBatch(items: NewsEmotionData[]) {
    this.data.push(...items);
    this.cleanup24h();
    this.notifyListeners();
  }

  private cleanup24h() {
    const cutoff = Date.now() - 24 * 60 * 60 * 1000;
    this.data = this.data.filter(item => item.timestamp >= cutoff);
  }

  getStationStats(): StationStats[] {
    const stats = new Map<string, StationStats>();
    
    for (const item of this.data) {
      const key = item.sourceId;
      if (!stats.has(key)) {
        stats.set(key, {
          sourceId: item.sourceId,
          sourceName: item.sourceName,
          region: item.region,
          total24h: 0,
          negative24h: 0,
          negShare24h: 0
        });
      }
      const stat = stats.get(key)!;
      stat.total24h++;
      if (item.isNegative) stat.negative24h++;
    }

    const result = Array.from(stats.values());
    result.forEach(s => s.negShare24h = s.total24h > 0 ? s.negative24h / s.total24h : 0);
    return result.sort((a, b) => b.negShare24h - a.negShare24h || b.total24h - a.total24h);
  }

  getRegionStats(): RegionStats[] {
    const stats = new Map<string, RegionStats>();
    
    for (const item of this.data) {
      if (!stats.has(item.region)) {
        stats.set(item.region, {
          region: item.region,
          total24h: 0,
          negative24h: 0,
          negShare24h: 0,
          topStation: ''
        });
      }
      const stat = stats.get(item.region)!;
      stat.total24h++;
      if (item.isNegative) stat.negative24h++;
    }

    const result = Array.from(stats.values());
    result.forEach(s => {
      s.negShare24h = s.total24h > 0 ? s.negative24h / s.total24h : 0;
      const stationStats = this.getStationStats().filter(st => st.region === s.region);
      s.topStation = stationStats[0]?.sourceName || '';
    });
    
    return result.sort((a, b) => b.negShare24h - a.negShare24h);
  }

  subscribe(callback: () => void) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  private notifyListeners() {
    this.listeners.forEach(callback => callback());
  }
}

export const newsEmotionStore = new NewsEmotionStore();
export type { NewsEmotionData, StationStats, RegionStats };