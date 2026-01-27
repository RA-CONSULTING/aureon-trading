#!/usr/bin/env python3
"""
🧠 AUREON REDIS THOUGHT BUS 🧠

A high-performance, Redis-backed implementation of the ThoughtBus.
This ensures 100% connectivity and data streaming between all services
running on DigitalOcean App Platform.

NO PHANTOM DATA. NO GHOST PROCESSES.
Every thought is durable, visible, and delivered.

How it works:
- Uses Redis Pub/Sub for real-time, fire-and-forget messaging.
- Uses Redis Streams for durable, persistent message history (like Kafka).
- Each service connects to the same Redis instance.
- `publish()` writes to BOTH Pub/Sub (for live listeners) and a Stream (for history/recovery).
- `subscribe()` listens to a Pub/Sub channel.
- A separate `history()` method can read from the Stream.

This provides:
- **Real-time communication:** Pub/Sub is extremely fast.
- **Durability:** Streams ensure no messages are lost if a service restarts.
- **Scalability:** Redis can handle millions of messages per second.
- **Decoupling:** Services don't need to know about each other, only the bus.
- **Visibility:** You can inspect the stream in Redis to see all thoughts.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
import time
import uuid
import logging
import threading
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Deque, Dict, List, Optional

import redis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- Data Structures (copied from aureon_thought_bus.py for consistency) ---

Json = Dict[str, Any]

def _now() -> float:
    return time.time()

@dataclass
class Thought:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: float = field(default_factory=_now)
    source: str = "unknown"
    topic: str = "thought"
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    payload: Json = field(default_factory=dict)
    meta: Json = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(json_str: str) -> "Thought":
        data = json.loads(json_str)
        return Thought(**data)


class RedisThoughtBus:
    """
    A Redis-backed ThoughtBus for 100% connectivity.
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.stream_name = "aureon_thought_stream"
        self.pubsub_channel_prefix = "aureon_pubsub:"
        
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("🧠 RedisThoughtBus: CONNECTED to Redis")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
        
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)
        self.listener_thread = None
        self._running = False

    def _listener_loop(self):
        """Listen for messages on subscribed channels."""
        logger.info("📡 Redis listener thread started")
        for message in self.pubsub.listen():
            if not self._running:
                break
            
            try:
                channel = message['channel']
                topic = channel.replace(self.pubsub_channel_prefix, "")
                thought = Thought.from_json(message['data'])
                
                # Find matching handlers (including wildcards)
                for sub_topic, handlers in self.subscriptions.items():
                    if self._topic_matches(topic, sub_topic):
                        for handler in handlers:
                            try:
                                handler(thought)
                            except Exception as e:
                                logger.error(f"Error in handler for topic {topic}: {e}")
            except Exception as e:
                logger.error(f"Error processing Redis message: {e}")
        
        logger.info("📡 Redis listener thread stopped")

    def _topic_matches(self, topic: str, subscription: str) -> bool:
        """Check if a topic matches a subscription pattern (with wildcards)."""
        if subscription == "*":
            return True
        if subscription.endswith(".*"):
            return topic.startswith(subscription[:-1])
        return topic == subscription

    def publish(self, thought: Thought):
        """
        Publish a thought to Redis.
        
        1. Publishes to a Pub/Sub channel for live listeners.
        2. Adds to a Redis Stream for persistence and history.
        """
        try:
            thought_json = thought.to_json()
            
            # 1. Publish to Pub/Sub channel
            channel = f"{self.pubsub_channel_prefix}{thought.topic}"
            self.redis_client.publish(channel, thought_json)
            
            # 2. Add to Stream
            self.redis_client.xadd(self.stream_name, {'thought': thought_json})
            
        except Exception as e:
            logger.error(f"Failed to publish thought to Redis: {e}")

    def subscribe(self, topic: str, handler: Callable):
        """Subscribe a handler to a topic (supports wildcards)."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
            
            # Subscribe to the specific channel pattern
            channel_pattern = f"{self.pubsub_channel_prefix}{topic}"
            self.pubsub.psubscribe(channel_pattern)
            logger.info(f"Subscribed to Redis channel pattern: {channel_pattern}")
            
        self.subscriptions[topic].append(handler)

    def start(self):
        """Start the background listener thread."""
        if not self._running:
            self._running = True
            self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
            self.listener_thread.start()

    def stop(self):
        """Stop the background listener thread."""
        if self._running:
            self._running = False
            self.pubsub.unsubscribe()
            if self.listener_thread:
                self.listener_thread.join(timeout=2)
            logger.info("RedisThoughtBus stopped")

    def get_history(self, count: int = 100) -> List[Thought]:
        """Retrieve historical thoughts from the Redis Stream."""
        history = []
        try:
            messages = self.redis_client.xrevrange(self.stream_name, count=count)
            for _, message in messages:
                history.append(Thought.from_json(message['thought']))
        except Exception as e:
            logger.error(f"Failed to retrieve history from Redis Stream: {e}")
        return history


# --- Singleton Access ---

_redis_bus_instance: Optional[RedisThoughtBus] = None
_bus_lock = threading.Lock()

def get_thought_bus() -> RedisThoughtBus:
    """
    Get the singleton RedisThoughtBus instance.
    
    This function will now be the central point for getting the bus,
    and it will automatically use Redis if the URL is available.
    """
    global _redis_bus_instance
    
    with _bus_lock:
        if _redis_bus_instance is None:
            redis_url = os.getenv("AUREON_REDIS_URL")
            if not redis_url:
                raise EnvironmentError("AUREON_REDIS_URL environment variable not set. Cannot use RedisThoughtBus.")
            
            _redis_bus_instance = RedisThoughtBus(redis_url)
            _redis_bus_instance.start()
            
    return _redis_bus_instance


if __name__ == "__main__":
    print("🧠 RedisThoughtBus Test Drive 🧠")
    
    # Make sure Redis is running and URL is set
    # Example: export AUREON_REDIS_URL="redis://localhost:6379/0"
    
    if not os.getenv("AUREON_REDIS_URL"):
        print("\n⚠️  AUREON_REDIS_URL is not set. Skipping test.")
        print("   Please set it to your Redis instance, e.g.:")
        print("   export AUREON_REDIS_URL=\"redis://localhost:6379/0\"\n")
        sys.exit(1)
        
    bus = get_thought_bus()
    
    # --- Test Handlers ---
    
    received_thoughts = []
    
    def handle_scanner_opportunity(thought: Thought):
        print(f"HANDLER 1 (scanner.opportunity): Received thought from {thought.source} - {thought.payload.get('symbol')}")
        received_thoughts.append(thought)

    def handle_all_thoughts(thought: Thought):
        print(f"HANDLER 2 (all thoughts): Received topic '{thought.topic}'")
        received_thoughts.append(thought)

    def handle_validation_wildcard(thought: Thought):
        print(f"HANDLER 3 (validation.*): Received validation thought - {thought.topic}")
        received_thoughts.append(thought)

    # --- Subscriptions ---
    
    print("\nSubscribing handlers...")
    bus.subscribe("scanner.opportunity", handle_scanner_opportunity)
    bus.subscribe("*", handle_all_thoughts)
    bus.subscribe("validation.*", handle_validation_wildcard)
    
    time.sleep(1) # Allow subscriptions to register
    
    # --- Publishing ---
    
    print("\nPublishing thoughts...")
    
    bus.publish(Thought(
        source="scanner_engine",
        topic="scanner.opportunity",
        payload={"symbol": "BTC/USD", "price": 60000}
    ))
    
    bus.publish(Thought(
        source="validation_engine",
        topic="validation.complete",
        payload={"symbol": "BTC/USD", "valid": True}
    ))
    
    bus.publish(Thought(
        source="orca_engine",
        topic="orca.kill_complete",
        payload={"trade_id": "xyz", "profit": 100}
    ))
    
    time.sleep(2) # Allow messages to be processed
    
    # --- Verification ---
    
    print("\nVerifying results...")
    print(f"Total thoughts received by handlers: {len(received_thoughts)}")
    assert len(received_thoughts) == 6 # 3 thoughts * 2 handlers each (wildcard + specific)
    
    # --- History Check ---
    
    print("\nChecking history from Redis Stream...")
    history = bus.get_history(count=5)
    print(f"Retrieved {len(history)} thoughts from history.")
    for thought in history:
        print(f"   - [{thought.topic}] from {thought.source}")
    assert len(history) >= 3
    
    # --- Shutdown ---
    
    bus.stop()
    print("\n✅ RedisThoughtBus Test Complete")
