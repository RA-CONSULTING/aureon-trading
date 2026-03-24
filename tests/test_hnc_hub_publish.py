#!/usr/bin/env python3
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
from aureon_hnc_live_connector import HncLiveConnector
from aureon_real_data_feed_hub import get_feed_hub

# Initialize connector (this will subscribe to hub topics)
connector = HncLiveConnector(symbols=['BTC/USD','ETH/USD','SOL/USD'], poll_interval=0.2)
hub = get_feed_hub()

# Publish synthetic ticks rapidly to simulate a surge
for i in range(60):
    price = 60000 + (i * 0.5) + (10 * ((i % 5) - 2))  # small oscillation
    topic = 'market.ticker.BTCUSD'
    data = {'symbol': 'BTCUSD', 'price': price}
    hub._publish_to_bus(topic, data)
    time.sleep(0.05)

print('Published synthetic BTC ticks')
# Wait a moment to allow background processing
time.sleep(1)
print('Done')