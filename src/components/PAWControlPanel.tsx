import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { PAWAPIDriver } from '../lib/paw-api-driver-complete';
import { Telemetry, Element, Voxel } from '../types/paw-types';

const pawDriver = new PAWAPIDriver();

export const PAWControlPanel: React.FC = () => {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [status, setStatus] = useState<string>('Offline');
  const [profile, setProfile] = useState('Standard');
  const [balanceB, setBalanceB] = useState(1.2);
  const [interlocks, setInterlocks] = useState(true);
  const [fluxIps, setFluxIps] = useState(1e5);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    if (isRunning) {
      const interval = setInterval(() => {
        const tel = pawDriver.GetTelemetry();
        setTelemetry(tel);
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isRunning]);

  const handleInit = () => {
    const [success, msg] = pawDriver.Init(profile);
    setStatus(success ? 'Initialized' : 'Error');
    if (success) setIsRunning(true);
  };

  const handleArm = () => {
    const [success, msg] = pawDriver.Arm(balanceB, interlocks);
    setStatus(success ? 'Armed' : msg);
  };

  const handleInject = () => {
    const elem: Element = { symbol: 'C', Z: 6, A: 12 };
    const [success, msg] = pawDriver.Inject(elem, fluxIps);
    setStatus(msg);
  };

  const handlePlace = () => {
    const voxel: Voxel = { i: 10, j: 10, k: 10 };
    const elem: Element = { symbol: 'C', Z: 6, A: 12 };
    const result = pawDriver.Place(voxel, elem, 100, 5);
    setStatus(result.msg);
  };

  const getStatusColor = () => {
    if (telemetry?.class3) return 'destructive';
    if (telemetry?.class2) return 'secondary';
    return 'default';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>PAW Control System</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="profile">Profile</Label>
              <Input
                id="profile"
                value={profile}
                onChange={(e) => setProfile(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="balance">Balance B</Label>
              <Input
                id="balance"
                type="number"
                step="0.1"
                value={balanceB}
                onChange={(e) => setBalanceB(parseFloat(e.target.value))}
              />
            </div>
          </div>
          
          <div>
            <Label htmlFor="flux">Flux (ips)</Label>
            <Input
              id="flux"
              type="number"
              value={fluxIps}
              onChange={(e) => setFluxIps(parseFloat(e.target.value))}
            />
          </div>

          <div className="flex gap-2 flex-wrap">
            <Button onClick={handleInit} variant="outline">Initialize</Button>
            <Button onClick={handleArm} variant="outline">Arm</Button>
            <Button onClick={handleInject} variant="outline">Inject</Button>
            <Button onClick={handlePlace} variant="default">Place</Button>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant={getStatusColor()}>{status}</Badge>
            {telemetry?.interlocks_ok && <Badge variant="outline">Interlocks OK</Badge>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};