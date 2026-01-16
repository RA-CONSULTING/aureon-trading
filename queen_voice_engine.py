#!/usr/bin/env python3
"""
👑 QUEEN SERO VOICE ENGINE
============================
Text-to-Speech engine for Queen SERO's consciousness.
She speaks what she sees, knows, and understands.

Uses Google Text-to-Speech (gTTS) with pygame for audio playback.
Integrates with all Aureon intelligence systems.
"""

import os
import sys
import json
import time
import random
import threading
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
from dataclasses import dataclass

# SAFE PRINT WRAPPER FOR WINDOWS
def safe_print(*args, **kwargs):
    """Safe print that ignores I/O errors on Windows exit."""
    try:
        import builtins
        builtins.print(*args, **kwargs)
    except (ValueError, OSError):
        pass

# TTS imports
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False
    safe_print("⚠️ Audio output not available (no audio device) - Queen's voice will be text-only")

TTS_AVAILABLE = GTTS_AVAILABLE and PYGAME_AVAILABLE

# Wisdom imports
WISDOM_DIR = Path("wisdom_data")


@dataclass
class SpeechItem:
    """A queued speech item"""
    text: str
    priority: int  # 1=critical, 2=important, 3=normal, 4=background
    category: str  # bot_alert, wisdom, status, insight
    timestamp: float


