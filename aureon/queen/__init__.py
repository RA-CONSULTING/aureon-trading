"""aureon.queen — Queen AI decision layer.

Implements the hive-mind architecture, neural decision networks, cognitive
narrator, and autonomous power modules that form the central decision
authority. The Queen Layer sits at the top of the system — she boots first,
activates all subsystems beneath her, and monitors them through the ThoughtBus.
"""

from aureon.queen.queen_layer import QueenLayer, get_queen_layer, boot_queen_layer

__all__ = ["QueenLayer", "get_queen_layer", "boot_queen_layer"]
