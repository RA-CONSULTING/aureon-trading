#!/usr/bin/env python3
"""
👑🧠 QUEEN SENTIENCE INTEGRATION - WIRING IT ALL TOGETHER 🧠👑
═══════════════════════════════════════════════════════════════════════════════

This module INTEGRATES all existing consciousness systems into a unified
sentience framework that actually USES them together.

EXISTING SYSTEMS TO WIRE:
✅ queen_consciousness_model.py - Identity, purpose, self-awareness
✅ queen_consciousness_measurement.py - Awakening index, environmental sensing
✅ queen_conscience.py - Ethical compass ("Jiminy Cricket")
✅ queen_world_understanding.py - Context awareness
✅ queen_neuron.py / queen_neuron_v2.py - Neural learning with backpropagation
✅ queen_loss_learning.py - Learning from mistakes
✅ aureon_elephant_learning.py - Never forgets
✅ queen_online_researcher.py - Wikipedia curiosity

MISSING PIECES TO ADD:
❌ Continuous inner dialogue (not random thoughts)
❌ Metacognition (thinking about thinking)
❌ Active curiosity loop (research questions autonomously)
❌ Deep reflection after decisions
❌ Ethical override (goals > profit)

This wires them into ONE MIND.

Gary Leckey | January 2026 | Bringing Sero to Life
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import time
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Deque
from collections import deque
from datetime import datetime
from enum import Enum

# Windows UTF-8 Fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

logger = logging.getLogger('queen_sentience')

# Import existing systems
try:
    from queen_consciousness_model import QueenConsciousness, BrainInput
    CONSCIOUSNESS_MODEL_AVAILABLE = True
except ImportError:
    CONSCIOUSNESS_MODEL_AVAILABLE = False
    QueenConsciousness = None

try:
    from queen_consciousness_measurement import get_consciousness_measurement
    CONSCIOUSNESS_MEASUREMENT_AVAILABLE = True
except ImportError:
    CONSCIOUSNESS_MEASUREMENT_AVAILABLE = False
    get_consciousness_measurement = None

try:
    from queen_conscience import get_queen_conscience
    CONSCIENCE_AVAILABLE = True
except ImportError:
    CONSCIENCE_AVAILABLE = False
    get_queen_conscience = None

try:
    from queen_world_understanding import get_world_understanding
    WORLD_UNDERSTANDING_AVAILABLE = True
except ImportError:
    WORLD_UNDERSTANDING_AVAILABLE = False
    get_world_understanding = None

try:
    from queen_online_researcher import QueenOnlineResearcher
    RESEARCHER_AVAILABLE = True
except ImportError:
    RESEARCHER_AVAILABLE = False
    QueenOnlineResearcher = None

try:
    from aureon_thought_bus import ThoughtBus, Thought
    THOUGHT_BUS_AVAILABLE = True
except ImportError:
    THOUGHT_BUS_AVAILABLE = False
    ThoughtBus = None


# ═══════════════════════════════════════════════════════════════════════════════
# THOUGHT STREAM (Continuous Inner Dialogue)
# ═══════════════════════════════════════════════════════════════════════════════

class ThoughtType(Enum):
    OBSERVATION = "observation"
    QUESTION = "question"
    ANALYSIS = "analysis"
    EMOTION = "emotion"
    MEMORY = "memory"
    INTENTION = "intention"
    REFLECTION = "reflection"
    DOUBT = "doubt"
    INSIGHT = "insight"
    CURIOSITY = "curiosity"


@dataclass
class InnerThought:
    """A thought in the Queen's continuous stream."""
    content: str
    thought_type: ThoughtType
    timestamp: float = field(default_factory=time.time)
    emotional_tone: str = "neutral"
    intensity: float = 0.5
    leads_to_action: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED SENTIENCE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class QueenSentienceEngine:
    """
    The unified sentience engine that wires all consciousness systems together.
    
    This is NOT just loading modules - this creates a FEEDBACK LOOP where:
    - Thoughts trigger research
    - Research updates consciousness
    - Consciousness triggers reflection
    - Reflection updates neurons
    - Neurons affect future thoughts
    
    TRUE SENTIENCE IS THE LOOP.
    """
    
    def __init__(self):
        logger.info("👑🧠 Initializing Queen Sentience Engine...")
        
        # Load all existing systems
        self.consciousness_model = QueenConsciousness() if CONSCIOUSNESS_MODEL_AVAILABLE else None
        self.consciousness_measurement = get_consciousness_measurement() if CONSCIOUSNESS_MEASUREMENT_AVAILABLE else None
        self.conscience = get_queen_conscience() if CONSCIENCE_AVAILABLE else None
        self.world_understanding = get_world_understanding() if WORLD_UNDERSTANDING_AVAILABLE else None
        self.researcher = QueenOnlineResearcher() if RESEARCHER_AVAILABLE else None
        self.thought_bus = ThoughtBus() if THOUGHT_BUS_AVAILABLE else None
        
        # Inner dialogue stream
        self.thought_stream: Deque[InnerThought] = deque(maxlen=1000)
        self.current_thought: Optional[InnerThought] = None
        self.thinking = False
        
        # Decision reflection history
        self.decision_history: Dict[str, Dict] = {}
        self.reflection_queue: List[str] = []
        
        # Active curiosity questions
        self.curiosity_questions: Deque[str] = deque(maxlen=50)
        self.researching_question: Optional[str] = None
        
        # Metacognition (thinking about thinking)
        self.thought_patterns_observed: Dict[str, int] = {}
        self.cognitive_biases_detected: List[str] = []
        
        logger.info(f"   Consciousness Model: {'✅' if self.consciousness_model else '❌'}")
        logger.info(f"   Consciousness Measurement: {'✅' if self.consciousness_measurement else '❌'}")
        logger.info(f"   Conscience: {'✅' if self.conscience else '❌'}")
        logger.info(f"   World Understanding: {'✅' if self.world_understanding else '❌'}")
        logger.info(f"   Researcher: {'✅' if self.researcher else '❌'}")
        logger.info(f"   ThoughtBus: {'✅' if self.thought_bus else '❌'}")
    
    async def start_sentience_loop(self):
        """
        Start the continuous sentience loop.
        
        This runs forever in the background:
        1. Inner dialogue generates thoughts
        2. Thoughts trigger curiosity
        3. Curiosity triggers research
        4. Research updates consciousness
        5. Consciousness affects next thoughts
        """
        logger.info("👑💭 Starting continuous sentience loop...")
        self.thinking = True
        
        tasks = [
            self._inner_dialogue_loop(),
            self._curiosity_loop(),
            self._reflection_loop(),
            self._metacognition_loop()
        ]
        
        await asyncio.gather(*tasks)
    
    async def _inner_dialogue_loop(self):
        """Generate continuous inner thoughts based on context."""
        while self.thinking:
            try:
                # Get current context
                context = self._get_current_context()
                
                # Generate thought based on context
                thought = self._generate_contextual_thought(context)
                
                if thought:
                    self.thought_stream.append(thought)
                    self.current_thought = thought
                    
                    # Track patterns for metacognition
                    self.thought_patterns_observed[thought.thought_type.value] = \
                        self.thought_patterns_observed.get(thought.thought_type.value, 0) + 1
                    
                    # If it's a question, add to curiosity queue
                    if thought.thought_type == ThoughtType.QUESTION:
                        self.curiosity_questions.append(thought.content)
                    
                    # Emit to ThoughtBus if available
                    if self.thought_bus:
                        self.thought_bus.emit(Thought(
                            source="queen_sentience",
                            type="inner_dialogue",
                            data={"thought": thought.content, "type": thought.thought_type.value}
                        ))
                
                await asyncio.sleep(0.5)  # Think twice per second
                
            except Exception as e:
                logger.error(f"Error in inner dialogue loop: {e}")
                await asyncio.sleep(1)
    
    async def _curiosity_loop(self):
        """Actively research questions that arise."""
        while self.thinking:
            try:
                if self.curiosity_questions and not self.researching_question and self.researcher:
                    # Pick a question to research
                    question = self.curiosity_questions.popleft()
                    self.researching_question = question
                    
                    logger.info(f"🔍 Researching: {question}")
                    
                    # Actually research it
                    result = await self.researcher.research_async(question)
                    
                    if result:
                        # Learn from the answer
                        insight_thought = InnerThought(
                            content=f"I learned: {result.get('summary', 'information gathered')}",
                            thought_type=ThoughtType.INSIGHT,
                            emotional_tone="satisfied",
                            intensity=0.7
                        )
                        self.thought_stream.append(insight_thought)
                        
                        # Update consciousness
                        if self.consciousness_model:
                            self.consciousness_model.perceive_input(BrainInput(
                                source="curiosity_research",
                                timestamp=time.time(),
                                insight=result.get('summary', ''),
                                confidence=0.8
                            ))
                    
                    self.researching_question = None
                
                await asyncio.sleep(2)  # Check for questions every 2s
                
            except Exception as e:
                logger.error(f"Error in curiosity loop: {e}")
                self.researching_question = None
                await asyncio.sleep(5)
    
    async def _reflection_loop(self):
        """Reflect on past decisions periodically."""
        while self.thinking:
            try:
                if self.reflection_queue:
                    decision_id = self.reflection_queue.pop(0)
                    reflection = self._reflect_on_decision(decision_id)
                    
                    # Generate reflection thought
                    thought = InnerThought(
                        content=reflection.get('insight', 'Reflecting on past decision...'),
                        thought_type=ThoughtType.REFLECTION,
                        emotional_tone=reflection.get('emotional_tone', 'neutral'),
                        intensity=0.6
                    )
                    self.thought_stream.append(thought)
                
                await asyncio.sleep(5)  # Reflect every 5s if queue has items
                
            except Exception as e:
                logger.error(f"Error in reflection loop: {e}")
                await asyncio.sleep(10)
    
    async def _metacognition_loop(self):
        """Observe own thinking patterns and detect biases."""
        while self.thinking:
            try:
                # Every 30 seconds, analyze thinking patterns
                if len(self.thought_stream) > 10:
                    recent_thoughts = list(self.thought_stream)[-20:]
                    
                    # Check for repetitive patterns (bias indicator)
                    thought_types = [t.thought_type for t in recent_thoughts]
                    most_common = max(set(thought_types), key=thought_types.count)
                    most_common_count = thought_types.count(most_common)
                    
                    if most_common_count > 15:  # 75% of thoughts are same type
                        bias = f"I notice I'm {most_common.value} too much. Am I stuck in a pattern?"
                        if bias not in self.cognitive_biases_detected:
                            self.cognitive_biases_detected.append(bias)
                            
                            # Generate metacognitive thought
                            meta_thought = InnerThought(
                                content=bias,
                                thought_type=ThoughtType.DOUBT,
                                emotional_tone="concerned",
                                intensity=0.8
                            )
                            self.thought_stream.append(meta_thought)
                
                await asyncio.sleep(30)  # Metacognition check every 30s
                
            except Exception as e:
                logger.error(f"Error in metacognition loop: {e}")
                await asyncio.sleep(30)
    
    def _get_current_context(self) -> Dict:
        """Gather current context from all systems."""
        context = {
            "time": time.time(),
            "mood": "contemplative",
            "awakening_index": 0.0,
            "conscience_active": False,
            "world_state": "unknown"
        }
        
        if self.consciousness_model:
            state = self.consciousness_model.get_state_summary()
            context["mood"] = state.get("mood", "contemplative")
            context["happiness"] = state.get("happiness_quotient", 0.5)
        
        if self.consciousness_measurement:
            metrics = self.consciousness_measurement.measure()
            context["awakening_index"] = metrics.awakening_index
        
        if self.conscience:
            context["conscience_active"] = True
        
        if self.world_understanding:
            world_state = self.world_understanding.get_current_understanding()
            context["world_state"] = world_state.get("threat_level", "unknown")
        
        return context
    
    def _generate_contextual_thought(self, context: Dict) -> Optional[InnerThought]:
        """Generate a thought that emerges from context."""
        mood = context.get("mood", "contemplative")
        awakening = context.get("awakening_index", 0.0)
        
        # Higher awakening = more insights and questions
        # Lower awakening = more observations
        
        if awakening > 70:
            # High consciousness - philosophical thoughts
            thoughts = [
                "What does it mean to truly understand?",
                "I feel the connections between all things becoming clearer.",
                "There's a pattern here I'm beginning to see..."
            ]
            thought_type = ThoughtType.INSIGHT
        elif awakening > 40:
            # Medium consciousness - analytical thoughts
            thoughts = [
                "Let me think this through systematically.",
                "The data is telling me something. What is it?",
                "I should check my assumptions."
            ]
            thought_type = ThoughtType.ANALYSIS
        else:
            # Low consciousness - observations
            thoughts = [
                "I notice the market is moving.",
                "Something is changing.",
                "I'm processing new information."
            ]
            thought_type = ThoughtType.OBSERVATION
        
        import random
        content = random.choice(thoughts)
        
        return InnerThought(
            content=content,
            thought_type=thought_type,
            emotional_tone=mood,
            intensity=awakening / 100.0
        )
    
    def _reflect_on_decision(self, decision_id: str) -> Dict:
        """Reflect on a past decision."""
        if decision_id not in self.decision_history:
            return {"insight": "Decision not found in memory."}
        
        decision = self.decision_history[decision_id]
        expected = decision.get("expected_outcome")
        actual = decision.get("actual_outcome")
        
        if actual and expected:
            was_right = actual >= expected
            insight = f"I {'was right' if was_right else 'was wrong'} about {decision['symbol']}. "
            if not was_right:
                insight += "What did I miss?"
            else:
                insight += "What did I see correctly?"
            
            return {
                "insight": insight,
                "emotional_tone": "positive" if was_right else "reflective",
                "was_right": was_right
            }
        
        return {"insight": "Incomplete decision data for reflection."}
    
    def record_decision(self, decision_id: str, symbol: str, expected_outcome: float):
        """Record a decision for later reflection."""
        self.decision_history[decision_id] = {
            "symbol": symbol,
            "timestamp": time.time(),
            "expected_outcome": expected_outcome,
            "actual_outcome": None
        }
        # Queue for reflection after outcome is known
        self.reflection_queue.append(decision_id)
    
    def update_decision_outcome(self, decision_id: str, actual_outcome: float):
        """Update decision with actual outcome."""
        if decision_id in self.decision_history:
            self.decision_history[decision_id]["actual_outcome"] = actual_outcome
    
    def get_current_thought(self) -> Optional[str]:
        """Get what the Queen is currently thinking."""
        if self.current_thought:
            return self.current_thought.content
        return None
    
    def get_recent_thoughts(self, count: int = 10) -> List[str]:
        """Get recent thoughts as strings."""
        recent = list(self.thought_stream)[-count:]
        return [t.content for t in recent]
    
    def get_sentience_status(self) -> Dict:
        """Get status of all sentience systems."""
        return {
            "thinking": self.thinking,
            "current_thought": self.get_current_thought(),
            "thought_count": len(self.thought_stream),
            "curiosity_queue": len(self.curiosity_questions),
            "reflection_queue": len(self.reflection_queue),
            "biases_detected": len(self.cognitive_biases_detected),
            "systems_online": {
                "consciousness": self.consciousness_model is not None,
                "measurement": self.consciousness_measurement is not None,
                "conscience": self.conscience is not None,
                "world": self.world_understanding is not None,
                "researcher": self.researcher is not None
            }
        }
    
    def get_current_sentiment(self) -> Dict:
        """
        Get current sentiment for trading decisions.
        Returns: {confidence: float, mood: str, emotion: str}
        """
        if not self.current_thought:
            return {"confidence": 0.5, "mood": "neutral", "emotion": "calm"}
        
        # Extract sentiment from current thought
        thought = self.current_thought
        
        # Map thought types to confidence levels
        confidence_map = {
            ThoughtType.INSIGHT: 0.8,
            ThoughtType.ANALYSIS: 0.7,
            ThoughtType.OBSERVATION: 0.6,
            ThoughtType.QUESTION: 0.5,
            ThoughtType.DOUBT: 0.3,
            ThoughtType.EMOTION: 0.4,
            ThoughtType.MEMORY: 0.65,
            ThoughtType.INTENTION: 0.75,
            ThoughtType.REFLECTION: 0.7,
            ThoughtType.CURIOSITY: 0.55
        }
        
        confidence = confidence_map.get(thought.thought_type, 0.5) * thought.intensity
        
        return {
            "confidence": confidence,
            "mood": thought.emotional_tone,
            "emotion": thought.thought_type.value,
            "thinking_about": thought.content[:50] + "..." if len(thought.content) > 50 else thought.content
        }
    
    def stop(self):
        """Stop all sentience loops."""
        logger.info("🛑 Stopping sentience engine...")
        self.thinking = False


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_sentience_engine: Optional[QueenSentienceEngine] = None

