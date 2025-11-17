import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { AlertTriangle, Shield, TrendingUp } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export const TradingConfig = () => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const { data, error } = await supabase
        .from('trading_config')
        .select('*')
        .single();

      if (error) throw error;
      setConfig(data);
    } catch (error) {
      console.error('Error loading config:', error);
      toast({
        title: 'Error',
        description: 'Failed to load trading configuration',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;

    try {
      const { error } = await supabase
        .from('trading_config')
        .update(config)
        .eq('id', config.id);

      if (error) throw error;

      toast({
        title: 'Configuration Saved',
        description: 'Trading settings updated successfully',
      });
    } catch (error) {
      console.error('Error saving config:', error);
      toast({
        title: 'Error',
        description: 'Failed to save configuration',
        variant: 'destructive',
      });
    }
  };

  if (loading || !config) {
    return <Card className="p-6"><p>Loading configuration...</p></Card>;
  }

  return (
    <Card className="p-6">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Automated Trading Configuration</h3>
            <p className="text-sm text-muted-foreground">
              Configure risk management and execution parameters
            </p>
          </div>
          <div className="flex items-center gap-4">
            {config.trading_mode === 'paper' ? (
              <Badge variant="outline"><Shield className="h-4 w-4 mr-2" />Paper Mode</Badge>
            ) : (
              <Badge variant="destructive"><AlertTriangle className="h-4 w-4 mr-2" />Live Mode</Badge>
            )}
          </div>
        </div>

        {/* Master Enable */}
        <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/50">
          <div>
            <Label htmlFor="enabled" className="text-base font-medium">
              Enable Automated Trading
            </Label>
            <p className="text-sm text-muted-foreground">
              {config.is_enabled ? 'System will execute trades on LHE signals' : 'Trading is paused'}
            </p>
          </div>
          <Switch
            id="enabled"
            checked={config.is_enabled}
            onCheckedChange={(checked) => setConfig({ ...config, is_enabled: checked })}
          />
        </div>

        {/* Trading Mode */}
        <div className="space-y-2">
          <Label htmlFor="mode">Trading Mode</Label>
          <Select
            value={config.trading_mode}
            onValueChange={(value) => setConfig({ ...config, trading_mode: value })}
          >
            <SelectTrigger id="mode">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="paper">Paper Trading (Simulated)</SelectItem>
              <SelectItem value="live">Live Trading (Real Money ⚠️)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Position Sizing */}
        <div className="space-y-4 border-t pt-4">
          <h4 className="font-medium flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Position Sizing
          </h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="base-size">Base Position Size (USDT)</Label>
              <Input
                id="base-size"
                type="number"
                value={config.base_position_size_usdt}
                onChange={(e) => setConfig({ ...config, base_position_size_usdt: parseFloat(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max-size">Max Position Size (USDT)</Label>
              <Input
                id="max-size"
                type="number"
                value={config.max_position_size_usdt}
                onChange={(e) => setConfig({ ...config, max_position_size_usdt: parseFloat(e.target.value) })}
              />
            </div>
          </div>
        </div>

        {/* Risk Management */}
        <div className="space-y-4 border-t pt-4">
          <h4 className="font-medium flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Risk Management
          </h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="stop-loss">Stop Loss (%)</Label>
              <Input
                id="stop-loss"
                type="number"
                step="0.1"
                value={config.stop_loss_percentage}
                onChange={(e) => setConfig({ ...config, stop_loss_percentage: parseFloat(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="take-profit">Take Profit (%)</Label>
              <Input
                id="take-profit"
                type="number"
                step="0.1"
                value={config.take_profit_percentage}
                onChange={(e) => setConfig({ ...config, take_profit_percentage: parseFloat(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max-loss">Max Daily Loss (USDT)</Label>
              <Input
                id="max-loss"
                type="number"
                value={config.max_daily_loss_usdt}
                onChange={(e) => setConfig({ ...config, max_daily_loss_usdt: parseFloat(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max-trades">Max Daily Trades</Label>
              <Input
                id="max-trades"
                type="number"
                value={config.max_daily_trades}
                onChange={(e) => setConfig({ ...config, max_daily_trades: parseInt(e.target.value) })}
              />
            </div>
          </div>
        </div>

        {/* Signal Filters */}
        <div className="space-y-4 border-t pt-4">
          <h4 className="font-medium">Signal Filters</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="min-coherence">Min Coherence (Γ)</Label>
              <Input
                id="min-coherence"
                type="number"
                step="0.001"
                value={config.min_coherence}
                onChange={(e) => setConfig({ ...config, min_coherence: parseFloat(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="min-confidence">Min Lighthouse Confidence</Label>
              <Input
                id="min-confidence"
                type="number"
                step="0.01"
                value={config.min_lighthouse_confidence}
                onChange={(e) => setConfig({ ...config, min_lighthouse_confidence: parseFloat(e.target.value) })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="min-prism">Min Prism Level</Label>
              <Input
                id="min-prism"
                type="number"
                min="1"
                max="5"
                value={config.min_prism_level}
                onChange={(e) => setConfig({ ...config, min_prism_level: parseInt(e.target.value) })}
              />
            </div>
            <div className="flex items-center space-x-2 pt-6">
              <Switch
                id="require-lhe"
                checked={config.require_lhe}
                onCheckedChange={(checked) => setConfig({ ...config, require_lhe: checked })}
              />
              <Label htmlFor="require-lhe">Require LHE</Label>
            </div>
          </div>
        </div>

        <Button onClick={saveConfig} className="w-full">
          Save Configuration
        </Button>

        {config.trading_mode === 'live' && (
          <div className="p-4 border border-destructive rounded-lg bg-destructive/10">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
              <div>
                <p className="font-medium text-destructive">Live Trading Warning</p>
                <p className="text-sm text-muted-foreground">
                  You are in LIVE trading mode. Real trades will be executed with real money.
                  Make sure your Binance API keys are configured correctly and start with small position sizes.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
