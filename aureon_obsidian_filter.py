"""
Aureon Obsidian Filter (Apache Tear Protocol)

This module implements a signal purification filter inspired by the metaphysical
and physical properties of Apache Tears (a type of black obsidian).

The core concept is to filter "market chaos" (high-frequency noise, sentiment
volatility, and entropic data) from the primary signal, enhancing the clarity
and coherence of the data before it enters the main probability nexus.

Obsidian's properties are metaphorically translated into digital signal processing:
- **Absorption of Negativity**: A low-pass filter to remove chaotic noise.
- **Grounding Energy**: A baseline stabilizer to prevent signal drift.
- **Revealing Truth (Sheen)**: A clarity function that enhances the signal-to-noise ratio.
- **Protection**: A shielding function that reduces the impact of negative sentiment spikes.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any

# --- Sacred Constants derived from Obsidian's properties ---
# Volcanic glass forms at ~1600-1700°C, cools rapidly. This is a thermal shock analog.
# Refractive index of obsidian is ~1.5. This is our core clarity scalar.
OBSIDIAN_REFRACTIVE_INDEX = 1.5
# Grounding frequency, related to the root chakra and Earth's core.
OBSIDIAN_GROUNDING_FREQ = 396.0  # Corresponds to a Solfeggio frequency for releasing fear

@dataclass
class ObsidianFilterState:
    """Stateful object to hold the filter's running parameters for an asset."""
    symbol: str
    chaos_accumulator: float = 0.0
    clarity_factor: float = 1.0
    last_price: float = 0.0
    is_stable: bool = True

class AureonObsidianFilter:
    """
    A filter that processes market data through the Apache Tear Protocol.
    """
    def __init__(self):
        self._filter_states: Dict[str, ObsidianFilterState] = {}
        print("🔮 Aureon Obsidian Filter (Apache Tear Protocol) initialized.")

    def _get_state(self, symbol: str) -> ObsidianFilterState:
        """Retrieve or create the state for a given symbol."""
        if symbol not in self._filter_states:
            self._filter_states[symbol] = ObsidianFilterState(symbol=symbol)
        return self._filter_states[symbol]

    def apply(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the Obsidian filter to a market data snapshot.

        The filter performs three main actions:
        1.  **Absorbs Chaos**: Identifies and quantifies market noise.
        2.  **Grounds Signal**: Stabilizes the price against excessive volatility.
        3.  **Enhances Clarity**: Improves the signal-to-noise ratio of core metrics.

        Args:
            symbol (str): The asset symbol (e.g., 'BTC/USD').
            market_data (Dict[str, Any]): A dictionary containing the latest market data,
                                          expected to have 'price', 'volume', 'volatility',
                                          and 'sentiment' keys.

        Returns:
            Dict[str, Any]: The filtered market data with chaos metrics added.
        """
        state = self._get_state(symbol)

        price = market_data.get('price', state.last_price)
        volatility = market_data.get('volatility', 0.0)
        sentiment = market_data.get('sentiment', 0.5) # 0=fear, 1=greed

        # 1. Absorb Chaos: Quantify noise from volatility and sentiment deviation
        # Rapid price changes and extreme sentiment are treated as "noise".
        price_delta = abs(price - state.last_price) if state.last_price > 0 else 0
        sentiment_deviation = abs(sentiment - 0.5) * 2 # Range [0, 1]
        
        # Chaos is a function of volatility, price movement, and sentiment extremity.
        chaos_signal = (volatility * 0.5) + (price_delta * 0.3) + (sentiment_deviation * 0.2)
        state.chaos_accumulator = (state.chaos_accumulator * 0.9) + (chaos_signal * 0.1) # Smooth accumulator

        # 2. Ground Signal: Apply a grounding factor based on the chaos level
        # The filter "grounds" the price by penalizing high chaos.
        grounding_factor = 1 / (1 + state.chaos_accumulator)
        
        # 3. Enhance Clarity: Use refractive index to boost signal-to-noise
        # The "sheen" of obsidian reveals the true signal within the noise.
        signal_to_noise = grounding_factor / (state.chaos_accumulator + 1e-9)
        state.clarity_factor = np.clip(signal_to_noise * OBSIDIAN_REFRACTIVE_INDEX, 0.1, 5.0)

        # Update state
        state.last_price = price
        state.is_stable = state.chaos_accumulator < 0.5

        # Create the filtered output
        filtered_data = market_data.copy()
        filtered_data['obsidian_chaos'] = state.chaos_accumulator
        filtered_data['obsidian_clarity'] = state.clarity_factor
        filtered_data['obsidian_grounding'] = grounding_factor
        
        # The primary output: a "clarified" price and coherence score
        # The original price is modulated by the clarity factor.
        # A clear signal is closer to the true price; a chaotic one is dampened.
        clarity_adjustment = (state.clarity_factor - 1) * 0.1 # Dampen the effect
        filtered_data['clarified_price'] = price * (1 + clarity_adjustment)
        
        # Boost coherence if the signal is clear and stable
        if state.is_stable and state.clarity_factor > 1.5:
            coherence_boost = np.log1p(state.clarity_factor - 1.5) * 0.1
            filtered_data['coherence'] = min(1.0, market_data.get('coherence', 0.5) + coherence_boost)

        return filtered_data

# --- Example Usage ---
if __name__ == '__main__':
    obsidian_filter = AureonObsidianFilter()

    # Simulate some market data
    market_snapshot_stable = {
        'price': 50000,
        'volume': 1000,
        'volatility': 0.05,
        'sentiment': 0.6, # Calm
        'coherence': 0.8
    }

    market_snapshot_chaotic = {
        'price': 52000,
        'volume': 5000,
        'volatility': 0.8,
        'sentiment': 0.1, # Extreme fear
        'coherence': 0.4
    }

    print("--- Applying filter to STABLE market data ---")
    filtered_stable = obsidian_filter.apply('BTC/USD', market_snapshot_stable)
    print(f"Original Price: {market_snapshot_stable['price']}, Clarified Price: {filtered_stable['clarified_price']:.2f}")
    print(f"Chaos: {filtered_stable['obsidian_chaos']:.4f}, Clarity: {filtered_stable['obsidian_clarity']:.4f}")
    print(f"Original Coherence: {market_snapshot_stable['coherence']}, New Coherence: {filtered_stable.get('coherence', market_snapshot_stable['coherence']):.4f}")

    print("\n--- Applying filter to CHAOTIC market data ---")
    # Apply again to simulate a subsequent tick
    filtered_chaotic = obsidian_filter.apply('BTC/USD', market_snapshot_chaotic)
    print(f"Original Price: {market_snapshot_chaotic['price']}, Clarified Price: {filtered_chaotic['clarified_price']:.2f}")
    print(f"Chaos: {filtered_chaotic['obsidian_chaos']:.4f}, Clarity: {filtered_chaotic['obsidian_clarity']:.4f}")
    print(f"Original Coherence: {market_snapshot_chaotic['coherence']}, New Coherence: {filtered_chaotic.get('coherence', market_snapshot_chaotic['coherence']):.4f}")
