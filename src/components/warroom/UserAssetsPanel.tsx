/**
 * User Assets Panel
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Displays per-asset holdings across all connected exchanges with USD values
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useUserBalances, ExchangeBalance } from '@/hooks/useUserBalances';
import { Wallet, RefreshCw, TrendingUp, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const EXCHANGE_COLORS: Record<string, string> = {
  binance: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  kraken: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  alpaca: 'bg-green-500/20 text-green-400 border-green-500/30',
  capital: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
};

const EXCHANGE_LABELS: Record<string, string> = {
  binance: 'Binance',
  kraken: 'Kraken',
  alpaca: 'Alpaca',
  capital: 'Capital.com',
};

export function UserAssetsPanel() {
  const { 
    balances, 
    totalEquityUsd, 
    connectedExchanges, 
    isLoading, 
    error, 
    lastUpdated,
    refresh,
    getConsolidatedAssets 
  } = useUserBalances(true, 30000);

  const consolidatedAssets = getConsolidatedAssets();

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Wallet className="h-4 w-4" />
            PORTFOLIO HOLDINGS
          </CardTitle>
          <div className="flex items-center gap-2">
            {lastUpdated && (
              <span className="text-[10px] text-muted-foreground">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={refresh}
              disabled={isLoading}
              className="h-6 w-6 p-0"
            >
              <RefreshCw className={cn("h-3 w-3", isLoading && "animate-spin")} />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Total Equity */}
        <div className="bg-muted/30 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Total Equity</span>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-400" />
              <span className="text-xl font-bold font-mono">
                ${totalEquityUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>

        {/* Exchange Connection Status */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {balances.map((exchange) => (
            <ExchangeStatusBadge key={exchange.exchange} exchange={exchange} />
          ))}
        </div>

        {/* Error State */}
        {error && (
          <div className="flex items-center gap-2 p-3 bg-destructive/10 rounded-lg text-destructive text-sm">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        {/* Loading State */}
        {isLoading && consolidatedAssets.length === 0 && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        )}

        {/* Assets List */}
        {consolidatedAssets.length > 0 && (
          <div className="space-y-1 max-h-[300px] overflow-y-auto">
            <div className="grid grid-cols-12 gap-2 text-[10px] text-muted-foreground uppercase tracking-wider pb-1 border-b border-border/30">
              <div className="col-span-3">Asset</div>
              <div className="col-span-3 text-right">Free</div>
              <div className="col-span-2 text-right">Locked</div>
              <div className="col-span-2 text-right">USD</div>
              <div className="col-span-2 text-right">Exchange</div>
            </div>
            
            {consolidatedAssets.map((asset) => (
              <AssetRow key={asset.asset} asset={asset} />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && consolidatedAssets.length === 0 && connectedExchanges.length > 0 && (
          <div className="text-center py-6 text-muted-foreground text-sm">
            No assets found in connected exchanges
          </div>
        )}

        {/* No Exchanges Connected */}
        {!isLoading && connectedExchanges.length === 0 && (
          <div className="text-center py-6 text-muted-foreground text-sm">
            No exchanges connected. Add API keys to view balances.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ExchangeStatusBadge({ exchange }: { exchange: ExchangeBalance }) {
  return (
    <div 
      className={cn(
        "flex items-center gap-1.5 px-2 py-1 rounded-md border text-[10px]",
        exchange.connected 
          ? EXCHANGE_COLORS[exchange.exchange] 
          : "bg-muted/30 text-muted-foreground border-border/50"
      )}
    >
      {exchange.connected ? (
        <CheckCircle2 className="h-3 w-3" />
      ) : (
        <XCircle className="h-3 w-3" />
      )}
      <span className="font-medium">{EXCHANGE_LABELS[exchange.exchange]}</span>
      {exchange.connected && (
        <span className="font-mono ml-auto">
          ${exchange.totalUsd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        </span>
      )}
    </div>
  );
}

interface ConsolidatedAsset {
  asset: string;
  free: number;
  locked: number;
  usdValue: number;
  exchanges: string[];
}

function AssetRow({ asset }: { asset: ConsolidatedAsset }) {
  const formatAmount = (val: number) => {
    if (val === 0) return '0';
    if (val < 0.0001) return val.toExponential(2);
    if (val < 1) return val.toFixed(6);
    if (val < 1000) return val.toFixed(4);
    return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
  };

  return (
    <div className="grid grid-cols-12 gap-2 text-xs py-2 border-b border-border/20 last:border-0 hover:bg-muted/20 rounded">
      <div className="col-span-3 font-medium flex items-center gap-1">
        <span className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-bold">
          {asset.asset.slice(0, 2)}
        </span>
        {asset.asset}
      </div>
      <div className="col-span-3 text-right font-mono text-muted-foreground">
        {formatAmount(asset.free)}
      </div>
      <div className="col-span-2 text-right font-mono text-muted-foreground">
        {asset.locked > 0 ? formatAmount(asset.locked) : '-'}
      </div>
      <div className="col-span-2 text-right font-mono font-medium">
        ${asset.usdValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </div>
      <div className="col-span-2 flex justify-end gap-0.5">
        {asset.exchanges.map((ex) => (
          <Badge 
            key={ex} 
            variant="outline" 
            className={cn("text-[8px] px-1 py-0", EXCHANGE_COLORS[ex])}
          >
            {ex.slice(0, 1).toUpperCase()}
          </Badge>
        ))}
      </div>
    </div>
  );
}