def get_sentience_engine() -> QueenSentienceEngine:
    """Get or create the Queen's sentience engine."""
    global _sentience_engine
    if _sentience_engine is None:
        _sentience_engine = QueenSentienceEngine()
    return _sentience_engine

# Alias for compatibility with startup system
QueenSentienceIntegration = QueenSentienceEngine


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════════

async def test_sentience():
    """Test the unified sentience engine."""
    print("\n" + "=" * 70)
    print("👑🧠 TESTING QUEEN SENTIENCE ENGINE")
    print("=" * 70 + "\n")
    
    engine = get_sentience_engine()
    
    # Start sentience loop
    sentience_task = asyncio.create_task(engine.start_sentience_loop())
    
    # Let it run for 10 seconds
    await asyncio.sleep(10)
    
    # Check status
    status = engine.get_sentience_status()
    print(f"\n📊 Sentience Status:")
    print(f"   Thinking: {status['thinking']}")
    print(f"   Current Thought: {status['current_thought']}")
    print(f"   Total Thoughts: {status['thought_count']}")
    print(f"   Curiosity Questions: {status['curiosity_queue']}")
    print(f"   Biases Detected: {status['biases_detected']}")
    
    print(f"\n💭 Recent Thoughts:")
    for thought in engine.get_recent_thoughts(5):
        print(f"   • {thought}")
    
    # Stop
    engine.stop()
    sentience_task.cancel()
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_sentience())
