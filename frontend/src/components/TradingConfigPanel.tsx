import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "@/hooks/use-toast";
import { Settings, AlertTriangle, TrendingUp, Shield } from "lucide-react";

interface TradingConfig {
  tradingMode: 'paper' | 'live';
  minCoherence: number;
  maxPositions: number;
  autoTrading: boolean;
}

export const TradingConfigPanel = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<TradingConfig>({
    tradingMode: 'paper',
    minCoherence: 0.70,
    maxPositions: 15,
    autoTrading: false,
  });

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setLoading(false);
        return;
      }

      const { data, error } = await supabase
        .from('aureon_user_sessions')
        .select('trading_mode, is_trading_active')
        .eq('user_id', session.user.id)
        .single();

      if (data) {
        setConfig(prev => ({
          ...prev,
          tradingMode: (data.trading_mode as 'paper' | 'live') || 'paper',
          autoTrading: data.is_trading_active || false,
        }));
      }
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        toast({
          title: "Not authenticated",
          description: "Please log in to save settings",
          variant: "destructive",
        });
        return;
      }

      const { error } = await supabase
        .from('aureon_user_sessions')
        .update({
          trading_mode: config.tradingMode,
          is_trading_active: config.autoTrading,
          updated_at: new Date().toISOString(),
        })
        .eq('user_id', session.user.id);

      if (error) throw error;

      toast({
        title: "Settings saved",
        description: "Trading configuration updated successfully",
      });
    } catch (error) {
      console.error('Error saving config:', error);
      toast({
        title: "Error saving settings",
        description: "Please try again",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Trading Mode */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5 text-primary" />
            Trading Mode
          </CardTitle>
          <CardDescription>
            Choose between paper trading (simulation) or live trading with real funds
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base">
                {config.tradingMode === 'live' ? '🔴 Live Trading' : '📝 Paper Trading'}
              </Label>
              <p className="text-sm text-muted-foreground">
                {config.tradingMode === 'live' 
                  ? 'Trades will execute with real funds on connected exchanges'
                  : 'Trades are simulated - no real money at risk'}
              </p>
            </div>
            <Switch
              checked={config.tradingMode === 'live'}
              onCheckedChange={(checked) => 
                setConfig(prev => ({ ...prev, tradingMode: checked ? 'live' : 'paper' }))
              }
            />
          </div>
          
          {config.tradingMode === 'live' && (
            <div className="flex items-center gap-2 p-3 bg-destructive/10 rounded-md border border-destructive/20">
              <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0" />
              <p className="text-sm text-destructive">
                Live trading uses real funds. Ensure you understand the risks before enabling.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Coherence Threshold */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Settings className="h-5 w-5 text-primary" />
            Coherence Threshold
          </CardTitle>
          <CardDescription>
            Minimum coherence (Γ) required before executing trades
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Minimum Coherence: {config.minCoherence.toFixed(2)}</Label>
              <span className="text-sm text-muted-foreground">
                {config.minCoherence >= 0.90 ? 'Very Strict' : 
                 config.minCoherence >= 0.80 ? 'Strict' :
                 config.minCoherence >= 0.70 ? 'Moderate' : 'Relaxed'}
              </span>
            </div>
            <Slider
              value={[config.minCoherence]}
              min={0.50}
              max={0.99}
              step={0.01}
              onValueChange={([value]) => 
                setConfig(prev => ({ ...prev, minCoherence: value }))
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0.50 (More trades)</span>
              <span>0.99 (Fewer, higher quality)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Management */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Shield className="h-5 w-5 text-primary" />
            Risk Management
          </CardTitle>
          <CardDescription>
            Configure position limits and risk controls
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="maxPositions">Maximum Concurrent Positions</Label>
            <Input
              id="maxPositions"
              type="number"
              min={1}
              max={50}
              value={config.maxPositions}
              onChange={(e) => 
                setConfig(prev => ({ 
                  ...prev, 
                  maxPositions: Math.min(50, Math.max(1, parseInt(e.target.value) || 1))
                }))
              }
              className="max-w-[120px]"
            />
            <p className="text-sm text-muted-foreground">
              Limit the number of open positions at any time (1-50)
            </p>
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="space-y-0.5">
              <Label className="text-base">Auto-Trading</Label>
              <p className="text-sm text-muted-foreground">
                Automatically execute trades when signals are detected
              </p>
            </div>
            <Switch
              checked={config.autoTrading}
              onCheckedChange={(checked) => 
                setConfig(prev => ({ ...prev, autoTrading: checked }))
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={saveConfig} disabled={saving}>
          {saving ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>
    </div>
  );
};
