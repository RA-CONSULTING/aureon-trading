#!/bin/bash
# 🦆⚔️ STAGGERED MULTI-BOT LAUNCHER - Avoid rate limits ⚔️🦆

# Kill any existing bots
pkill -f aureon_ultimate.py
sleep 2

echo "🦆⚔️ LAUNCHING 5 BOTS WITH STAGGERED TIMING ⚔️🦆"
echo "Each bot offset by 12 seconds to avoid API rate limits"
echo ""

# Key 4 - Start immediately
export BINANCE_API_KEY="92nqB9iH4JLDCNY9tGZEW3OuEcM9L9oknJJGRlJH03WIkkO8TkvbYRzoyFUbJdfL"
export BINANCE_API_SECRET="KgaBXEmUV4xKTREww0W5vfNoAYHfNwBryUInzTQZHqjfsEIcFMquzANchTreKEWH"
export BINANCE_USE_TESTNET=false
export BINANCE_DRY_RUN=false
nohup python aureon_ultimate.py > aureon_key4.log 2>&1 &
echo "✅ Bot 1 (Key 4) started at T+0s  - PID: $!"

# Key 5 - Wait 12 seconds
sleep 12
export BINANCE_API_KEY="lImzLyev2qdfWnO8WVfXYhAbvR9JKX9rTI7fGjPvSimhY7x0my3Ivg5GNWwv2HgL"
export BINANCE_API_SECRET="kvaNjghikzWE77Outg7bmXKO8fmi404VU9Hp6anRcNG3GZEntb9MrohpK3rizIdu"
nohup python aureon_ultimate.py > aureon_key5.log 2>&1 &
echo "✅ Bot 2 (Key 5) started at T+12s - PID: $!"

# Key 6 - Wait another 12 seconds
sleep 12
export BINANCE_API_KEY="LO6XOdnfHeFZmUvVGH9qeurrJaooCEpI0eWf0ffNPMXRmhLzk3Ok1WS68PD9td8T"
export BINANCE_API_SECRET="TO8N685rjjzVUmch3NyLPYtABX5ch5gnYoiEF67eJQApNJARSAWSrpTog2rYrOtt"
nohup python aureon_ultimate.py > aureon_key6.log 2>&1 &
echo "✅ Bot 3 (Key 6) started at T+24s - PID: $!"

# Key 8 - Wait another 12 seconds
sleep 12
export BINANCE_API_KEY="1lxtzT46XJKmNxY1XPtKiX2FqlXS564YoS8EJepWRQvHeRh8FQB22dgtQrCMjR3e"
export BINANCE_API_SECRET="aiwyltwOzvw5OWwCtDmiMQ9vRWXLGWWqoL5g2hGFEN4OwqB6QwBY1Zx6MOgZt11K"
nohup python aureon_ultimate.py > aureon_key8.log 2>&1 &
echo "✅ Bot 4 (Key 8) started at T+36s - PID: $!"

# Key 9 - Wait another 12 seconds
sleep 12
export BINANCE_API_KEY="b1y7dTPUSBVXfVeFFS90aWRY87e58bHabDGsoOt8ZBv8QmovuqNnVvyEQ0rnptsD"
export BINANCE_API_SECRET="D9WIsTpMUifMLoFtYb7EXef2E2Io2AaapqZsN2PIJjwZJtZVf0CP2zTwWISpkbsH"
nohup python aureon_ultimate.py > aureon_key9.log 2>&1 &
echo "✅ Bot 5 (Key 9) started at T+48s - PID: $!"

echo ""
echo "🦆⚔️ ALL 5 BOTS DEPLOYED! ⚔️🦆"
echo ""
echo "Monitor logs:"
echo "  tail -f aureon_key4.log"
echo "  tail -f aureon_key5.log"
echo "  tail -f aureon_key6.log"
echo "  tail -f aureon_key8.log"
echo "  tail -f aureon_key9.log"
echo ""
echo "Check all processes:"
echo "  ps aux | grep aureon_ultimate"
