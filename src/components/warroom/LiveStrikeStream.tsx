import { useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useStrikeFeed } from '@/hooks/useStrikeFeed';
import { Activity, Zap, AlertCircle } from 'lucide-react';

export function LiveStrikeStream() {
  const { events } = useStrikeFeed();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const recentEvents = events.slice(-50);

  return (
    <Card className="bg-black/40 border-border/30 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-muted-foreground">Live Strike Feed</h3>
        <Badge variant="outline" className="animate-pulse">
          <Activity className="w-3 h-3 mr-1" />
          {events.length} events
        </Badge>
      </div>
      
      <div
        ref={scrollRef}
        className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-purple-500/30 scrollbar-track-transparent"
      >
        {recentEvents.map((event) => (
          <div
            key={event.id}
            className="flex items-center gap-3 p-2 bg-black/30 rounded border border-border/20 animate-slide-in-right"
          >
            <EventIcon type={event.type} status={event.status} />
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-sm font-mono">{event.symbol}</span>
                {event.side && (
                  <Badge
                    variant={event.side === 'BUY' ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    {event.side}
                  </Badge>
                )}
              </div>
              {event.message && (
                <div className="text-xs text-muted-foreground truncate">
                  {event.message}
                </div>
              )}
            </div>

            {event.pnl !== undefined && (
              <div className={`text-sm font-bold ${event.pnl > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {event.pnl > 0 ? '+' : ''}{event.pnl.toFixed(2)}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

interface EventIconProps {
  type: string;
  status?: string;
}

function EventIcon({ type, status }: EventIconProps) {
  if (type === 'lhe') {
    return <Zap className="w-4 h-4 text-yellow-400 animate-pulse" />;
  }

  if (status === 'error') {
    return <AlertCircle className="w-4 h-4 text-red-400" />;
  }

  if (status === 'success') {
    return <Activity className="w-4 h-4 text-green-400" />;
  }

  return <Activity className="w-4 h-4 text-cyan-400" />;
}