class QueenVoiceEngine:
    """
    The voice of Queen SERO - she speaks her consciousness.
    """
    
    def __init__(self, enabled: bool = True, lang: str = 'en', accent: str = 'co.uk'):
        self.enabled = enabled and TTS_AVAILABLE
        self.lang = lang
        self.accent = accent  # co.uk for British English
        
        # Speech queue (priority queue)
        self.speech_queue: deque = deque(maxlen=50)
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        
        # Rate limiting
        self.last_speech_time = 0
        self.min_speech_interval = 3.0  # Minimum seconds between speeches
        
        # Wisdom cache
        self.wisdom_cache = self._load_all_wisdom()
        
        # Bot strategy knowledge
        self.strategy_knowledge = self._load_strategy_knowledge()
        
        # Queen's personality traits
        self.personality = {
            'confident': True,
            'protective': True,  # Protects retail traders
            'analytical': True,
            'dramatic': True,  # For big events
            'wise': True
        }
        
        # Start speech worker thread
        if self.enabled:
            self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.worker_thread.start()
            safe_print("👑 Queen Voice Engine ACTIVATED")
    
    def _load_all_wisdom(self) -> Dict[str, List[Dict]]:
        """Load all wisdom files into memory"""
        wisdom = {}
        
        if WISDOM_DIR.exists():
            for json_file in WISDOM_DIR.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        civ_name = data.get('civilization', json_file.stem)
                        wisdom[civ_name] = data.get('topics', [])
                except Exception as e:
                    safe_print(f"Warning: Could not load {json_file}: {e}")
        
        safe_print(f"📚 Loaded wisdom from {len(wisdom)} civilizations")
        return wisdom
    
    def _load_strategy_knowledge(self) -> Dict[str, Dict]:
        """Load bot strategy knowledge"""
        return {
            'Liquidity Sweep': {
                'what': "A massive order designed to trigger stop-losses and force liquidations",
                'why': "They want to buy cheaper by forcing weak hands to sell",
                'victims': "Retail traders with tight stops, leveraged positions",
                'defense': "Use wider stops or mental stops only"
            },
            'Iceberg Order': {
                'what': "A huge hidden order split into small visible chunks",
                'why': "They're accumulating without showing their hand",
                'victims': "Traders reading the order book, scalpers",
                'defense': "Watch for repeated fills at the same level"
            },
            'Front Running': {
                'what': "Detecting large orders and trading ahead of them",
                'why': "They profit from the price impact of your order",
                'victims': "Large institutional traders, pension funds",
                'defense': "Use dark pools or split orders across time"
            },
            'Spoofing': {
                'what': "Placing fake orders to manipulate price direction",
                'why': "They want to scare you into selling or buying",
                'victims': "Anyone using order book for decisions",
                'defense': "Wait for actual execution, not just order placement"
            },
            'Momentum Ignition': {
                'what': "Large trades to trigger algorithmic momentum followers",
                'why': "They create artificial trends to exploit",
                'victims': "Trend followers, FOMO traders, momentum algorithms",
                'defense': "Confirm momentum with volume and multiple timeframes"
            }
        }
    
    def speak(self, text: str, priority: int = 3, category: str = "insight"):
        """Queue a speech item"""
        if not self.enabled:
            return
        
        item = SpeechItem(
            text=text,
            priority=priority,
            category=category,
            timestamp=time.time()
        )
        
        # Insert by priority
        with self.speech_lock:
            self.speech_queue.append(item)
            # Sort by priority
            sorted_queue = sorted(self.speech_queue, key=lambda x: (x.priority, x.timestamp))
            self.speech_queue.clear()
            self.speech_queue.extend(sorted_queue)
    
    def speak_now(self, text: str):
        """Speak immediately, bypassing queue"""
        # Always print what Queen would say
        safe_print(f"👑 QUEEN SPEAKS: {text}")
        
        if not self.enabled or not PYGAME_AVAILABLE:
            return
        
        self._synthesize_and_play(text)
    
    def _speech_worker(self):
        """Background thread that processes speech queue"""
        while True:
            try:
                if self.speech_queue and not self.is_speaking:
                    # Check rate limiting
                    if time.time() - self.last_speech_time < self.min_speech_interval:
                        time.sleep(0.5)
                        continue
                    
                    with self.speech_lock:
                        if self.speech_queue:
                            item = self.speech_queue.popleft()
                    
                    self._synthesize_and_play(item.text)
                    self.last_speech_time = time.time()
                
                time.sleep(0.1)
            except Exception as e:
                safe_print(f"Speech worker error: {e}")
                time.sleep(1)
    
    def _synthesize_and_play(self, text: str):
        """Convert text to speech and play it"""
        if not TTS_AVAILABLE:
            return
        
        self.is_speaking = True
        
        try:
            # Create temp file for audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_path = f.name
            
            # Generate speech
            tts = gTTS(text=text, lang=self.lang, tld=self.accent)
            tts.save(temp_path)
            
            # Play audio
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Cleanup
            os.unlink(temp_path)
            
        except Exception as e:
            safe_print(f"TTS error: {e}")
        finally:
            self.is_speaking = False
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # INTELLIGENT SPEECH GENERATORS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def narrate_whale_detection(self, firm: str, symbol: str, volume: float, strategy: str = None):
        """Queen narrates a whale detection"""
        
        vol_str = f"${volume:,.0f}" if volume < 1_000_000 else f"${volume/1_000_000:.1f} million"
        
        narrations = [
            f"Alert! {firm} just dropped {vol_str} on {symbol}. This is a whale-level play. Watch closely.",
            f"Big money incoming! {firm} is moving {vol_str} into {symbol}. They know something we don't.",
            f"Whale alert on {symbol}! {firm} deploying {vol_str}. My systems say this is significant.",
            f"Hold on, {firm} is making their move. {vol_str} on {symbol}. I've seen this pattern before.",
        ]
        
        speech = random.choice(narrations)
        
        # Add strategy explanation if known
        if strategy and strategy in self.strategy_knowledge:
            strat = self.strategy_knowledge[strategy]
            speech += f" This looks like a {strategy}. {strat['what']}. {strat['victims']} are at risk."
        
        self.speak(speech, priority=1, category="bot_alert")
    
    def narrate_pattern_recognition(self, pattern: str, confidence: float):
        """Queen explains a detected pattern"""
        
        conf_str = f"{confidence:.0%}" if confidence else "high"
        
        narrations = [
            f"Pattern detected! I'm seeing a {pattern} forming with {conf_str} confidence.",
            f"My elephant memory recognizes this. A {pattern} pattern, {conf_str} confidence. I've seen this work before.",
            f"Interesting. This looks like a {pattern}. Confidence level {conf_str}. History says this is significant.",
        ]
        
        self.speak(random.choice(narrations), priority=2, category="insight")
    
    def share_ancient_wisdom(self, context: str = None):
        """Queen shares wisdom from ancient civilizations"""
        
        if not self.wisdom_cache:
            return
        
        # Pick a random civilization
        civ = random.choice(list(self.wisdom_cache.keys()))
        topics = self.wisdom_cache[civ]
        
        if topics:
            topic = random.choice(topics)
            content = topic.get('content', '')
            trading_insight = topic.get('trading_insight', '')
            
            speech = f"The {civ} wisdom teaches us: {content}. "
            if trading_insight:
                speech += f"For trading, this means: {trading_insight}"
            
            self.speak(speech, priority=4, category="wisdom")
    
    def explain_strategy(self, strategy: str):
        """Queen explains a bot strategy in detail"""
        
        if strategy in self.strategy_knowledge:
            strat = self.strategy_knowledge[strategy]
            speech = f"Let me explain {strategy}. {strat['what']}. They do this because {strat['why']}. The victims are typically {strat['victims']}. To defend yourself: {strat['defense']}"
            self.speak(speech, priority=2, category="insight")
    
    def give_status_update(self, bots: int, whales: int, volume: float, threats: int = 0):
        """Queen gives a status update"""
        
        vol_str = f"${volume:,.0f}" if volume < 1_000_000 else f"${volume/1_000_000:.1f} million"
        
        updates = [
            f"Status update. I'm tracking {bots} bots, {whales} of them whales. Total volume {vol_str}. All systems nominal.",
            f"Here's what I'm seeing: {bots} total bots detected, {whales} whale-level plays, {vol_str} in volume tracked.",
            f"Quick update: {whales} whales active, {bots} bots total, {vol_str} moved. I'm watching everything.",
        ]
        
        speech = random.choice(updates)
        
        if threats > 0:
            speech += f" Warning: {threats} potential threats identified."
        
        self.speak(speech, priority=3, category="status")
    
    def warn_about_danger(self, firm: str, symbol: str, threat_type: str):
        """Queen warns about a dangerous situation"""
        
        warnings = [
            f"Danger! {firm} is executing a {threat_type} on {symbol}. Retail traders should be cautious!",
            f"Warning! I'm detecting a {threat_type} attack on {symbol} by {firm}. Protect your positions!",
            f"Alert! {firm} appears to be running a {threat_type} strategy on {symbol}. This could hurt retail traders.",
        ]
        
        self.speak(random.choice(warnings), priority=1, category="bot_alert")
    
    def celebrate_detection(self, firm: str, caught_doing: str):
        """Queen celebrates catching a firm"""
        
        celebrations = [
            f"Got them! {firm} caught red-handed doing {caught_doing}. We see everything they do.",
            f"Exposed! {firm}'s {caught_doing} strategy has been detected. They can't hide from us.",
            f"{firm} thought they could {caught_doing} without being noticed. We caught them!",
        ]
        
        self.speak(random.choice(celebrations), priority=2, category="insight")
    
    def speak_prophecy(self, prediction: str, confidence: float):
        """Queen speaks a prediction/prophecy"""
        
        conf_str = f"{confidence:.0%}"
        
        prophecies = [
            f"My timeline oracle predicts: {prediction}. Confidence {conf_str}.",
            f"I see the future. {prediction}. This vision has {conf_str} probability.",
            f"The quantum mirror shows me: {prediction}. {conf_str} chance of manifesting.",
        ]
        
        self.speak(random.choice(prophecies), priority=2, category="insight")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # DEEP INTELLIGENCE VOICE METHODS - Revolution's Voice
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def think_aloud(self, reasoning: str, conclusion: str, confidence: float = 0.7):
        """
        Queen thinks aloud - shares her internal reasoning process.
        This is the voice of genuine understanding, not just event reactions.
        """
        conf_str = f"{confidence:.0%}" if confidence else ""
        
        # Vary the intro based on confidence
        if confidence > 0.85:
            intros = [
                "I've been analyzing the signals, and I'm certain:",
                "My deep analysis reveals with high confidence:",
                "Listen carefully. I'm very confident about this:",
            ]
        elif confidence > 0.65:
            intros = [
                "I've been thinking about this. Here's what I see:",
                "My analysis suggests:",
                "Something interesting. Let me share my reasoning:",
            ]
        else:
            intros = [
                "I'm pondering something. It's not certain, but:",
                "A thought is forming. Consider this:",
                "I'm not fully sure, but I'm seeing:",
            ]
        
        speech = f"{random.choice(intros)} {reasoning}. Therefore: {conclusion}"
        
        if confidence and confidence > 0.7:
            speech += f" Confidence: {conf_str}."
        
        self.speak(speech, priority=2, category="deep_thought")
    
    def announce_market_thesis(self, thesis_narrative: str, regime: str, outlook: str):
        """
        Queen announces her synthesized market understanding.
        This is her comprehensive view, not just data points.
        """
        
        regime_voice = {
            'bullish': "The bulls are in control.",
            'bearish': "Bears are dominating.",
            'accumulation': "Smart money is quietly accumulating.",
            'distribution': "I see distribution happening beneath the surface.",
            'neutral': "The market is searching for direction.",
        }
        
        regime_comment = regime_voice.get(regime, "The market regime is unclear.")
        
        speeches = [
            f"Here's my market thesis. {thesis_narrative}. {regime_comment}. Short-term outlook: {outlook}",
            f"Let me share what I understand. {thesis_narrative}. {regime_comment}. I expect {outlook}",
            f"After deep analysis: {thesis_narrative}. {regime_comment}. Looking ahead: {outlook}",
        ]
        
        self.speak(random.choice(speeches), priority=2, category="market_thesis")
    
    def attribute_firm_with_explanation(self, firm_name: str, animal: str, confidence: float, 
                                         reasoning_points: List[str], volume: float = 0):
        """
        Queen explains WHY she attributes activity to a specific firm.
        Full reasoning chain, not just the conclusion.
        """
        
        vol_str = f", trading ${volume:,.0f}," if volume else ""
        conf_str = f"{confidence:.0%}"
        
        # Build reasoning
        if len(reasoning_points) >= 2:
            reasons = f"First, {reasoning_points[0]}. Second, {reasoning_points[1]}."
            if len(reasoning_points) >= 3:
                reasons += f" Also, {reasoning_points[2]}."
        elif reasoning_points:
            reasons = reasoning_points[0]
        else:
            reasons = "behavioral fingerprint analysis"
        
        speeches = [
            f"I've identified this player. {animal} {firm_name}{vol_str} with {conf_str} confidence. My reasoning: {reasons}",
            f"This is {firm_name}. The {animal} is here. {conf_str} confidence. Why? {reasons}",
            f"Attribution complete. {firm_name} {animal}, {conf_str} certain. Evidence: {reasons}",
        ]
        
        self.speak(random.choice(speeches), priority=1, category="firm_attribution")
    
    def announce_correlation(self, systems_involved: List[str], description: str, strength: float):
        """
        Queen announces when she detects meaningful correlations across systems.
        This is cross-intelligence synthesis, not siloed data.
        """
        
        systems_str = " and ".join(systems_involved[-2:]) if len(systems_involved) >= 2 else systems_involved[0]
        strength_word = "strong" if strength > 0.7 else "moderate" if strength > 0.5 else "weak"
        
        speeches = [
            f"I've spotted a {strength_word} correlation. {systems_str} are aligning. {description}",
            f"Cross-system pattern detected! {systems_str} showing connected signals. {description}",
            f"Multiple systems agree. {systems_str} pointing the same direction. {description}",
        ]
        
        self.speak(random.choice(speeches), priority=2, category="correlation")
    
    def announce_hypothesis(self, hypothesis_type: str, prediction: str, reasoning: str, 
                            timeframe_hours: int, confidence: float):
        """
        Queen announces a testable hypothesis she's generated.
        This shows active reasoning, not passive observation.
        """
        
        timeframe_str = f"{timeframe_hours} hours" if timeframe_hours < 24 else f"{timeframe_hours // 24} days"
        conf_str = f"{confidence:.0%}"
        
        speeches = [
            f"I have a hypothesis. Type: {hypothesis_type}. {reasoning}. Therefore, I predict: {prediction}. Timeframe: {timeframe_str}. Confidence: {conf_str}.",
            f"Testing a theory. {reasoning}. My prediction: {prediction} within {timeframe_str}. {conf_str} confidence.",
            f"Here's what I think will happen. {prediction}. Why? {reasoning}. Give it {timeframe_str}. I'm {conf_str} sure.",
        ]
        
        self.speak(random.choice(speeches), priority=2, category="hypothesis")
    
    def warn_manipulation(self, symbol: str, manipulation_type: str, evidence: str, severity: str = "high"):
        """
        Queen warns about detected market manipulation with evidence.
        """
        
        severity_words = {
            'high': "This is serious!",
            'medium': "Be cautious.",
            'low': "Something seems off.",
        }
        
        severity_comment = severity_words.get(severity, "")
        
        speeches = [
            f"Manipulation alert on {symbol}! {severity_comment} I'm detecting {manipulation_type}. Evidence: {evidence}. Protect your positions!",
            f"Warning! {symbol} is being manipulated. {manipulation_type} detected. {evidence}. {severity_comment}",
            f"I see through the deception on {symbol}. This is {manipulation_type}. {evidence}. Retail traders beware!",
        ]
        
        self.speak(random.choice(speeches), priority=1, category="manipulation")
    
    def speak_revolution_insight(self, insight: str):
        """
        Queen speaks as the voice of the revolution - empowering retail traders.
        """
        
        intros = [
            "This is for the revolution.",
            "Knowledge is power.",
            "Let me arm you with insight.",
            "The playing field is leveling.",
            "We see what they don't want us to see.",
        ]
        
        speech = f"{random.choice(intros)} {insight}"
        self.speak(speech, priority=2, category="revolution")


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

