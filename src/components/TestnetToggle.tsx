import { Card } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useBinanceCredentials } from '@/hooks/useBinanceCredentials';
import { Shield, AlertTriangle } from 'lucide-react';

export const TestnetToggle = () => {
  const { useTestnet, setUseTestnet } = useBinanceCredentials();

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Label htmlFor="testnet-mode" className="text-base font-semibold">
              Trading Environment
            </Label>
            {useTestnet ? (
              <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                <Shield className="h-3 w-3 mr-1" />
                TESTNET (SAFE)
              </Badge>
            ) : (
              <Badge variant="destructive">
                <AlertTriangle className="h-3 w-3 mr-1" />
                MAINNET (REAL MONEY)
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {useTestnet 
              ? 'Using Binance Testnet for risk-free testing with simulated funds'
              : 'Using Binance Mainnet - trades execute with real money!'
            }
          </p>
        </div>
        <Switch
          id="testnet-mode"
          checked={useTestnet}
          onCheckedChange={setUseTestnet}
        />
      </div>
      
      {!useTestnet && (
        <div className="mt-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
          <p className="text-sm text-destructive font-medium">
            ⚠️ Warning: Mainnet mode will execute real trades with real money. 
            Make sure you've tested thoroughly on testnet first!
          </p>
        </div>
      )}
    </Card>
  );
};
