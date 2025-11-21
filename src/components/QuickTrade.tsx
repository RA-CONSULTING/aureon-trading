import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { TrendingUp, TrendingDown, AlertCircle, Loader2 } from "lucide-react";
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { Badge } from "@/components/ui/badge";

interface Balance {
  asset: string;
  free: number;
  price: number;
  usdtValue: number;
}

interface QuickTradeProps {
  balances: Balance[];
  canTrade: boolean;
}

export const QuickTrade = ({ balances, canTrade }: QuickTradeProps) => {
  const [symbol, setSymbol] = useState<string>('');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [amount, setAmount] = useState<string>('');
  const [isExecuting, setIsExecuting] = useState(false);
  const { toast } = useToast();

  // Get tradeable pairs - assets with USDT value > $10
  const tradableAssets = balances.filter(b => 
    b.asset !== 'USDT' && 
    (b.usdtValue > 10 || side === 'SELL')
  );

  const selectedAsset = balances.find(b => b.asset === symbol);

  const executeTrade = async () => {
    if (!symbol || !amount || parseFloat(amount) <= 0) {
      toast({
        title: "Invalid Input",
        description: "Please select a symbol and enter a valid amount",
        variant: "destructive",
      });
      return;
    }

    if (!canTrade) {
      toast({
        title: "Trading Disabled",
        description: "Your API key doesn't have trading permissions",
        variant: "destructive",
      });
      return;
    }

    setIsExecuting(true);

    try {
      // Get trading config
      const { data: config } = await supabase
        .from('trading_config')
        .select('*')
        .single();

      if (!config?.is_enabled) {
        throw new Error('Trading is currently disabled in system settings');
      }

      const tradingSymbol = `${symbol}USDT`;
      const currentPrice = selectedAsset?.price || 0;
      
      if (!currentPrice) {
        throw new Error('Unable to fetch current price');
      }

      // Calculate quantity based on amount (in USDT)
      const amountUsdt = parseFloat(amount);
      const quantity = amountUsdt / currentPrice;

      // Check if user has enough balance
      if (side === 'SELL') {
        const availableBalance = selectedAsset?.free || 0;
        if (quantity > availableBalance) {
          throw new Error(`Insufficient ${symbol} balance. Available: ${availableBalance.toFixed(6)}`);
        }
      } else {
        // For BUY, check USDT balance
        const usdtBalance = balances.find(b => b.asset === 'USDT');
        if (!usdtBalance || amountUsdt > usdtBalance.free) {
          throw new Error(`Insufficient USDT balance. Available: $${usdtBalance?.free.toFixed(2) || 0}`);
        }
      }

      // Create a manual signal first
      const { data: signal, error: signalError } = await supabase
        .from('trading_signals')
        .insert({
          signal_type: side === 'BUY' ? 'LONG' : 'SHORT',
          coherence: 0.85, // Manual trades get high coherence
          lighthouse_value: 0.9,
          prism_level: 4,
          reason: `🎯 Manual ${side} order - ${symbol} @ $${currentPrice.toFixed(2)}`,
          strength: 0.8,
        })
        .select()
        .single();

      if (signalError || !signal) {
        throw new Error('Failed to create trading signal');
      }

      // Execute the trade
      const { data, error } = await supabase.functions.invoke('execute-trade', {
        body: {
          signalId: signal.id,
          lighthouseEventId: null,
          symbol: tradingSymbol,
          signalType: side === 'BUY' ? 'LONG' : 'SHORT',
          coherence: 0.85,
          lighthouseValue: 0.9,
          lighthouseConfidence: 0.85,
          prismLevel: 4,
          currentPrice,
        },
      });

      if (error) throw error;
      if (data.error) throw new Error(data.error);

      toast({
        title: "Trade Executed! 🎉",
        description: data.message,
      });

      // Reset form
      setAmount('');
      
    } catch (error) {
      console.error('Trade execution error:', error);
      toast({
        title: "Trade Failed",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  if (!canTrade) {
    return (
      <Card className="bg-card/50 backdrop-blur border-border/50">
        <CardContent className="p-6">
          <div className="flex items-start gap-3 text-center">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div>
              <p className="font-medium text-sm">Trading Disabled</p>
              <p className="text-xs text-muted-foreground mt-1">
                Your Binance API key doesn't have trading permissions enabled.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Quick Trade
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="symbol">Asset</Label>
          <Select value={symbol} onValueChange={setSymbol}>
            <SelectTrigger id="symbol">
              <SelectValue placeholder="Select asset to trade" />
            </SelectTrigger>
            <SelectContent>
              {tradableAssets.map((balance) => (
                <SelectItem key={balance.asset} value={balance.asset}>
                  <div className="flex items-center justify-between w-full gap-4">
                    <span className="font-mono">{balance.asset}</span>
                    <span className="text-xs text-muted-foreground">
                      {balance.free.toFixed(6)} @ ${balance.price.toFixed(2)}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Side</Label>
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant={side === 'BUY' ? 'default' : 'outline'}
              onClick={() => setSide('BUY')}
              className="gap-2"
            >
              <TrendingUp className="h-4 w-4" />
              Buy
            </Button>
            <Button
              type="button"
              variant={side === 'SELL' ? 'default' : 'outline'}
              onClick={() => setSide('SELL')}
              className="gap-2"
            >
              <TrendingDown className="h-4 w-4" />
              Sell
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="amount">Amount (USDT)</Label>
          <Input
            id="amount"
            type="number"
            placeholder="Enter amount in USDT"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            min="0"
            step="0.01"
          />
          {selectedAsset && amount && parseFloat(amount) > 0 && (
            <div className="text-xs text-muted-foreground mt-1">
              ≈ {(parseFloat(amount) / selectedAsset.price).toFixed(6)} {symbol}
            </div>
          )}
        </div>

        {selectedAsset && (
          <div className="p-3 rounded-lg bg-muted/50 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Current Price:</span>
              <span className="font-mono font-semibold">${selectedAsset.price.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Available Balance:</span>
              <span className="font-mono">{selectedAsset.free.toFixed(6)} {symbol}</span>
            </div>
            {side === 'BUY' && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">USDT Available:</span>
                <span className="font-mono">
                  ${(balances.find(b => b.asset === 'USDT')?.free || 0).toFixed(2)}
                </span>
              </div>
            )}
          </div>
        )}

        <Button
          onClick={executeTrade}
          disabled={isExecuting || !symbol || !amount}
          className="w-full"
          size="lg"
        >
          {isExecuting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Executing Trade...
            </>
          ) : (
            <>
              {side === 'BUY' ? <TrendingUp className="h-4 w-4 mr-2" /> : <TrendingDown className="h-4 w-4 mr-2" />}
              Execute {side} Order
            </>
          )}
        </Button>

        <div className="pt-2 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center">
            <Badge variant="outline" className="text-xs">Paper Trading Mode</Badge>
            <br />
            Check trading config to enable live trading
          </p>
        </div>
      </CardContent>
    </Card>
  );
};