import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface ExchangeSymbol {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  exchange: string;
  minQty?: number;
  maxQty?: number;
  stepSize?: number;
  minNotional?: number;
  tickSize?: number;
  pricePrecision?: number;
  quantityPrecision?: number;
  isActive: boolean;
  isSpotTradingAllowed: boolean;
  status: string;
}

async function fetchBinanceAssets(): Promise<ExchangeSymbol[]> {
  try {
    console.log('[sync-exchange-assets] Fetching Binance exchange info...');
    const response = await fetch('https://api.binance.com/api/v3/exchangeInfo');
    
    if (!response.ok) {
      throw new Error(`Binance API error: ${response.status}`);
    }
    
    const data = await response.json();
    const symbols: ExchangeSymbol[] = [];
    
    for (const sym of data.symbols) {
      // Only include USDT spot pairs
      if (sym.quoteAsset === 'USDT' && sym.isSpotTradingAllowed) {
        const lotSizeFilter = sym.filters?.find((f: any) => f.filterType === 'LOT_SIZE');
        const priceFilter = sym.filters?.find((f: any) => f.filterType === 'PRICE_FILTER');
        const notionalFilter = sym.filters?.find((f: any) => f.filterType === 'NOTIONAL' || f.filterType === 'MIN_NOTIONAL');
        
        symbols.push({
          symbol: sym.symbol,
          baseAsset: sym.baseAsset,
          quoteAsset: sym.quoteAsset,
          exchange: 'binance',
          minQty: lotSizeFilter ? parseFloat(lotSizeFilter.minQty) : undefined,
          maxQty: lotSizeFilter ? parseFloat(lotSizeFilter.maxQty) : undefined,
          stepSize: lotSizeFilter ? parseFloat(lotSizeFilter.stepSize) : undefined,
          minNotional: notionalFilter ? parseFloat(notionalFilter.minNotional || notionalFilter.notional) : undefined,
          tickSize: priceFilter ? parseFloat(priceFilter.tickSize) : undefined,
          pricePrecision: sym.pricePrecision || 8,
          quantityPrecision: sym.quantityPrecision || 8,
          isActive: sym.status === 'TRADING',
          isSpotTradingAllowed: sym.isSpotTradingAllowed,
          status: sym.status,
        });
      }
    }
    
    console.log(`[sync-exchange-assets] Found ${symbols.length} Binance USDT pairs`);
    return symbols;
  } catch (error) {
    console.error('[sync-exchange-assets] Binance fetch error:', error);
    return [];
  }
}

async function fetchKrakenAssets(): Promise<ExchangeSymbol[]> {
  try {
    console.log('[sync-exchange-assets] Fetching Kraken asset pairs...');
    const response = await fetch('https://api.kraken.com/0/public/AssetPairs');
    
    if (!response.ok) {
      throw new Error(`Kraken API error: ${response.status}`);
    }
    
    const data = await response.json();
    const symbols: ExchangeSymbol[] = [];
    
    if (data.result) {
      for (const [pairName, pairInfo] of Object.entries(data.result) as [string, any][]) {
        // Only include USD pairs
        if (pairInfo.quote === 'ZUSD' || pairInfo.quote === 'USD') {
          symbols.push({
            symbol: pairName,
            baseAsset: pairInfo.base.replace(/^[XZ]/, ''),
            quoteAsset: 'USD',
            exchange: 'kraken',
            minQty: pairInfo.ordermin ? parseFloat(pairInfo.ordermin) : undefined,
            tickSize: pairInfo.tick_size ? parseFloat(pairInfo.tick_size) : undefined,
            pricePrecision: pairInfo.pair_decimals || 8,
            quantityPrecision: pairInfo.lot_decimals || 8,
            isActive: pairInfo.status === 'online',
            isSpotTradingAllowed: true,
            status: pairInfo.status || 'online',
          });
        }
      }
    }
    
    console.log(`[sync-exchange-assets] Found ${symbols.length} Kraken USD pairs`);
    return symbols;
  } catch (error) {
    console.error('[sync-exchange-assets] Kraken fetch error:', error);
    return [];
  }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    const { exchanges = ['binance', 'kraken'] } = await req.json().catch(() => ({}));
    
    console.log(`[sync-exchange-assets] Syncing assets for: ${exchanges.join(', ')}`);
    
    const allSymbols: ExchangeSymbol[] = [];
    
    // Fetch from all requested exchanges in parallel
    const fetchPromises: Promise<ExchangeSymbol[]>[] = [];
    
    if (exchanges.includes('binance')) {
      fetchPromises.push(fetchBinanceAssets());
    }
    if (exchanges.includes('kraken')) {
      fetchPromises.push(fetchKrakenAssets());
    }
    
    const results = await Promise.all(fetchPromises);
    results.forEach(symbols => allSymbols.push(...symbols));
    
    console.log(`[sync-exchange-assets] Total symbols to upsert: ${allSymbols.length}`);
    
    // Upsert all symbols to database
    const upsertData = allSymbols.map(s => ({
      symbol: s.symbol,
      base_asset: s.baseAsset,
      quote_asset: s.quoteAsset,
      exchange: s.exchange,
      min_qty: s.minQty,
      max_qty: s.maxQty,
      step_size: s.stepSize,
      min_notional: s.minNotional,
      tick_size: s.tickSize,
      price_precision: s.pricePrecision,
      quantity_precision: s.quantityPrecision,
      is_active: s.isActive,
      is_spot_trading_allowed: s.isSpotTradingAllowed,
      status: s.status,
      last_synced_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }));
    
    // Batch upsert in chunks of 500
    const chunkSize = 500;
    let totalUpserted = 0;
    
    for (let i = 0; i < upsertData.length; i += chunkSize) {
      const chunk = upsertData.slice(i, i + chunkSize);
      const { data, error } = await supabase
        .from('crypto_assets_registry')
        .upsert(chunk, { onConflict: 'symbol,exchange' })
        .select('id');
      
      if (error) {
        console.error(`[sync-exchange-assets] Upsert error for chunk ${i}:`, error);
      } else {
        totalUpserted += data?.length || 0;
      }
    }
    
    console.log(`[sync-exchange-assets] Successfully synced ${totalUpserted} assets`);
    
    return new Response(
      JSON.stringify({
        success: true,
        synced: totalUpserted,
        exchanges: exchanges,
        breakdown: {
          binance: allSymbols.filter(s => s.exchange === 'binance').length,
          kraken: allSymbols.filter(s => s.exchange === 'kraken').length,
        },
        syncedAt: new Date().toISOString(),
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    console.error('[sync-exchange-assets] Error:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
