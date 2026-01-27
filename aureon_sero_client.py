from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            """Check if stream is already a UTF-8 TextIOWrapper."""
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            """Check if stream buffer is valid and not closed."""
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

"""
Aureon Dr Auris Throne Chatbot Client - AI Intelligence Augmentation 🧠🤖

Integration with DigitalOcean AI Agents chatbot (Llama 3.3 Instruct 70B)
for Queen decision validation and market intelligence enhancement.

Architecture:
- HTTP client to Dr Auris Throne Chatbot API
- Async query interface for non-blocking integration
- Structured prompts for trading context
- Response parsing with confidence scoring
- Fail-safe: Trading continues if chatbot unavailable

Usage in Queen Gate:
```python
sero = SeroClient()
advice = await sero.ask_trading_decision(
    symbol="BTC/USD",
    side="BUY",
    context={"coherence": 0.85, "queen_confidence": 0.72}
)
if advice and advice.confidence > 0.7:
    # Blend Dr Auris Throne signal into Queen decision
    pass
```
"""

import os
import asyncio
import aiohttp
import logging
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class SeroAdvice:
    """Structured response from Dr Auris Throne Chatbot."""
    recommendation: str  # "PROCEED", "CAUTION", "ABORT"
    confidence: float  # 0.0-1.0
    reasoning: str
    risk_flags: list
    timestamp: float

class SeroClient:
    """
    Client for Dr Auris Throne Chatbot (Llama 3.3 Instruct 70B) intelligence augmentation.
    
    Provides async interface to query external AI agent for:
    - Trade decision validation
    - Market pattern recognition
    - Risk assessment
    - Anomaly detection
    """
    
    def __init__(self):
        self.endpoint = os.getenv('AUREON_AGENT_ENDPOINT', '')
        self.agent_id = os.getenv('AUREON_AGENT_ID', '')
        self.chatbot_id = os.getenv('AUREON_CHATBOT_ID', '')
        # DigitalOcean widget uses chatbot_id as API key; allow override via AUREON_AGENT_KEY
        self.api_key = os.getenv('AUREON_AGENT_KEY', '') or self.chatbot_id
        
        self.enabled = bool(self.endpoint and self.api_key and self.agent_id and self.chatbot_id)
        self.timeout = aiohttp.ClientTimeout(total=15.0)  # 15s max (outer gate has 3s timeout)
        
        if not self.enabled:
            logger.warning("Dr Auris Throne Chatbot not configured - AI augmentation disabled")
        else:
            logger.info(f"Dr Auris Throne Chatbot enabled: agent_id={self.agent_id[:8]}...")
    
    async def ask_trading_decision(
        self,
        symbol: str,
        side: str,
        context: Dict[str, Any],
        queen_confidence: float
    ) -> Optional[SeroAdvice]:
        """
        Ask Dr Auris Throne to validate a trading decision.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USD")
            side: "BUY" or "SELL"
            context: Dict with coherence, fusion_bias, threat_level, etc.
            queen_confidence: Queen neuron's current confidence (0-1)
        
        Returns:
            Dr Auris Throne advice if successful, None if unavailable/error
        """
        if not self.enabled:
            return None
        
        # Build concise prompt for trading context
        prompt = self._build_trading_prompt(symbol, side, context, queen_confidence)
        
        try:
            response = await self._query_api(prompt)
            return self._parse_trading_response(response)
        except Exception as e:
            logger.warning(f"Dr Auris Throne query failed (non-critical): {type(e).__name__} {repr(e)}")
            return None
    
    async def ask_market_intelligence(self, query: str) -> Optional[str]:
        """
        General-purpose market intelligence query.
        
        Args:
            query: Natural language question about markets/patterns
        
        Returns:
            Response text or None if unavailable
        """
        if not self.enabled:
            return None
        
        try:
            response = await self._query_api(query)
            return self._extract_message_from_response(response)
        except Exception as e:
            logger.warning(f"Dr Auris Throne intelligence query failed: {type(e).__name__} {repr(e)}")
            return None
    
    def _build_trading_prompt(
        self,
        symbol: str,
        side: str,
        context: Dict[str, Any],
        queen_confidence: float
    ) -> str:
        """Build structured prompt for trading decision validation."""
        coherence = context.get('coherence', 0.0)
        fusion_bias = context.get('fusion_bias', 0.0)
        threat_level = context.get('threat_level', 0.0)
        
        prompt = f"""Trading Decision Validation Request:

Symbol: {symbol}
Side: {side}
Queen Confidence: {queen_confidence:.2f}

Context Metrics:
- Harmonic Coherence: {coherence:.2f}
- Fusion Bias: {fusion_bias:.2f}
- Counter-Frequency Threat: {threat_level:.2f}

Based on these metrics, provide:
1. Recommendation: PROCEED / CAUTION / ABORT
2. Confidence: 0.0-1.0
3. Risk flags (if any)
4. Brief reasoning (1 sentence)

Format response as:
RECOMMENDATION: [choice]
CONFIDENCE: [0.0-1.0]
RISK_FLAGS: [comma-separated or "none"]
REASONING: [brief explanation]
"""
        return prompt
    
    async def _query_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Send query to Dr Auris Throne Chatbot API using DigitalOcean Agents flow.
        
        Args:
            prompt: Text prompt to send
        
        Returns:
            API response dict or None if failed
        """
        if not self.endpoint or not self.agent_id or not self.api_key:
            return None

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            token = await self._get_access_token(session)
            if not token:
                return None

            url = f"{self.endpoint}/api/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            payload = {
                'messages': [
                    {
                        'id': f"sero-{int(time.time()*1000)}",
                        'role': 'user',
                        'content': prompt,
                        'sentTime': datetime.now(timezone.utc).isoformat(),
                        'receivedTime': ''
                    }
                ],
                'stream': False,
                'include_functions_info': True,
                'include_retrieval_info': True,
                'include_guardrails_info': True
            }

            try:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Dr Auris Throne API error: {resp.status} at {url} | {text[:200]}")
                        return None
                    try:
                        return await resp.json()
                    except Exception:
                        text = await resp.text()
                        logger.error(f"Dr Auris Throne API non-JSON response: {text[:200]}")
                        return None
            except aiohttp.ClientError as e:
                logger.error(f"Dr Auris Throne API request failed: {e}")
                return None

    async def _get_access_token(self, session: aiohttp.ClientSession) -> Optional[str]:
        """Issue access token via DigitalOcean Agents auth endpoint."""
        url = f"https://cloud.digitalocean.com/gen-ai/auth/agents/{self.agent_id}/token"
        api_keys = []
        if self.chatbot_id:
            api_keys.append(self.chatbot_id)
        if self.api_key and self.api_key != self.chatbot_id:
            api_keys.append(self.api_key)

        for key in api_keys:
            headers = {
                'Content-Type': 'application/json',
                'X-Api-Key': key
            }
            try:
                async with session.post(url, json={}, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('access_token')
                    text = await resp.text()
                    logger.error(f"Token issuance failed: {resp.status} | {text[:200]}")
            except aiohttp.ClientError as e:
                logger.error(f"Token request failed: {e}")
                continue

        return None
    
    def _parse_trading_response(self, response: Optional[Dict[str, Any]]) -> Optional[SeroAdvice]:
        """
        Parse structured trading response from Dr Auris Throne.
        
        Args:
            response: Raw API response dict
        
        Returns:
            Dr Auris Throne advice object or None if parsing failed
        """
        if not response:
            return None
        
        try:
            message = self._extract_message_from_response(response)
            if not message:
                return None
            
            # Parse structured response
            lines = message.strip().split('\n')
            parsed = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    parsed[key.strip().upper()] = value.strip()
            
            recommendation = parsed.get('RECOMMENDATION', 'CAUTION').upper()
            if recommendation not in ['PROCEED', 'CAUTION', 'ABORT']:
                recommendation = 'CAUTION'
            
            confidence_str = parsed.get('CONFIDENCE', '0.5')
            try:
                confidence = float(confidence_str)
            except:
                confidence = 0.5
            
            reasoning = parsed.get('REASONING', 'No reasoning provided')
            
            risk_flags_str = parsed.get('RISK_FLAGS', 'none')
            risk_flags = [] if risk_flags_str.lower() == 'none' else [
                f.strip() for f in risk_flags_str.split(',')
            ]
            
            return SeroAdvice(
                recommendation=recommendation,
                confidence=confidence,
                reasoning=reasoning,
                risk_flags=risk_flags,
                timestamp=time.time()
            )
        
        except Exception as e:
            logger.error(f"Failed to parse Dr Auris Throne response: {e}")
            return None

    def _extract_message_from_response(self, response: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract assistant message from DO chat completion response."""
        if not response:
            return None
        # OpenAI-like format: { choices: [ { message: { content } } ] }
        choices = response.get('choices') if isinstance(response, dict) else None
        if isinstance(choices, list) and choices:
            choice = choices[0] or {}
            message = choice.get('message') or {}
            content = message.get('content')
            if content:
                return content
        # Fallbacks
        for key in ('message', 'response', 'content'):
            val = response.get(key) if isinstance(response, dict) else None
            if isinstance(val, str) and val.strip():
                return val
        return None


