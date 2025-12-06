import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Flame, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { forceValidatedTrade, ForceTradeResult } from '@/core/forceValidatedTrade';
import { useToast } from '@/hooks/use-toast';

interface IgnitionButtonProps {
  userId: string;
  tradingMode: 'paper' | 'live';
  onComplete?: (result: ForceTradeResult) => void;
  disabled?: boolean;
}

export function IgnitionButton({ userId, tradingMode, onComplete, disabled }: IgnitionButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<ForceTradeResult | null>(null);
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const { toast } = useToast();

  const handleIgnition = async () => {
    setShowConfirm(false);
    setIsRunning(true);
    setResult(null);

    try {
      const tradeResult = await forceValidatedTrade(userId, symbol, side, tradingMode);
      setResult(tradeResult);
      
      if (tradeResult.success) {
        toast({
          title: '🔥 Cycle 1 Complete',
          description: 'All 10 validation steps passed successfully!',
        });
      } else {
        toast({
          title: '❌ Validation Failed',
          description: tradeResult.message,
          variant: 'destructive',
        });
      }

      onComplete?.(tradeResult);
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to execute forced validation',
        variant: 'destructive',
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <>
      <Button
        onClick={() => setShowConfirm(true)}
        disabled={disabled || isRunning}
        variant="destructive"
        size="lg"
        className="gap-2 font-bold"
      >
        {isRunning ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            VALIDATING...
          </>
        ) : result?.success ? (
          <>
            <CheckCircle2 className="h-5 w-5" />
            CYCLE 1 ✓
          </>
        ) : result && !result.success ? (
          <>
            <XCircle className="h-5 w-5" />
            RETRY IGNITION
          </>
        ) : (
          <>
            <Flame className="h-5 w-5" />
            FORCE CYCLE 1 TRADE
          </>
        )}
      </Button>

      <Dialog open={showConfirm} onOpenChange={setShowConfirm}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-destructive" />
              Force Validated Trade
            </DialogTitle>
            <DialogDescription>
              This will execute 1 fully validated trade through all 10 system steps to prove the cycle works.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium w-20">Symbol:</label>
              <Select value={symbol} onValueChange={setSymbol}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BTCUSDT">BTCUSDT</SelectItem>
                  <SelectItem value="ETHUSDT">ETHUSDT</SelectItem>
                  <SelectItem value="SOLUSDT">SOLUSDT</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-4">
              <label className="text-sm font-medium w-20">Side:</label>
              <Select value={side} onValueChange={(v) => setSide(v as 'BUY' | 'SELL')}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BUY">BUY</SelectItem>
                  <SelectItem value="SELL">SELL</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className={`p-3 rounded-lg ${tradingMode === 'live' ? 'bg-destructive/10 border border-destructive' : 'bg-muted'}`}>
              <p className="text-sm font-medium">
                Mode: <span className={tradingMode === 'live' ? 'text-destructive' : 'text-muted-foreground'}>
                  {tradingMode === 'live' ? '🔴 LIVE (Simulated for safety)' : '📝 PAPER'}
                </span>
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {tradingMode === 'live' 
                  ? 'Live mode runs full validation but simulates execution for safety during forced tests.'
                  : 'Paper mode simulates the entire trade without real funds.'}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirm(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleIgnition} className="gap-2">
              <Flame className="h-4 w-4" />
              Execute Cycle 1
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
