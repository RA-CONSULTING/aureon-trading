import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Bell, BellOff, Mail, Volume2, VolumeX, RotateCcw } from 'lucide-react';

interface AlertConfig {
  enabled: boolean;
  notifyOnDegraded: boolean;
  notifyOnUnhealthy: boolean;
  emailNotifications: boolean;
  soundAlerts: boolean;
  minTimeBetweenAlerts: number;
}

interface HealthAlertSettingsProps {
  config: AlertConfig;
  onConfigChange: (updates: Partial<AlertConfig>) => void;
  onClearHistory: () => void;
}

export function HealthAlertSettings({ 
  config, 
  onConfigChange, 
  onClearHistory 
}: HealthAlertSettingsProps) {
  const handleMinTimeChange = (value: number[]) => {
    onConfigChange({ minTimeBetweenAlerts: value[0] * 60000 }); // Convert minutes to ms
  };

  return (
    <Card className="p-6 bg-card/50 backdrop-blur border-primary/20">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          {config.enabled ? (
            <Bell className="h-5 w-5 text-primary" />
          ) : (
            <BellOff className="h-5 w-5 text-muted-foreground" />
          )}
          <h3 className="text-lg font-semibold">Health Alert Settings</h3>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onClearHistory}
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          Clear History
        </Button>
      </div>

      <div className="space-y-6">
        {/* Master Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Enable Alerts</Label>
            <p className="text-sm text-muted-foreground">
              Turn health monitoring alerts on or off
            </p>
          </div>
          <Switch
            checked={config.enabled}
            onCheckedChange={(checked) => onConfigChange({ enabled: checked })}
          />
        </div>

        {config.enabled && (
          <>
            {/* Alert Levels */}
            <div className="space-y-4 pt-4 border-t">
              <Label className="text-base">Alert Triggers</Label>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-sm font-normal">Degraded Status</Label>
                  <p className="text-xs text-muted-foreground">
                    Notify when system performance degrades
                  </p>
                </div>
                <Switch
                  checked={config.notifyOnDegraded}
                  onCheckedChange={(checked) => onConfigChange({ notifyOnDegraded: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-sm font-normal">Unhealthy Status</Label>
                  <p className="text-xs text-muted-foreground">
                    Notify when critical issues are detected
                  </p>
                </div>
                <Switch
                  checked={config.notifyOnUnhealthy}
                  onCheckedChange={(checked) => onConfigChange({ notifyOnUnhealthy: checked })}
                />
              </div>
            </div>

            {/* Notification Methods */}
            <div className="space-y-4 pt-4 border-t">
              <Label className="text-base">Notification Methods</Label>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5 flex items-center gap-2">
                  {config.soundAlerts ? (
                    <Volume2 className="h-4 w-4" />
                  ) : (
                    <VolumeX className="h-4 w-4 text-muted-foreground" />
                  )}
                  <div>
                    <Label className="text-sm font-normal">Sound Alerts</Label>
                    <p className="text-xs text-muted-foreground">
                      Play audio notification on alerts
                    </p>
                  </div>
                </div>
                <Switch
                  checked={config.soundAlerts}
                  onCheckedChange={(checked) => onConfigChange({ soundAlerts: checked })}
                />
              </div>

              <div className="flex items-center justify-between opacity-50">
                <div className="space-y-0.5 flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  <div>
                    <Label className="text-sm font-normal">Email Notifications</Label>
                    <p className="text-xs text-muted-foreground">
                      Send email alerts (Coming soon)
                    </p>
                  </div>
                </div>
                <Switch
                  disabled
                  checked={config.emailNotifications}
                  onCheckedChange={(checked) => onConfigChange({ emailNotifications: checked })}
                />
              </div>
            </div>

            {/* Alert Frequency */}
            <div className="space-y-4 pt-4 border-t">
              <div className="space-y-2">
                <Label className="text-base">Alert Frequency</Label>
                <p className="text-sm text-muted-foreground">
                  Minimum time between similar alerts: {Math.round(config.minTimeBetweenAlerts / 60000)} minutes
                </p>
                <Slider
                  value={[config.minTimeBetweenAlerts / 60000]}
                  onValueChange={handleMinTimeChange}
                  min={1}
                  max={60}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>1 min</span>
                  <span>60 min</span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
