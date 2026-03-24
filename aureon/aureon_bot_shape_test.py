"""
Simple end-to-end test for BotShapeClassifier integration.
Run: python aureon_bot_shape_test.py
"""
from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import time
import math
from aureon_thought_bus import get_thought_bus, Thought
from aureon_whale_integration import get_latest_prediction

bus = get_thought_bus()

symbol = 'TESTCOIN/USD'
# publish synthetic market ticks (sine + noise)
for t in range(256):
    price = 100.0 + math.sin(t/4.0) * 0.5 + (0.01 * ((t%10)-5))
    th = Thought(source='test', topic='market.snapshot', payload={'symbol': symbol, 'price': price, 'ts': time.time()})
    bus.publish(th)
    time.sleep(0.002)

# publish orderbook analysis to trigger classification
analysis = {'symbol': symbol, 'detected_at': time.time(), 'walls': [{'price':100.0,'size':2000.0,'notional_usd':200000.0,'side':'bid'}], 'layering_score':0.2, 'bids_depth':200000.0, 'asks_depth':50000.0}
bus.publish(Thought(source='test', topic='whale.orderbook.analyzed', payload=analysis))

# wait for classifier and predictor to process
for i in range(6):
    p = get_latest_prediction(symbol)
    print('latest prediction', i, p)
    time.sleep(0.5)
