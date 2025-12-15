/**
 * 🎵 API CAPACITY & KEY REQUIREMENTS ANALYSIS 🎵
 * 
 * Calculates exactly how many API keys needed per broker
 * to sustain 48,000 trades/day (2,000 trades/hour × 24 hours)
 */

interface BrokerAPISpec {
  name: string;
  emoji: string;
  // Rate limits
  requestsPerSecond: number;
  requestsPerMinute: number;
  ordersPerSecond: number;
  ordersPerDay: number;
  // API calls per trade
  callsPerTrade: number; // price check + order + confirmation
  // Costs
  apiKeyLimit: number; // max keys per account
  monthlyDataFee: number;
  // Position limits
  maxConcurrentPositions: number;
  maxOrdersPerSecond: number;
}

const BROKERS: { [key: string]: BrokerAPISpec } = {
  binance: {
    name: 'Binance',
    emoji: '🪙',
    requestsPerSecond: 20,        // 1200/min = 20/sec
    requestsPerMinute: 1200,
    ordersPerSecond: 10,
    ordersPerDay: 100000,
    callsPerTrade: 3,             // getPrice + createOrder + getOrder
    apiKeyLimit: 30,              // max 30 API keys per account
    monthlyDataFee: 0,
    maxConcurrentPositions: 200,  // practical limit
    maxOrdersPerSecond: 10,
  },
  capital: {
    name: 'Capital.com',
    emoji: '📊',
    requestsPerSecond: 10,
    requestsPerMinute: 600,
    ordersPerSecond: 5,
    ordersPerDay: 50000,          // estimated
    callsPerTrade: 4,             // session + price + order + confirm
    apiKeyLimit: 5,               // limited API keys
    monthlyDataFee: 0,
    maxConcurrentPositions: 200,
    maxOrdersPerSecond: 5,
  },
  alpaca: {
    name: 'Alpaca',
    emoji: '🦙',
    requestsPerSecond: 3.33,      // 200/min = 3.33/sec
    requestsPerMinute: 200,
    ordersPerSecond: 3,
    ordersPerDay: 500000,         // very generous
    callsPerTrade: 2,             // order + confirmation (streaming prices)
    apiKeyLimit: 1,               // 1 key per account, need multiple accounts
    monthlyDataFee: 0,            // free tier
    maxConcurrentPositions: 1000,
    maxOrdersPerSecond: 3,
  },
  oanda: {
    name: 'OANDA',
    emoji: '💱',
    requestsPerSecond: 120,       // very generous!
    requestsPerMinute: 7200,
    ordersPerSecond: 30,
    ordersPerDay: 1000000,        // essentially unlimited
    callsPerTrade: 2,             // streaming prices, just order + confirm
    apiKeyLimit: 1,               // 1 key per account
    monthlyDataFee: 0,
    maxConcurrentPositions: 1000,
    maxOrdersPerSecond: 30,
  },
};

// Our trading requirements
const REQUIREMENTS = {
  tradesPerHour: 500,          // per broker
  hoursPerDay: 24,
  brokersCount: 4,
  
  // Derived
  get tradesPerDay() { return this.tradesPerHour * this.hoursPerDay; },
  get tradesPerMinute() { return this.tradesPerHour / 60; },
  get tradesPerSecond() { return this.tradesPerHour / 3600; },
  get totalDailyTrades() { return this.tradesPerDay * this.brokersCount; },
};

