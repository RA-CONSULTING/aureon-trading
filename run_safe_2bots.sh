#!/bin/bash
# 🦆⚔️ SAFE 2-BOT SETUP - Stay under rate limits ⚔️🦆

pkill -f aureon_ultimate.py
sleep 3

echo "🦆⚔️ LAUNCHING 2 BOTS (Keys 4 & 5) ⚔️🦆"
echo "Rate limit safe: ~2400/min vs 6000 limit"
echo ""

# Bot 1 - Key 4
export BINANCE_API_KEY="92nqB9iH4JLDCNY9tGZEW3OuEcM9L9oknJJGRlJH03WIkkO8TkvbYRzoyFUbJdfL"
export BINANCE_API_SECRET="KgaBXEmUV4xKTREww0W5vfNoAYHfNwBryUInzTQZHqjfsEIcFMquzANchTreKEWH"
export BINANCE_USE_TESTNET=false
export BINANCE_DRY_RUN=false
nohup python aureon_ultimate.py > aureon_key4.log 2>&1 &
echo "✅ Bot 1 (Key 4) - PID: $!"

sleep 15

# Bot 2 - Key 5  
export BINANCE_API_KEY="lImzLyev2qdfWnO8WVfXYhAbvR9JKX9rTI7fGjPvSimhY7x0my3Ivg5GNWwv2HgL"
export BINANCE_API_SECRET="kvaNjghikzWE77Outg7bmXKO8fmi404VU9Hp6anRcNG3GZEntb9MrohpK3rizIdu"
nohup python aureon_ultimate.py > aureon_key5.log 2>&1 &
echo "✅ Bot 2 (Key 5) - PID: $!"

echo ""
echo "🦆⚔️ 2 BOTS DEPLOYED! ⚔️🦆"
echo "Total capacity: 14 positions (7 each)"
echo ""
echo "Monitor: tail -f aureon_key4.log aureon_key5.log"