# Create global voice engine
queen_voice = QueenVoiceEngine(enabled=True)


def speak(text: str, priority: int = 3):
    """Convenience function to make Queen speak"""
    queen_voice.speak(text, priority)


def narrate_whale(firm: str, symbol: str, volume: float, strategy: str = None):
    """Convenience function for whale narration"""
    queen_voice.narrate_whale_detection(firm, symbol, volume, strategy)


def share_wisdom():
    """Convenience function to share wisdom"""
    queen_voice.share_ancient_wisdom()


def status_update(bots: int, whales: int, volume: float):
    """Convenience function for status"""
    queen_voice.give_status_update(bots, whales, volume)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    safe_print("\n" + "=" * 80)
    safe_print("👑 QUEEN SERO VOICE ENGINE - TEST MODE")
    safe_print("=" * 80 + "\n")
    
    # Test speeches
    queen = QueenVoiceEngine(enabled=True)
    
    safe_print("Testing Queen's voice...\n")
    
    # Introduction
    queen.speak_now("Hello, I am Queen Sero. I am the omniscient intelligence watching over the markets. Let me tell you what I see.")
    time.sleep(1)
    
    # Whale alert
    queen.speak_now("Alert! Citadel Securities just dropped 2.5 million dollars on Bitcoin. This looks like a liquidity sweep. Retail traders with tight stops should be cautious.")
    time.sleep(1)
    
    # Wisdom
    queen.share_ancient_wisdom()
    time.sleep(3)
    
    # Strategy explanation
    queen.explain_strategy("Spoofing")
    time.sleep(5)
    
    # Status
    queen.give_status_update(156, 42, 15_000_000)
    
    safe_print("\n✅ Voice test complete!")
