from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
from typing import Optional
from aureon_enigma_dream import DreamEngine

class DreamScheduler:
    """Decides when the Queen should dream."""

    def __init__(self, dream_engine: DreamEngine, idle_threshold_seconds: int = 300, volatility_threshold: float = 0.5):
        self.dream_engine = dream_engine
        self.idle_threshold_seconds = idle_threshold_seconds
        self.volatility_threshold = volatility_threshold
        self.last_activity_timestamp: float = time.time()

    def notify_activity(self):
        """Notifies the scheduler of system activity."""
        self.last_activity_timestamp = time.time()

    def should_dream(self, current_volatility: float) -> bool:
        """
        Determines if the system should enter a dream state.
        Dreams are initiated during periods of low market volatility and system inactivity.
        """
        is_low_volatility = current_volatility < self.volatility_threshold
        is_idle = (time.time() - self.last_activity_timestamp) > self.idle_threshold_seconds

        if is_low_volatility and is_idle:
            return True
        return False

    def run(self, current_volatility: float):
        """Runs the dream scheduler, initiating a dream cycle if conditions are met."""
        if self.should_dream(current_volatility):
            print("Dream conditions met. Initiating dream cycle...")
            # Reset activity timestamp to prevent immediate re-dreaming
            self.notify_activity()
            # Initiate a dream cycle. Let's start with a REM dream for consolidation.
            self.dream_engine.run_rem_dream_cycle()
