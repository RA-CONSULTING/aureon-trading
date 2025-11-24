import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useBinanceBalances } from '@/hooks/useBinanceBalances';
import { RefreshCw, Wallet, DollarSign, Bitcoin } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export function RealBinanceBalances() {
  const { accounts, totals, loading, lastUpdated, refresh } = useBinanceBalances();

  return (
    <Card className="p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Wallet className="h-5 w-5" />
              Live Binance Wallets
            </h3>
            <p className="text-sm text-muted-foreground">
              {accounts.length} accounts connected
              {lastUpdated && ` • Updated ${formatDistanceToNow(lastUpdated, { addSuffix: true })}`}
            </p>
          </div>
          <Button onClick={refresh} disabled={loading} variant="outline" size="sm">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Total Balances */}
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="h-4 w-4 text-green-500" />
              <div className="text-xs text-muted-foreground">USDT</div>
            </div>
            <div className="text-2xl font-bold text-green-500">
              ${totals.USDT.toFixed(2)}
            </div>
          </div>
          
          <div className="p-4 rounded-lg bg-gradient-to-br from-orange-500/10 to-orange-600/10 border border-orange-500/20">
            <div className="flex items-center gap-2 mb-2">
              <Bitcoin className="h-4 w-4 text-orange-500" />
              <div className="text-xs text-muted-foreground">BTC</div>
            </div>
            <div className="text-2xl font-bold text-orange-500">
              {totals.BTC.toFixed(6)}
            </div>
          </div>
          
          <div className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20">
            <div className="flex items-center gap-2 mb-2">
              <div className="h-4 w-4 text-blue-500">Ξ</div>
              <div className="text-xs text-muted-foreground">ETH</div>
            </div>
            <div className="text-2xl font-bold text-blue-500">
              {totals.ETH.toFixed(6)}
            </div>
          </div>
        </div>

        {/* Account Details */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {accounts.map((account) => (
            <div
              key={account.name}
              className="p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium text-sm">{account.name}</div>
                {account.error ? (
                  <Badge variant="destructive">Error</Badge>
                ) : account.canTrade ? (
                  <Badge className="bg-green-500">Active</Badge>
                ) : (
                  <Badge variant="outline">Restricted</Badge>
                )}
              </div>
              
              {account.error ? (
                <div className="text-xs text-red-500">{account.error}</div>
              ) : (
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {Object.entries(account.balances)
                    .filter(([_, bal]) => bal.total > 0.001) // Only show significant balances
                    .slice(0, 6) // Limit to top 6 assets
                    .map(([asset, balance]) => (
                      <div key={asset} className="flex justify-between">
                        <span className="text-muted-foreground">{asset}:</span>
                        <span className="font-medium">{balance.total.toFixed(asset === 'USDT' ? 2 : 6)}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {loading && (
          <div className="text-center text-sm text-muted-foreground">
            Fetching real-time balances from Binance...
          </div>
        )}
      </div>
    </Card>
  );
}
