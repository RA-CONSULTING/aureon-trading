import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNewsEmotion } from '@/hooks/useNewsEmotion';
import { TrendingDown, Globe, Radio } from 'lucide-react';

export default function NewsEmotionDashboard() {
  const { stationStats, regionStats, lastUpdate } = useNewsEmotion();

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;
  
  const getMoodColor = (negShare: number) => {
    if (negShare > 0.6) return 'text-red-500';
    if (negShare > 0.4) return 'text-orange-500';
    if (negShare > 0.2) return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700 text-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingDown className="w-5 h-5 text-red-400" />
          Live News Emotion Monitor
        </CardTitle>
        <p className="text-sm text-slate-400">
          Last updated: {lastUpdate.toLocaleTimeString()} • 24h sliding window
        </p>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="stations" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-slate-800">
            <TabsTrigger value="stations" className="flex items-center gap-2">
              <Radio className="w-4 h-4" />
              By Station
            </TabsTrigger>
            <TabsTrigger value="regions" className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              By Region
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="stations" className="space-y-3">
            {stationStats.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <p>Waiting for news data...</p>
                <p className="text-xs mt-2">Configure VITE_NEWS_PROXY_URL or VITE_GNEWS_API_KEY in .env</p>
              </div>
            ) : (
              stationStats.slice(0, 10).map((station, i) => (
                <div key={station.sourceId} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-xs">#{i + 1}</Badge>
                    <div>
                      <div className="font-medium">{station.sourceName}</div>
                      <div className="text-xs text-slate-400">{station.region}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${getMoodColor(station.negShare24h)}`}>
                      {formatPercent(station.negShare24h)}
                    </div>
                    <div className="text-xs text-slate-400">
                      {station.negative24h}/{station.total24h} articles
                    </div>
                  </div>
                </div>
              ))
            )}
          </TabsContent>
          
          <TabsContent value="regions" className="space-y-3">
            {regionStats.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <p>Waiting for regional data...</p>
              </div>
            ) : (
              regionStats.map((region, i) => (
                <div key={region.region} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-xs">#{i + 1}</Badge>
                    <div>
                      <div className="font-medium">{region.region}</div>
                      <div className="text-xs text-slate-400">Top: {region.topStation}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${getMoodColor(region.negShare24h)}`}>
                      {formatPercent(region.negShare24h)}
                    </div>
                    <div className="text-xs text-slate-400">
                      {region.negative24h}/{region.total24h} articles
                    </div>
                  </div>
                </div>
              ))
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}