function analyzeApiCapacity() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🔑 API CAPACITY & KEY REQUIREMENTS ANALYSIS 🔑                              ║
  ║                                                                               ║
  ║   Trading Target: ${REQUIREMENTS.tradesPerHour} trades/hour per broker                          ║
  ║   Daily Target: ${REQUIREMENTS.tradesPerDay.toLocaleString()} trades/day per broker                          ║
  ║   Total Daily: ${REQUIREMENTS.totalDailyTrades.toLocaleString()} trades across all brokers                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  console.log('  ═══════════════════════════════════════════════════════════════════════════════');
  console.log('                              📊 RATE LIMIT ANALYSIS');
  console.log('  ═══════════════════════════════════════════════════════════════════════════════\n');

  const results: any[] = [];

  for (const [brokerId, spec] of Object.entries(BROKERS)) {
    const tradesPerSecond = REQUIREMENTS.tradesPerSecond;
    const tradesPerMinute = REQUIREMENTS.tradesPerMinute;
    const tradesPerDay = REQUIREMENTS.tradesPerDay;
    
    // API calls needed
    const callsPerSecond = tradesPerSecond * spec.callsPerTrade;
    const callsPerMinute = tradesPerMinute * spec.callsPerTrade;
    const callsPerDay = tradesPerDay * spec.callsPerTrade;
    
    // Capacity per key
    const maxTradesPerSecPerKey = spec.ordersPerSecond;
    const maxTradesPerMinPerKey = spec.requestsPerMinute / spec.callsPerTrade;
    const maxTradesPerDayPerKey = spec.ordersPerDay;
    
    // Keys needed (bottleneck calculation)
    const keysForSecondLimit = Math.ceil(tradesPerSecond / maxTradesPerSecPerKey);
    const keysForMinuteLimit = Math.ceil(tradesPerMinute / maxTradesPerMinPerKey);
    const keysForDayLimit = Math.ceil(tradesPerDay / maxTradesPerDayPerKey);
    
    const keysNeeded = Math.max(keysForSecondLimit, keysForMinuteLimit, keysForDayLimit);
    const bottleneck = keysForSecondLimit >= keysForMinuteLimit && keysForSecondLimit >= keysForDayLimit 
      ? 'orders/sec' 
      : keysForMinuteLimit >= keysForDayLimit 
        ? 'requests/min' 
        : 'orders/day';
    
    // Utilization with 1 key
    const utilizationSec = (tradesPerSecond / maxTradesPerSecPerKey * 100).toFixed(1);
    const utilizationMin = (tradesPerMinute / maxTradesPerMinPerKey * 100).toFixed(1);
    const utilizationDay = (tradesPerDay / maxTradesPerDayPerKey * 100).toFixed(1);
    
    // Can we do it with 1 key?
    const singleKeyOk = keysNeeded <= 1;
    
    // Accounts needed (if keys limited)
    const accountsNeeded = Math.ceil(keysNeeded / spec.apiKeyLimit);

    results.push({
      brokerId,
      spec,
      callsPerSecond,
      callsPerMinute,
      callsPerDay,
      keysNeeded,
      bottleneck,
      utilizationSec,
      utilizationMin,
      utilizationDay,
      singleKeyOk,
      accountsNeeded,
      maxTradesPerSecPerKey,
      maxTradesPerMinPerKey,
      maxTradesPerDayPerKey,
    });

    console.log(`  ${spec.emoji} ${spec.name.toUpperCase()}`);
    console.log(`  ${'─'.repeat(70)}`);
    console.log(`
  📋 API LIMITS (per key):
     • Requests/second:     ${spec.requestsPerSecond}
     • Requests/minute:     ${spec.requestsPerMinute.toLocaleString()}
     • Orders/second:       ${spec.ordersPerSecond}
     • Orders/day:          ${spec.ordersPerDay.toLocaleString()}
     • Calls per trade:     ${spec.callsPerTrade}
     • Max positions:       ${spec.maxConcurrentPositions}

  📊 OUR REQUIREMENTS:
     • Trades/second:       ${tradesPerSecond.toFixed(3)}
     • Trades/minute:       ${tradesPerMinute.toFixed(2)}
     • Trades/day:          ${tradesPerDay.toLocaleString()}
     • API calls/second:    ${callsPerSecond.toFixed(2)}
     • API calls/day:       ${callsPerDay.toLocaleString()}

  📈 CAPACITY PER KEY:
     • Max trades/sec:      ${maxTradesPerSecPerKey}
     • Max trades/min:      ${maxTradesPerMinPerKey.toFixed(1)}
     • Max trades/day:      ${maxTradesPerDayPerKey.toLocaleString()}

  ⚡ UTILIZATION (with 1 key):
     • Second limit:        ${utilizationSec}% ${parseFloat(utilizationSec) > 100 ? '🔴 EXCEEDED' : '🟢 OK'}
     • Minute limit:        ${utilizationMin}% ${parseFloat(utilizationMin) > 100 ? '🔴 EXCEEDED' : '🟢 OK'}
     • Daily limit:         ${utilizationDay}% ${parseFloat(utilizationDay) > 100 ? '🔴 EXCEEDED' : '🟢 OK'}

  🔑 KEYS REQUIRED:
     • Minimum keys:        ${keysNeeded} ${singleKeyOk ? '✅ (1 key sufficient!)' : '⚠️'}
     • Bottleneck:          ${bottleneck}
     • Max keys/account:    [REDACTED]
     • Accounts needed:     ${accountsNeeded}
`);
  }

  // Summary table
  console.log(`
  ═══════════════════════════════════════════════════════════════════════════════
                              📋 SUMMARY TABLE
  ═══════════════════════════════════════════════════════════════════════════════
  `);

  console.log('  ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐');
  console.log('  │   Broker    │ Trades/Day  │  Keys Need  │  Bottleneck │  Accounts   │   Status    │');
  console.log('  ├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤');

  for (const r of results) {
    const status = r.singleKeyOk ? '✅ 1 KEY OK' : `⚠️ ${r.keysNeeded} KEYS`;
    console.log(`  │ ${r.spec.emoji} ${r.spec.name.padEnd(9)} │ ${REQUIREMENTS.tradesPerDay.toLocaleString().padStart(11)} │ ${r.keysNeeded.toString().padStart(11)} │ ${r.bottleneck.padStart(11)} │ ${r.accountsNeeded.toString().padStart(11)} │ ${status.padStart(11)} │`);
  }

  console.log('  └─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘');

  // Total requirements
  const totalKeys = results.reduce((sum, r) => sum + r.keysNeeded, 0);
  const totalAccounts = results.reduce((sum, r) => sum + r.accountsNeeded, 0);

  console.log(`
  ═══════════════════════════════════════════════════════════════════════════════
                           🔐 TOTAL REQUIREMENTS
  ═══════════════════════════════════════════════════════════════════════════════

  ┌───────────────────────────────────────────────────────────────────────────────┐
  │                                                                               │
  │   🔑 Total API Keys Needed:      ${totalKeys.toString().padStart(3)}                                         │
  │   👤 Total Accounts Needed:      ${totalAccounts.toString().padStart(3)}                                         │
  │   📈 Total Daily Trades:         ${REQUIREMENTS.totalDailyTrades.toLocaleString().padStart(7)}                                   │
  │   💰 Monthly API Costs:          £0.00 (all free tier!)                       │
  │                                                                               │
  └───────────────────────────────────────────────────────────────────────────────┘
  `);

  // Detailed breakdown by broker
  console.log(`
  ═══════════════════════════════════════════════════════════════════════════════
                        📝 DETAILED SETUP REQUIREMENTS
  ═══════════════════════════════════════════════════════════════════════════════
  `);

  for (const r of results) {
    console.log(`  ${r.spec.emoji} ${r.spec.name.toUpperCase()}`);
    console.log(`  ${'─'.repeat(70)}`);
    
    if (r.singleKeyOk) {
      console.log(`
     ✅ SINGLE KEY SUFFICIENT
     
     Setup:
     • 1 trading account
     • 1 API key
     • Enable trading permissions
     
     Headroom: ${(100 - Math.max(parseFloat(r.utilizationSec), parseFloat(r.utilizationMin), parseFloat(r.utilizationDay))).toFixed(1)}% spare capacity
`);
    } else {
      console.log(`
     ⚠️ MULTIPLE KEYS REQUIRED
     
     Setup:
     • ${r.accountsNeeded} trading account(s)
     • ${r.keysNeeded} API key(s) total
     • Load balance across keys
     
     Strategy:
     • Round-robin requests across ${r.keysNeeded} keys
     • Each key handles ${Math.ceil(REQUIREMENTS.tradesPerDay / r.keysNeeded)} trades/day
     
     Alternative:
     • Reduce trade frequency to ${Math.floor(r.spec.ordersPerDay / 24)} trades/hour (single key)
`);
    }
  }

  // Scaling recommendations
  console.log(`
  ═══════════════════════════════════════════════════════════════════════════════
                        📈 SCALING RECOMMENDATIONS
  ═══════════════════════════════════════════════════════════════════════════════

  🎯 CURRENT TARGET: 500 trades/hour per broker (48,000/day total)

  ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
  │   Scale     │  Trades/Hr  │ Trades/Day  │  Keys Need  │   Accounts  │
  ├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤`);

  const scales = [
    { name: 'Minimal', multiplier: 0.1 },
    { name: 'Conservative', multiplier: 0.25 },
    { name: 'Moderate', multiplier: 0.5 },
    { name: 'Current', multiplier: 1 },
    { name: 'Aggressive', multiplier: 2 },
    { name: 'Maximum', multiplier: 5 },
  ];

  for (const scale of scales) {
    const tradesPerHour = Math.floor(500 * scale.multiplier);
    const tradesPerDay = tradesPerHour * 24 * 4;
    
    let totalKeysNeeded = 0;
    let totalAccountsNeeded = 0;
    
    for (const [brokerId, spec] of Object.entries(BROKERS)) {
      const dailyTrades = tradesPerHour * 24;
      const keysNeeded = Math.max(
        1,
        Math.ceil(dailyTrades / spec.ordersPerDay),
        Math.ceil((tradesPerHour / 60) / (spec.requestsPerMinute / spec.callsPerTrade))
      );
      totalKeysNeeded += keysNeeded;
      totalAccountsNeeded += Math.ceil(keysNeeded / spec.apiKeyLimit);
    }
    
    const current = scale.name === 'Current' ? ' 👈' : '';
    console.log(`  │ ${scale.name.padEnd(11)} │ ${(tradesPerHour * 4).toLocaleString().padStart(11)} │ ${tradesPerDay.toLocaleString().padStart(11)} │ ${totalKeysNeeded.toString().padStart(11)} │ ${totalAccountsNeeded.toString().padStart(11)} │${current}`);
  }

  console.log(`  └─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘`);

  // WebSocket recommendation
  console.log(`
  ═══════════════════════════════════════════════════════════════════════════════
                        🔌 WEBSOCKET OPTIMIZATION
  ═══════════════════════════════════════════════════════════════════════════════

  Using WebSocket streams REDUCES API calls significantly:

  ┌─────────────┬───────────────────────┬───────────────────────┐
  │   Broker    │  REST (calls/trade)   │  WebSocket (calls)    │
  ├─────────────┼───────────────────────┼───────────────────────┤
  │ 🪙 Binance   │  3 (price+order+conf) │  1 (order only)       │
  │ 📊 Capital   │  4 (session+price+2)  │  2 (order+conf)       │
  │ 🦙 Alpaca    │  2 (order+conf)       │  1 (order only)       │
  │ 💱 OANDA     │  2 (order+conf)       │  1 (order only)       │
  └─────────────┴───────────────────────┴───────────────────────┘

  💡 With WebSocket: ALL brokers work with 1 API key!

  ═══════════════════════════════════════════════════════════════════════════════
  `);

  // Final verdict
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🎵 FINAL VERDICT: THE TEMPO IS ACHIEVABLE 🎵                                ║
  ║                                                                               ║
  ╠═══════════════════════════════════════════════════════════════════════════════╣
  ║                                                                               ║
  ║   For 48,000 trades/day (current simulation):                                 ║
  ║                                                                               ║
  ║   🪙 Binance:    1 API key  ✅ (has 10 orders/sec capacity)                   ║
  ║   📊 Capital:    1 API key  ✅ (10 req/sec is enough)                         ║
  ║   🦙 Alpaca:     1 API key  ✅ (200/min handles 8.3 trades/min)               ║
  ║   💱 OANDA:      1 API key  ✅ (120 req/sec is massive overkill!)             ║
  ║                                                                               ║
  ║   ─────────────────────────────────────────────────────────────────────────   ║
  ║                                                                               ║
  ║   TOTAL: 4 API keys (1 per broker) + 4 accounts                               ║
  ║   COST:  £0/month (all free tier APIs)                                        ║
  ║                                                                               ║
  ║   🎯 The symphony can play at full tempo with minimal setup! 🎯               ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝

  ─────────────────────────────────────────────────────────────────────────────────
  🎵 "Four keys, four accounts, 48,000 trades - the dance continues" 🎵
  ─────────────────────────────────────────────────────────────────────────────────
  `);
}

analyzeApiCapacity();