# Global singleton
_sero_client: Optional[SeroClient] = None

def get_sero_client() -> SeroClient:
    """Get or create global Dr Auris Throne client singleton."""
    global _sero_client
    if _sero_client is None:
        _sero_client = SeroClient()
    return _sero_client


# --- Testing / CLI ---
async def test_sero():
    """Test Dr Auris Throne Chatbot connectivity."""
    sero = get_sero_client()
    
    if not sero.enabled:
        print("❌ Dr Auris Throne Chatbot not configured")
        return
    
    print(f"✅ Dr Auris Throne Chatbot configured: {sero.agent_id[:8]}...")
    
    # Test trading decision query
    print("\n📊 Testing trading decision validation...")
    advice = await sero.ask_trading_decision(
        symbol="BTC/USD",
        side="BUY",
        context={
            'coherence': 0.85,
            'fusion_bias': 0.3,
            'threat_level': 0.1
        },
        queen_confidence=0.72
    )
    
    if advice:
        print(f"✅ Dr Auris Throne Advice:")
        print(f"   Recommendation: {advice.recommendation}")
        print(f"   Confidence: {advice.confidence:.2f}")
        print(f"   Reasoning: {advice.reasoning}")
        print(f"   Risk Flags: {advice.risk_flags}")
    else:
        print("❌ No advice received")
    
    # Test general intelligence query
    print("\n🧠 Testing market intelligence query...")
    intel = await sero.ask_market_intelligence(
        "What are key risk factors for crypto trading in current market conditions?"
    )
    
    if intel:
        print(f"✅ Intelligence: {intel[:200]}...")
    else:
        print("❌ No intelligence received")


if __name__ == '__main__':
    asyncio.run(test_sero())
