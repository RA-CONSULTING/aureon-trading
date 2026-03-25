import { Card } from '@/components/ui/card';
import { useGlobalState } from '@/hooks/useGlobalState';
import { cn } from '@/lib/utils';

const safeNumber = (value: unknown, fallback = 0): number => {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
};

const formatSigned = (value: unknown, digits = 2, prefix = '') => {
  const num = safeNumber(value);
  const sign = num >= 0 ? '+' : '';
  return `${prefix}${sign}${num.toFixed(digits)}`;
};

const ExchangeMetric = ({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) => (
  <div className="flex items-center justify-between gap-3 text-[11px] font-mono">
    <span className="text-muted-foreground">{label}</span>
    <span className={cn('text-foreground', className)}>{value}</span>
  </div>
);

const PositionLine = ({
  symbol,
  side,
  entryPrice,
  currentPrice,
  pnlPercent,
  exchange,
}: {
  symbol: string;
  side: 'LONG' | 'SHORT';
  entryPrice: number;
  currentPrice: number;
  pnlPercent: number;
  exchange?: string;
}) => (
  <div className="rounded border border-border/40 bg-background/60 px-3 py-2">
    <div className="flex items-center justify-between gap-3 font-mono text-[11px]">
      <div className="flex items-center gap-2">
        <span className="font-semibold text-foreground">{symbol}</span>
        <span className={cn('text-[10px]', side === 'LONG' ? 'text-green-500' : 'text-red-500')}>
          {side}
        </span>
        {exchange && <span className="text-[10px] uppercase text-muted-foreground">{exchange}</span>}
      </div>
      <span className={cn(pnlPercent >= 0 ? 'text-green-500' : 'text-red-500')}>
        {formatSigned(pnlPercent, 2)}%
      </span>
    </div>
    <div className="mt-1 flex items-center gap-3 font-mono text-[10px] text-muted-foreground">
      <span>Entry ${entryPrice.toFixed(4)}</span>
      <span>Now ${currentPrice.toFixed(4)}</span>
    </div>
  </div>
);

export function LiveTerminalStats() {
  const state = useGlobalState();
  const summary = state.unifiedMarketSummary;
  const activePositions = Array.isArray(state.activePositions) ? state.activePositions : [];
  const krakenPositions = activePositions.filter((pos) => pos.exchange === 'kraken');
  const capitalPositions = activePositions.filter((pos) => pos.exchange === 'capital');

  const totalEquity = safeNumber(state.totalEquity);
  const available = safeNumber(state.availableBalance);
  const totalPnl = safeNumber(state.totalPnl);
  const krakenEquity = safeNumber(summary?.krakenEquity);
  const capitalEquity = safeNumber(summary?.capitalEquityGbp);
  const krakenPnl = safeNumber(summary?.krakenSessionPnl);
  const capitalPnl = safeNumber(summary?.capitalSessionPnlGbp);
  const krakenOpen = safeNumber(summary?.krakenOpenPositions, krakenPositions.length);
  const capitalOpen = safeNumber(summary?.capitalOpenPositions, capitalPositions.length);

  return (
    <Card className="border-border/50 bg-background/95 p-4">
      <div className="mb-4 flex items-center justify-between gap-3 border-b border-border/40 pb-3">
        <div>
          <div className="text-sm font-semibold text-foreground">Live Exchange Metrics</div>
          <div className="text-xs text-muted-foreground">Kraken margin and Capital CFDs only</div>
        </div>
        <div className="text-right font-mono text-[11px]">
          <div className="text-foreground">Open {krakenOpen}K / {capitalOpen}C</div>
          <div className={cn(totalPnl >= 0 ? 'text-green-500' : 'text-red-500')}>
            Session {formatSigned(totalPnl, 2, '€')}
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded border border-border/40 bg-muted/20 p-3">
          <div className="mb-2 font-mono text-xs font-semibold text-foreground">KRAKEN</div>
          <div className="space-y-1.5">
            <ExchangeMetric label="Equity" value={`$${krakenEquity.toFixed(2)}`} />
            <ExchangeMetric label="Session P&L" value={formatSigned(krakenPnl, 2, '$')} className={krakenPnl >= 0 ? 'text-green-500' : 'text-red-500'} />
            <ExchangeMetric label="Open Positions" value={`${krakenOpen}`} />
          </div>
          <div className="mt-3 space-y-2">
            {krakenPositions.length > 0 ? (
              krakenPositions.slice(0, 4).map((pos, index) => (
                <PositionLine
                  key={`kraken-${pos.symbol}-${index}`}
                  symbol={pos.symbol}
                  side={pos.side}
                  entryPrice={safeNumber(pos.entryPrice)}
                  currentPrice={safeNumber(pos.currentPrice, safeNumber(pos.entryPrice))}
                  pnlPercent={safeNumber(pos.pnlPercent)}
                  exchange={pos.exchange}
                />
              ))
            ) : (
              <div className="font-mono text-[11px] text-muted-foreground">No open Kraken positions</div>
            )}
          </div>
        </div>

        <div className="rounded border border-border/40 bg-muted/20 p-3">
          <div className="mb-2 font-mono text-xs font-semibold text-foreground">CAPITAL</div>
          <div className="space-y-1.5">
            <ExchangeMetric label="Equity" value={`£${capitalEquity.toFixed(2)}`} />
            <ExchangeMetric label="Session P&L" value={formatSigned(capitalPnl, 2, '£')} className={capitalPnl >= 0 ? 'text-green-500' : 'text-red-500'} />
            <ExchangeMetric label="Open Positions" value={`${capitalOpen}`} />
          </div>
          <div className="mt-3 space-y-2">
            {capitalPositions.length > 0 ? (
              capitalPositions.slice(0, 4).map((pos, index) => (
                <PositionLine
                  key={`capital-${pos.symbol}-${index}`}
                  symbol={pos.symbol}
                  side={pos.side}
                  entryPrice={safeNumber(pos.entryPrice)}
                  currentPrice={safeNumber(pos.currentPrice, safeNumber(pos.entryPrice))}
                  pnlPercent={safeNumber(pos.pnlPercent)}
                  exchange={pos.exchange}
                />
              ))
            ) : (
              <div className="font-mono text-[11px] text-muted-foreground">No open Capital positions</div>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 rounded border border-border/40 bg-background/60 p-3">
        <div className="mb-2 font-mono text-xs font-semibold text-foreground">ACCOUNT SUMMARY</div>
        <div className="grid gap-1.5 md:grid-cols-3">
          <ExchangeMetric label="Portfolio" value={`€${totalEquity.toFixed(2)}`} />
          <ExchangeMetric label="Available" value={`€${available.toFixed(2)}`} />
          <ExchangeMetric
            label="Total Open"
            value={`${activePositions.length}/${safeNumber(state.maxPositions)}`}
            className="text-primary"
          />
        </div>
        {state.latestMonitorLine && (
          <div className="mt-3 border-t border-border/30 pt-3 font-mono text-[11px] text-muted-foreground">
            {state.latestMonitorLine}
          </div>
        )}
      </div>
    </Card>
  );
}
