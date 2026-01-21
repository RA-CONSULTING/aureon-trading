import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { Telemetry } from '../types/paw-types';

interface PAWTelemetryDisplayProps {
  telemetry: Telemetry | null;
}

export const PAWTelemetryDisplay: React.FC<PAWTelemetryDisplayProps> = ({ telemetry }) => {
  if (!telemetry) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Telemetry</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No telemetry data available</p>
        </CardContent>
      </Card>
    );
  }

  const errorPercent = Math.min((telemetry.error_pm / 200) * 100, 100);
  const tempPercent = Math.min(((telemetry.temp_K - 1.5) / 2.5) * 100, 100);
  const fluxPercent = Math.min((telemetry.flux_ips / 2e6) * 100, 100);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Telemetry
          <div className="flex gap-2">
            {telemetry.class3 && <Badge variant="destructive">Class 3</Badge>}
            {telemetry.class2 && <Badge variant="secondary">Class 2</Badge>}
            {!telemetry.class2 && !telemetry.class3 && <Badge variant="outline">Normal</Badge>}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {(telemetry.class2 || telemetry.class3) && (
          <Alert variant={telemetry.class3 ? "destructive" : "default"}>
            <AlertDescription>
              {telemetry.class3 
                ? "Class 3 Safety Violation - Critical error levels detected"
                : "Class 2 Warning - Elevated error levels detected"
              }
            </AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium">Placement Error</span>
              <span className="text-sm text-muted-foreground">{telemetry.error_pm.toFixed(1)} pm</span>
            </div>
            <Progress value={errorPercent} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium">Temperature</span>
              <span className="text-sm text-muted-foreground">{telemetry.temp_K.toFixed(2)} K</span>
            </div>
            <Progress value={tempPercent} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium">Ion Flux</span>
              <span className="text-sm text-muted-foreground">{telemetry.flux_ips.toExponential(1)} ips</span>
            </div>
            <Progress value={fluxPercent} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium">Energy/Atom</span>
              <span className="text-sm text-muted-foreground">{telemetry.epa_eV.toFixed(2)} eV</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium">Balance B</span>
              <span className="text-sm text-muted-foreground">{telemetry.balance_B.toFixed(2)}</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium">Interlocks</span>
              <Badge variant={telemetry.interlocks_ok ? "outline" : "destructive"}>
                {telemetry.interlocks_ok ? "OK" : "FAULT"}
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PAWTelemetryDisplay;