import { useState } from 'react';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { AlertTriangle, Play, TestTube } from 'lucide-react';

interface TradingModeToggleProps {
  isLive: boolean;
  onModeChange: (isLive: boolean) => void;
  disabled?: boolean;
}

export function TradingModeToggle({ isLive, onModeChange, disabled }: TradingModeToggleProps) {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingMode, setPendingMode] = useState<boolean | null>(null);

  const handleToggle = (checked: boolean) => {
    if (checked) {
      // Switching to LIVE mode requires confirmation
      setPendingMode(true);
      setShowConfirmDialog(true);
    } else {
      // Switching to paper mode is immediate
      onModeChange(false);
    }
  };

  const handleConfirmLive = () => {
    if (pendingMode !== null) {
      onModeChange(pendingMode);
    }
    setShowConfirmDialog(false);
    setPendingMode(null);
  };

  const handleCancel = () => {
    setShowConfirmDialog(false);
    setPendingMode(null);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <Badge 
          variant={isLive ? "destructive" : "secondary"} 
          className="gap-1 text-xs"
        >
          {isLive ? (
            <>
              <Play className="h-3 w-3" />
              LIVE
            </>
          ) : (
            <>
              <TestTube className="h-3 w-3" />
              PAPER
            </>
          )}
        </Badge>
        <Switch
          checked={isLive}
          onCheckedChange={handleToggle}
          disabled={disabled}
          className="data-[state=checked]:bg-destructive"
        />
      </div>

      <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <AlertDialogContent className="border-destructive/50">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Enable LIVE Trading?
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-3">
              <p>
                You are about to enable <strong>LIVE trading mode</strong>. This will execute 
                real trades on your connected Binance account using real funds.
              </p>
              <div className="bg-destructive/10 border border-destructive/30 rounded-md p-3 text-sm">
                <ul className="list-disc list-inside space-y-1 text-foreground">
                  <li>Real money will be used for all trades</li>
                  <li>Losses are permanent and irreversible</li>
                  <li>Trading fees will be charged by the exchange</li>
                  <li>Market volatility can cause rapid losses</li>
                </ul>
              </div>
              <p className="text-muted-foreground text-sm">
                Only enable live trading if you understand the risks and have verified 
                your strategy with paper trading first.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancel}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmLive}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              I Understand, Enable LIVE Trading
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}