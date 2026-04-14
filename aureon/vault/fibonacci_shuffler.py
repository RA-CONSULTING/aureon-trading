"""
FibonacciCardShuffler — Golden-Ratio Replay Mechanism
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Learns like shuffling Fibonacci cards."

The shuffler takes a set of VaultContent cards and reorders them for
replay using golden-ratio-spaced selection. Each replay pass:

  • walks the deck with Fibonacci strides (1, 1, 2, 3, 5, 8, 13, ...)
    wrapped modulo deck size
  • biases the walk toward high love_weight cards
  • produces a deck in which no two adjacent cards are boringly close

The stride pattern means the same replay is never a trivial permutation
of the previous one — each pass exposes different neighbourhood structure.
"""

from __future__ import annotations

import math
import random
from typing import Iterable, List

# Reuse the Fibonacci intervals already defined for the swarm snapper,
# but fall back to a local copy if that import fails.
try:
    from aureon.swarm_motion.fibonacci_snapper import FIBONACCI_INTERVALS, PHI
except Exception:
    FIBONACCI_INTERVALS = [1.0, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0, 34.0, 55.0, 89.0, 144.0]
    PHI = (1.0 + math.sqrt(5.0)) / 2.0

# Integer Fibonacci sequence used for the walker (distinct from the
# FIBONACCI_INTERVALS which is float-seconds for the snapper).
FIB_STEPS: List[int] = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]


class FibonacciCardShuffler:
    """
    Reorders a list of cards with golden-ratio-spaced replay.

    Usage:
        s = FibonacciCardShuffler(love_bias=1.0)
        deck = s.shuffle(cards)
    """

    def __init__(
        self,
        love_bias: float = 1.0,
        rng_seed: int = None,
    ):
        self.love_bias = float(love_bias)
        self._rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

    def shuffle(self, cards: Iterable) -> List:
        """
        Return the cards in Fibonacci-stride order, biased by love_weight.

        The walker starts at a pseudo-random position, then takes steps
        along the Fibonacci sequence (mod deck size). Cards with high
        love_weight get a chance to "jump the queue".
        """
        deck = list(cards)
        n = len(deck)
        if n <= 1:
            return deck

        # Sort the deck by love_weight ∈ [0, 1] so higher love tends
        # to land earlier in the walker's path (weighted by love_bias)
        if self.love_bias > 0:
            deck.sort(
                key=lambda c: getattr(c, "love_weight", 0.0) * self.love_bias,
                reverse=True,
            )

        # Build an output deck using Fibonacci stride walking
        used = [False] * n
        ordered: List = []
        position = self._rng.randrange(n)
        step_idx = 0

        # Emit until every card has been seen once
        attempts = 0
        max_attempts = n * 10
        while len(ordered) < n and attempts < max_attempts:
            attempts += 1
            if not used[position]:
                ordered.append(deck[position])
                used[position] = True
            step = FIB_STEPS[step_idx % len(FIB_STEPS)]
            step_idx += 1
            position = (position + step) % n

        # Fill in any stragglers (shouldn't happen but safety net)
        if len(ordered) < n:
            for i in range(n):
                if not used[i]:
                    ordered.append(deck[i])
                    used[i] = True

        return ordered

    def stride_sequence(self, length: int) -> List[int]:
        """Return the stride walker's positions for a deck of given length."""
        if length <= 0:
            return []
        seq = []
        position = 0
        for i in range(length):
            seq.append(position)
            step = FIB_STEPS[i % len(FIB_STEPS)]
            position = (position + step) % length
        return seq

    @staticmethod
    def phi() -> float:
        """Return the golden ratio constant used by the shuffler."""
        return PHI
