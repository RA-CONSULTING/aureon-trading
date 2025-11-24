/**
 * HNC Score Card Component
 * -----------------------
 * Displays the Harmonic Nexus Core coherence score,
 * band analysis, and top narrative drivers.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { HNCRegionTick } from "@/core/harmonicNexusCore";

interface HNCScoreCardProps {
  tick?: HNCRegionTick;
  className?: string;
}

export function HNCScoreCard({ tick, className }: HNCScoreCardProps) {
  if (!tick) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-sm">HNC Coherence</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">No data</div>
        </CardContent>
      </Card>
    );
  }

  const { score, byBand, drivers } = tick;

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center justify-between">
          HNC Coherence
          <Badge variant={score > 75 ? "default" : score > 50 ? "secondary" : "destructive"}>
            {score}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Band Analysis */}
        <div className="space-y-2">
          <div className="text-xs font-medium">Band Coherence</div>
          {Object.entries(byBand).map(([band, value]) => (
            <div key={band} className="flex items-center gap-2">
              <span className="text-xs w-12">{band}Hz</span>
              <Progress value={value * 100} className="h-1 flex-1" />
              <span className="text-xs text-muted-foreground w-8">
                {Math.round(value * 100)}%
              </span>
            </div>
          ))}
        </div>

        {/* Top Drivers */}
        <div className="space-y-2">
          <div className="text-xs font-medium">Top Drivers</div>
          <div className="flex flex-wrap gap-1">
            {drivers.slice(0, 3).map((driver, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                {driver.label} ({Math.round(driver.weight * 100)}%)
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}