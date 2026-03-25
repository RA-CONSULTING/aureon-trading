#!/bin/bash
# 🦆⚔️ SPECIALIZED 5-BOT ARMY ⚔️🦆
# 2 Buyers | 2 Sellers | 1 Watcher

pkill -f aureon
sleep 3

echo "🦆⚔️ DEPLOYING SPECIALIZED TRADING ARMY ⚔️🦆"
echo ""

# BOT 1 - BUYER (Key 4)
echo "💰 Launching BUYER 1..."
export BINANCE_API_KEY="92nqB9iH4JLDCNY9tGZEW3OuEcM9L9oknJJGRlJH03WIkkO8TkvbYRzoyFUbJdfL"
export BINANCE_API_SECRET="KgaBXEmUV4xKTREww0W5vfNoAYHfNwBryUInzTQZHqjfsEIcFMquzANchTreKEWH"
export BINANCE_USE_TESTNET=false
export BINANCE_DRY_RUN=false
export BOT_ROLE=BUYER
nohup python aureon_specialized.py > aureon_buyer1.log 2>&1 &
echo "✅ Buyer 1 (Key 4) - PID: $!"

sleep 10

# BOT 2 - BUYER (Key 5)
echo "💰 Launching BUYER 2..."
export BINANCE_API_KEY="lImzLyev2qdfWnO8WVfXYhAbvR9JKX9rTI7fGjPvSimhY7x0my3Ivg5GNWwv2HgL"
export BINANCE_API_SECRET="kvaNjghikzWE77Outg7bmXKO8fmi404VU9Hp6anRcNG3GZEntb9MrohpK3rizIdu"
export BOT_ROLE=BUYER
nohup python aureon_specialized.py > aureon_buyer2.log 2>&1 &
echo "✅ Buyer 2 (Key 5) - PID: $!"

sleep 10

# BOT 3 - SELLER (Key 6)
echo "💎 Launching SELLER 1..."
export BINANCE_API_KEY="LO6XOdnfHeFZmUvVGH9qeurrJaooCEpI0eWf0ffNPMXRmhLzk3Ok1WS68PD9td8T"
export BINANCE_API_SECRET="TO8N685rjjzVUmch3NyLPYtABX5ch5gnYoiEF67eJQApNJARSAWSrpTog2rYrOtt"
export BOT_ROLE=SELLER
nohup python aureon_specialized.py > aureon_seller1.log 2>&1 &
echo "✅ Seller 1 (Key 6) - PID: $!"

sleep 10

# BOT 4 - SELLER (Key 8)
echo "💎 Launching SELLER 2..."
export BINANCE_API_KEY="1lxtzT46XJKmNxY1XPtKiX2FqlXS564YoS8EJepWRQvHeRh8FQB22dgtQrCMjR3e"
export BINANCE_API_SECRET="aiwyltwOzvw5OWwCtDmiMQ9vRWXLGWWqoL5g2hGFEN4OwqB6QwBY1Zx6MOgZt11K"
export BOT_ROLE=SELLER
nohup python aureon_specialized.py > aureon_seller2.log 2>&1 &
echo "✅ Seller 2 (Key 8) - PID: $!"

sleep 10

# BOT 5 - WATCHER (Key 9)
echo "👁️ Launching WATCHER..."
export BINANCE_API_KEY="b1y7dTPUSBVXfVeFFS90aWRY87e58bHabDGsoOt8ZBv8QmovuqNnVvyEQ0rnptsD"
export BINANCE_API_SECRET="D9WIsTpMUifMLoFtYb7EXef2E2Io2AaapqZsN2PIJjwZJtZVf0CP2zTwWISpkbsH"
export BOT_ROLE=WATCHER
nohup python aureon_specialized.py > aureon_watcher.log 2>&1 &
echo "✅ Watcher (Key 9) - PID: $!"

echo ""
echo "🦆⚔️ SPECIALIZED ARMY DEPLOYED! ⚔️🦆"
echo ""
echo "💰 2 BUYERS:  Hunting entries (Keys 4, 5)"
echo "💎 2 SELLERS: Managing exits (Keys 6, 8)"
echo "👁️ 1 WATCHER: Market intel (Key 9)"
echo ""
echo "Monitor:"
echo "  tail -f aureon_buyer*.log"
echo "  tail -f aureon_seller*.log"  
echo "  tail -f aureon_watcher.log"
