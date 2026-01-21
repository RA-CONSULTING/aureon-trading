import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';

export type QuantumPhaseLockProps = {
  /** Whether the PLL-like lock is engaged */
  locked?: boolean;
  /** Callback when user toggles lock */
  onToggle?: (locked: boolean) => void;
  /** Carrier / reference frequency (Hz) for display only */
  frequencyHz?: number;
  /** Relative phase (degrees) for display only */
  phaseDeg?: number;
  className?: string;
};

/**
 * QuantumPhaseLock
 * A tiny, presentational widget that shows a lock state with optional frequency & phase readouts.
 *
 * This component provides BOTH a named export (QuantumPhaseLock) and a default export
 * so it can be imported as either:
 *   import { QuantumPhaseLock } from './QuantumPhaseLock';
 * or
 *   import QuantumPhaseLock from './QuantumPhaseLock';
 */
export function QuantumPhaseLock({
  locked = false,
  onToggle,
  frequencyHz,
  phaseDeg,
  className,
}: QuantumPhaseLockProps) {
  const freq = typeof frequencyHz === 'number' ? `${frequencyHz.toLocaleString()} Hz` : '—';
  const phase = typeof phaseDeg === 'number' ? `${phaseDeg.toFixed(2)}°` : '—';

  return (
    <Card className={cn('w-full rounded-2xl', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold">Quantum Phase Lock</CardTitle>
        <div className="flex items-center gap-3">
          <Badge variant={locked ? 'default' : 'secondary'} className="text-xs">
            {locked ? 'Locked' : 'Unlocked'}
          </Badge>
          <Switch
            checked={locked}
            onCheckedChange={(val) => onToggle?.(val)}
            aria-label="Toggle quantum phase lock"
          />
        </div>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <div className="text-sm text-muted-foreground">Reference Frequency</div>
          <div className="text-base font-medium">{freq}</div>
        </div>
        <div className="space-y-1">
          <div className="text-sm text-muted-foreground">Relative Phase</div>
          <div className="text-base font-medium">{phase}</div>
        </div>
      </CardContent>
    </Card>
  );
}

export default QuantumPhaseLock;