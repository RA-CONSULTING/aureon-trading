#!/usr/bin/env python3
"""
⛏️ AUREON MINER - INTEGRATED BACKGROUND MINER ⛏️
=================================================

Aureon IS the miner. One process. Background thread doing hashes.

COMPONENTS:
├─ StratumClient: Pool communication (subscribe, authorize, notify, submit)
├─ MiningSession: Manages connection and mining for a single pool
├─ AureonMiner: Orchestrates multiple MiningSessions (Multi-Pool)
├─ HarmonicMiningOptimizer: Ties harmonic/solar data into mining decisions
└─ MiningTelemetry: Stats and integration with Aureon ecosystem

Gary Leckey & GitHub Copilot | December 2025
"From trading to mining - one unified system"
"""

import hashlib
import struct
import socket
import json
import threading
import time
import logging
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, List, Tuple
from collections import deque

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

PHI = (1 + 5 ** 0.5) / 2  # Golden Ratio
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]

# Mining defaults
DEFAULT_NONCE_BATCH = 100_000  # Nonces per batch before checking for new job
HASH_REPORT_INTERVAL = 10.0    # Seconds between hashrate reports
MAX_NONCE = 0xFFFFFFFF         # Maximum 32-bit nonce value

# Known Mining Platforms
KNOWN_POOLS = {
    'braiins': {'host': 'stratum.braiins.com', 'port': 3333, 'desc': 'Braiins Pool (formerly Slushpool)'},
    'slushpool': {'host': 'stratum.slushpool.com', 'port': 3333, 'desc': 'Slushpool (Legacy)'},
    'antpool': {'host': 'stratum.antpool.com', 'port': 3333, 'desc': 'AntPool'},
    'f2pool': {'host': 'btc.f2pool.com', 'port': 3333, 'desc': 'F2Pool'},
    'viabtc': {'host': 'btc.viabtc.com', 'port': 3333, 'desc': 'ViaBTC'},
    'nicehash': {'host': 'sha256.auto.nicehash.com', 'port': 9200, 'desc': 'NiceHash Auto'},
    'kano': {'host': 'stratum.kano.is', 'port': 3333, 'desc': 'KanoPool'},
    'ckpool': {'host': 'solo.ckpool.org', 'port': 3333, 'desc': 'Solo CKPool (Solo Mining)'},
    'binance': {'host': 'sha256.poolbinance.com', 'port': 8888, 'desc': 'Binance Pool'},
    'luxor': {'host': 'btc.global.luxor.tech', 'port': 700, 'desc': 'Luxor Mining'},
}

def resolve_pool_config(platform: str = None, host: str = None, port: int = None) -> Tuple[str, int]:
    """
    Resolve pool connection details from platform name or explicit host/port.
    Returns (host, port).
    """
    if platform and platform.lower() in KNOWN_POOLS:
        config = KNOWN_POOLS[platform.lower()]
        return config['host'], config['port']
    
    # Default fallback
    return host or 'stratum.braiins.com', port or 3333


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MiningJob:
    """Represents a mining job from the pool"""
    job_id: str
    prev_hash: bytes
    coinbase1: bytes
    coinbase2: bytes
    merkle_branches: List[bytes]
    version: bytes
    nbits: bytes
    ntime: bytes
    clean_jobs: bool
    target: int
    extranonce1: bytes
    extranonce2_size: int
    difficulty: float = 1.0
    
    def build_header(self, extranonce2: bytes, nonce: int) -> bytes:
        """Build 80-byte block header with given extranonce2 and nonce"""
        # Build coinbase transaction
        coinbase = self.coinbase1 + self.extranonce1 + extranonce2 + self.coinbase2
        coinbase_hash = hashlib.sha256(hashlib.sha256(coinbase).digest()).digest()
        
        # Build merkle root
        merkle_root = coinbase_hash
        for branch in self.merkle_branches:
            merkle_root = hashlib.sha256(hashlib.sha256(merkle_root + branch).digest()).digest()
        
        # Build header (80 bytes)
        header = (
            self.version +
            self.prev_hash +
            merkle_root +
            self.ntime +
            self.nbits +
            struct.pack('<I', nonce)
        )
        return header
    
    def __repr__(self):
        return f"MiningJob(id={self.job_id}, diff={self.difficulty:.2f})"


@dataclass
class MiningStats:
    """Mining statistics"""
    hashes: int = 0
    shares_submitted: int = 0
    shares_accepted: int = 0
    shares_rejected: int = 0
    start_time: float = field(default_factory=time.time)
    last_share_time: float = 0.0
    best_difficulty: float = 0.0
    
    @property
    def hashrate(self) -> float:
        elapsed = time.time() - self.start_time
        return self.hashes / elapsed if elapsed > 0 else 0
    
    @property
    def accept_rate(self) -> float:
        if self.shares_submitted == 0:
            return 0.0
        return self.shares_accepted / self.shares_submitted
    
    @property
    def uptime(self) -> float:
        return time.time() - self.start_time
    
    def format_hashrate(self) -> Tuple[float, str]:
        """Return hashrate with appropriate unit"""
        hr = self.hashrate
        if hr > 1e12:
            return hr / 1e12, 'TH/s'
        elif hr > 1e9:
            return hr / 1e9, 'GH/s'
        elif hr > 1e6:
            return hr / 1e6, 'MH/s'
        elif hr > 1e3:
            return hr / 1e3, 'KH/s'
        return hr, 'H/s'


@dataclass
class HarmonicMiningState:
    """Harmonic state influencing mining behavior"""
    coherence: float = 0.5
    solar_forcing: float = 1.0
    planetary_alignment: float = 0.5
    optimal_nonce_bias: int = 0  # Offset for nonce starting point
    intensity_multiplier: float = 1.0  # How aggressive to mine
    schumann_resonance: float = 7.83  # Earth's frequency
    phi_phase: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════
# STRATUM CLIENT
# ═══════════════════════════════════════════════════════════════════════════

class StratumClient:
    """
    Stratum protocol client for pool communication.
    Handles: subscribe, authorize, notify (jobs), submit (shares)
    """
    
    def __init__(self, host: str, port: int, worker: str, password: str = 'x'):
        self.host = host
        self.port = port
        self.worker = worker
        self.password = password
        
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.authorized = False
        
        self.extranonce1: bytes = b''
        self.extranonce2_size: int = 4
        self.current_job: Optional[MiningJob] = None
        self.job_lock = threading.Lock()
        self.difficulty: float = 1.0
        
        self.message_id = 0
        self.pending_responses: Dict[int, Callable] = {}
        self.response_lock = threading.Lock()
        
        self._recv_thread: Optional[threading.Thread] = None
        self._running = False
        self._recv_buffer = ''
        
        # Callbacks
        self.on_job: Optional[Callable[[MiningJob], None]] = None
        self.on_share_result: Optional[Callable[[bool, str], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None
    
    def connect(self) -> bool:
        """Connect to pool and perform handshake"""
        try:
            logger.info(f"⛏️ Connecting to pool: {self.host}:{self.port}")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"✅ TCP connection established to {self.host}")
            
            # Start receive thread
            self._running = True
            self._recv_thread = threading.Thread(target=self._receive_loop, daemon=True, name=f'stratum-{self.host}')
            self._recv_thread.start()
            
            # Subscribe
            logger.info(f"📝 Sending mining.subscribe to {self.host}...")
            if not self._subscribe():
                logger.error(f"❌ Subscribe failed on {self.host}")
                return False
            
            # Authorize
            logger.info(f"🔐 Authorizing worker: {self.worker} on {self.host}")
            if not self._authorize():
                logger.error(f"❌ Authorization failed on {self.host}")
                return False
            
            self.authorized = True
            logger.info(f"✅ Authorized successfully on {self.host}!")
            return True
            
        except socket.timeout:
            logger.error(f"❌ Connection timeout to {self.host}:{self.port}")
            return False
        except ConnectionRefusedError:
            logger.error(f"❌ Connection refused by {self.host}:{self.port}")
            return False
        except Exception as e:
            logger.error(f"❌ Pool connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from pool"""
        self._running = False
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except:
                pass
        self.connected = False
        self.authorized = False
        logger.info(f"🔌 Disconnected from pool {self.host}")
    
    def _send(self, method: str, params: list) -> int:
        """Send JSON-RPC message to pool"""
        self.message_id += 1
        msg = {
            'id': self.message_id,
            'method': method,
            'params': params
        }
        data = json.dumps(msg) + '\n'
        try:
            self.socket.sendall(data.encode())
            logger.debug(f"📤 Sent: {method} (id={self.message_id})")
        except Exception as e:
            logger.error(f"Send error: {e}")
        return self.message_id
    
    def _receive_loop(self):
        """Background thread receiving pool messages"""
        logger.debug("Receive thread started")
        
        while self._running:
            try:
                self.socket.settimeout(1.0)
                data = self.socket.recv(4096)
                
                if not data:
                    logger.warning(f"Pool {self.host} closed connection")
                    break
                
                self._recv_buffer += data.decode('utf-8', errors='ignore')
                
                while '\n' in self._recv_buffer:
                    line, self._recv_buffer = self._recv_buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            self._handle_message(msg)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON from pool: {e}")
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Receive error: {e}")
                break
        
        self.connected = False
        if self.on_disconnect and self._running:
            self.on_disconnect()
    
    def _handle_message(self, msg: dict):
        """Handle incoming pool message"""
        # Check if it's a notification (no id) or a response (has id)
        if 'method' in msg:
            # Server notification
            method = msg['method']
            params = msg.get('params', [])
            
            logger.debug(f"📥 Notification: {method}")
            
            if method == 'mining.notify':
                self._handle_notify(params)
            elif method == 'mining.set_difficulty':
                self._handle_set_difficulty(params)
            elif method == 'mining.set_extranonce':
                self._handle_set_extranonce(params)
                
        elif 'id' in msg:
            # Response to our request
            msg_id = msg['id']
            with self.response_lock:
                if msg_id in self.pending_responses:
                    callback = self.pending_responses.pop(msg_id)
                    callback(msg)
    
    def _handle_notify(self, params: list):
        """Handle new job notification (mining.notify)"""
        try:
            # Stratum v1 mining.notify params:
            # [job_id, prevhash, coinb1, coinb2, merkle_branch[], version, nbits, ntime, clean_jobs]
            if len(params) < 9:
                logger.warning(f"Invalid notify params: {len(params)} items")
                return
            
            job = MiningJob(
                job_id=params[0],
                prev_hash=bytes.fromhex(params[1]),
                coinbase1=bytes.fromhex(params[2]),
                coinbase2=bytes.fromhex(params[3]),
                merkle_branches=[bytes.fromhex(b) for b in params[4]],
                version=bytes.fromhex(params[5]),
                nbits=bytes.fromhex(params[6]),
                ntime=bytes.fromhex(params[7]),
                clean_jobs=params[8],
                target=self._calculate_target_from_difficulty(self.difficulty),
                extranonce1=self.extranonce1,
                extranonce2_size=self.extranonce2_size,
                difficulty=self.difficulty
            )
            
            with self.job_lock:
                self.current_job = job
            
            clean_str = "🧹 CLEAN" if job.clean_jobs else ""
            logger.info(f"📋 New job on {self.host}: {job.job_id} (diff={self.difficulty:.4f}) {clean_str}")
            
            if self.on_job:
                self.on_job(job)
                
        except Exception as e:
            logger.error(f"Failed to parse job: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_set_difficulty(self, params: list):
        """Handle difficulty change (mining.set_difficulty)"""
        if params:
            self.difficulty = float(params[0])
            logger.info(f"⚙️ Pool {self.host} difficulty set to: {self.difficulty}")
    
    def _handle_set_extranonce(self, params: list):
        """Handle extranonce change (mining.set_extranonce)"""
        if len(params) >= 2:
            self.extranonce1 = bytes.fromhex(params[0])
            self.extranonce2_size = int(params[1])
            logger.info(f"🔧 Extranonce updated on {self.host}: {params[0]}")
    
    def _calculate_target_from_difficulty(self, difficulty: float) -> int:
        """Calculate target from pool difficulty"""
        # Bitcoin mainnet target at difficulty 1
        MAX_TARGET = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        if difficulty <= 0:
            difficulty = 1
        return int(MAX_TARGET / difficulty)
    
    def _subscribe(self) -> bool:
        """Send mining.subscribe and wait for response"""
        result_event = threading.Event()
        response_data = {'result': None, 'error': None}
        
        def on_response(msg):
            response_data['result'] = msg.get('result')
            response_data['error'] = msg.get('error')
            result_event.set()
        
        msg_id = self._send('mining.subscribe', ['aureon-miner/1.0'])
        with self.response_lock:
            self.pending_responses[msg_id] = on_response
        
        if not result_event.wait(timeout=15):
            logger.error("Subscribe timeout")
            return False
        
        if response_data['error']:
            logger.error(f"Subscribe error: {response_data['error']}")
            return False
        
        res = response_data['result']
        if res and len(res) >= 3:
            # res = [[[subscription_details]], extranonce1, extranonce2_size]
            self.extranonce1 = bytes.fromhex(res[1])
            self.extranonce2_size = int(res[2])
            logger.info(f"📝 Subscribed to {self.host}: extranonce1={res[1]}, extranonce2_size={res[2]}")
            return True
        
        logger.error(f"Invalid subscribe response: {res}")
        return False
    
    def _authorize(self) -> bool:
        """Send mining.authorize and wait for response"""
        result_event = threading.Event()
        response_data = {'result': None, 'error': None}
        
        def on_response(msg):
            response_data['result'] = msg.get('result')
            response_data['error'] = msg.get('error')
            result_event.set()
        
        msg_id = self._send('mining.authorize', [self.worker, self.password])
        with self.response_lock:
            self.pending_responses[msg_id] = on_response
        
        if not result_event.wait(timeout=15):
            logger.error("Authorize timeout")
            return False
        
        if response_data['error']:
            logger.error(f"Authorize error: {response_data['error']}")
            return False
        
        return response_data['result'] == True
    
    def submit_share(self, job: MiningJob, extranonce2: bytes, ntime: bytes, nonce: int):
        """Submit a share to the pool"""
        params = [
            self.worker,
            job.job_id,
            extranonce2.hex(),
            ntime.hex(),
            struct.pack('>I', nonce).hex()  # Big-endian for submission
        ]
        
        def on_response(msg):
            accepted = msg.get('result', False)
            error = msg.get('error')
            error_str = ''
            if error:
                if isinstance(error, list) and len(error) >= 2:
                    error_str = str(error[1])
                else:
                    error_str = str(error)
            
            if self.on_share_result:
                self.on_share_result(accepted, error_str)
        
        msg_id = self._send('mining.submit', params)
        with self.response_lock:
            self.pending_responses[msg_id] = on_response
        
        logger.debug(f"📤 Submitted share: job={job.job_id}, nonce={nonce:08x}")
    
    def get_current_job(self) -> Optional[MiningJob]:
        """Get current job (thread-safe)"""
        with self.job_lock:
            return self.current_job


# ═══════════════════════════════════════════════════════════════════════════
# HARMONIC MINING OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════

class HarmonicMiningOptimizer:
    """
    Integrates Aureon's harmonic/probability systems into mining decisions.
    
    Hooks into:
    - Nonce range selection (probability matrix)
    - Mining intensity (solar/planetary forcing)
    - Timing windows (harmonic coherence)
    """
    
    def __init__(self):
        self.state = HarmonicMiningState()
        self.history: deque = deque(maxlen=1000)
        self.share_nonces: List[int] = []  # Track successful nonces for pattern analysis
        
        # Try to import Aureon systems
        self._probability_matrix = None
        self._earth_engine = None
        self._imperial_engine = None
        self._load_aureon_hooks()
    
    def _load_aureon_hooks(self):
        """Load Aureon probability/harmonic systems if available"""
        try:
            from aureon_probability_nexus import AureonProbabilityNexus
            self._probability_matrix = AureonProbabilityNexus()
            logger.info("🔮 Probability Matrix: CONNECTED to miner")
        except ImportError:
            logger.debug("Probability Matrix not available for mining")
        
        try:
            from hnc_earth_resonance import EarthResonanceEngine
            self._earth_engine = EarthResonanceEngine()
            logger.info("🌍 Earth Resonance Engine: CONNECTED to miner")
        except ImportError:
            logger.debug("Earth Resonance Engine not available for mining")
        
        try:
            from hnc_imperial_predictability import ImperialPredictabilityEngine
            self._imperial_engine = ImperialPredictabilityEngine()
            logger.info("🌌 Imperial Engine: CONNECTED to miner")
        except ImportError:
            logger.debug("Imperial Engine not available for mining")
    
    def update_state(self, solar_data: Optional[dict] = None, 
                     planetary_data: Optional[dict] = None):
        """Update harmonic state from external data"""
        # Update from Earth engine if available
        if self._earth_engine:
            try:
                earth_state = self._earth_engine.get_state()
                self.state.schumann_resonance = earth_state.get('schumann_mode1', 7.83)
                self.state.coherence = earth_state.get('field_coherence', 0.5)
                self.state.phi_phase = earth_state.get('phi_multiplier', 1.0) - 1.0
            except:
                pass
        
        # Update from Imperial engine if available
        if self._imperial_engine:
            try:
                imperial_state = self._imperial_engine.get_state()
                self.state.planetary_alignment = imperial_state.get('coherence', 0.5)
            except:
                pass
        
        # Override with explicit data if provided
        if solar_data:
            tsi = solar_data.get('tsi', 1361.0)
            f107 = solar_data.get('f107', 100.0)
            # Normalize solar forcing (baseline ~1361 W/m², F10.7 ~100 sfu)
            self.state.solar_forcing = (tsi / 1361.0) * (f107 / 100.0)
        
        if planetary_data:
            self.state.planetary_alignment = planetary_data.get('coherence', self.state.planetary_alignment)
        
        # Compute intensity multiplier based on harmonic state
        # Higher coherence = more aggressive mining
        self.state.intensity_multiplier = (
            0.5 +  # Base 50%
            0.3 * self.state.coherence +  # Up to 30% from coherence
            0.2 * self.state.planetary_alignment  # Up to 20% from planetary
        ) * self.state.solar_forcing
        
        # Clamp to reasonable range
        self.state.intensity_multiplier = max(0.1, min(2.0, self.state.intensity_multiplier))
        
        self.history.append({
            'time': time.time(),
            'state': {
                'coherence': self.state.coherence,
                'solar': self.state.solar_forcing,
                'planetary': self.state.planetary_alignment,
                'intensity': self.state.intensity_multiplier
            }
        })
    
    def get_nonce_bias(self) -> int:
        """
        Get nonce starting offset based on probability matrix.
        Uses Fibonacci/Prime patterns from Aureon's coherence logic.
        """
        # Use probability prediction if available
        if self._probability_matrix:
            try:
                pred = self._probability_matrix.get_next_prediction()
                if pred and pred.get('probability', 0) > 0.6:
                    # High confidence - use prime-aligned offset
                    prob = pred['probability']
                    prime_idx = int(prob * len(PRIMES))
                    bias = PRIMES[prime_idx % len(PRIMES)] * 1_000_000
                    logger.debug(f"🔮 Probability-guided nonce bias: {bias}")
                    return bias
            except:
                pass
        
        # Analyze previous successful nonces for patterns
        if len(self.share_nonces) >= 3:
            # Look for Fibonacci-like patterns in successful nonces
            avg_nonce = sum(self.share_nonces[-10:]) / min(10, len(self.share_nonces))
            fib_bias = int(avg_nonce * PHI) % MAX_NONCE
            if fib_bias > 0:
                return fib_bias
        
        # Default: Fibonacci-based bias using coherence
        fib_idx = int(self.state.coherence * len(FIBONACCI))
        bias = FIBONACCI[fib_idx % len(FIBONACCI)] * 100_000
        return bias % MAX_NONCE
    
    def should_mine(self) -> bool:
        """
        Determine if conditions are favorable for mining.
        Always True for now, but could gate on extreme conditions.
        """
        return True
    
    def get_batch_size(self) -> int:
        """Get nonce batch size based on current intensity"""
        base_batch = DEFAULT_NONCE_BATCH
        adjusted = int(base_batch * self.state.intensity_multiplier)
        return max(10_000, min(adjusted, 1_000_000))  # Clamp to reasonable range
    
    def on_share_found(self, hash_value: bytes, nonce: int, difficulty: float):
        """Called when a valid share is found - for learning"""
        # Record successful nonce for pattern analysis
        self.share_nonces.append(nonce)
        if len(self.share_nonces) > 100:
            self.share_nonces = self.share_nonces[-100:]
        
        # Record event
        self.history.append({
            'time': time.time(),
            'event': 'share_found',
            'nonce': nonce,
            'difficulty': difficulty,
            'hash_prefix': hash_value[:8].hex(),
            'coherence': self.state.coherence
        })
        
        # Positive feedback on coherence
        self.state.coherence = min(1.0, self.state.coherence * 1.005)
        
        logger.debug(f"🎯 Share pattern recorded: nonce={nonce:08x}, coherence now {self.state.coherence:.3f}")
    
    def get_mining_insight(self) -> dict:
        """Get current mining optimization state"""
        return {
            'coherence': self.state.coherence,
            'intensity': self.state.intensity_multiplier,
            'batch_size': self.get_batch_size(),
            'nonce_bias': self.get_nonce_bias(),
            'successful_shares': len(self.share_nonces),
            'schumann': self.state.schumann_resonance,
            'phi_phase': self.state.phi_phase
        }


# ═══════════════════════════════════════════════════════════════════════════
# MINING SESSION (SINGLE POOL)
# ═══════════════════════════════════════════════════════════════════════════

class MiningSession:
    """
    Manages mining operations for a single pool connection.
    """
    
    def __init__(self, host: str, port: int, worker: str, password: str, 
                 optimizer: HarmonicMiningOptimizer, session_id: str):
        self.host = host
        self.port = port
        self.worker = worker
        self.password = password
        self.optimizer = optimizer
        self.session_id = session_id
        
        self.stratum = StratumClient(host, port, worker, password)
        self.stats = MiningStats()
        
        self._running = False
        self._paused = False
        self._threads: List[threading.Thread] = []
        
        self._extranonce2_counter = 0
        self._extranonce2_lock = threading.Lock()
        
        # Wire callbacks
        self.stratum.on_share_result = self._on_share_result
        self.stratum.on_disconnect = self._on_disconnect
    
    def start(self, num_threads: int) -> bool:
        """Start mining on this session"""
        if not self.stratum.connect():
            logger.error(f"[{self.session_id}] Failed to connect")
            return False
        
        self._running = True
        self._threads = []
        
        for i in range(num_threads):
            t = threading.Thread(
                target=self._mine_loop,
                args=(i,),
                daemon=True,
                name=f'miner-{self.session_id}-{i}'
            )
            t.start()
            self._threads.append(t)
            
        logger.info(f"[{self.session_id}] Started with {num_threads} threads")
        return True
    
    def stop(self):
        """Stop mining on this session"""
        self._running = False
        self.stratum.disconnect()
        for t in self._threads:
            t.join(timeout=2)
        self._threads.clear()
    
    def pause(self):
        self._paused = True
    
    def resume(self):
        self._paused = False
        
    def _get_next_extranonce2(self, job: MiningJob) -> bytes:
        with self._extranonce2_lock:
            self._extranonce2_counter += 1
            counter = self._extranonce2_counter
        en2 = struct.pack('<Q', counter)[:job.extranonce2_size]
        return en2
    
    def _mine_loop(self, thread_id: int):
        local_hashes = 0
        last_job_id = None
        
        while self._running:
            if self._paused:
                time.sleep(0.5)
                continue
            
            if not self.optimizer.should_mine():
                time.sleep(1)
                continue
            
            job = self.stratum.get_current_job()
            if not job:
                time.sleep(0.5)
                continue
            
            if job.job_id != last_job_id:
                last_job_id = job.job_id
                # logger.debug(f"[{self.session_id}] Thread {thread_id} new job {job.job_id}")
            
            batch_size = self.optimizer.get_batch_size()
            nonce_bias = self.optimizer.get_nonce_bias()
            
            extranonce2 = self._get_next_extranonce2(job)
            
            # Distribute nonces based on thread_id AND session_id hash to avoid overlap if multiple sessions use same logic
            # But here we rely on extranonce2 being unique per session instance if we managed it globally, 
            # but extranonce1 is unique per connection usually.
            
            nonce_start = (nonce_bias + thread_id * batch_size) % MAX_NONCE
            nonce_end = min(nonce_start + batch_size, MAX_NONCE)
            
            for nonce in range(nonce_start, nonce_end):
                if not self._running or self._paused:
                    break
                
                if nonce % 10000 == 0:
                    new_job = self.stratum.get_current_job()
                    if new_job and new_job.job_id != job.job_id:
                        break
                
                header = job.build_header(extranonce2, nonce)
                hash_result = hashlib.sha256(hashlib.sha256(header).digest()).digest()
                hash_int = int.from_bytes(hash_result[::-1], 'big')
                
                local_hashes += 1
                if local_hashes >= 1000:
                    self.stats.hashes += local_hashes
                    local_hashes = 0
                
                if hash_int < job.target:
                    achieved_diff = self._calculate_difficulty_from_hash(hash_int)
                    logger.info(f"💎 SHARE [{self.session_id}] Thread {thread_id} | Diff: {achieved_diff:.6f}")
                    
                    self.stratum.submit_share(job, extranonce2, job.ntime, nonce)
                    self.stats.shares_submitted += 1
                    self.stats.last_share_time = time.time()
                    
                    if achieved_diff > self.stats.best_difficulty:
                        self.stats.best_difficulty = achieved_diff
                    
                    self.optimizer.on_share_found(hash_result, nonce, achieved_diff)
        
        self.stats.hashes += local_hashes

    def _calculate_difficulty_from_hash(self, hash_int: int) -> float:
        MAX_TARGET = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        if hash_int == 0: return float('inf')
        return MAX_TARGET / hash_int

    def _on_share_result(self, accepted: bool, error: str):
        if accepted:
            self.stats.shares_accepted += 1
        else:
            self.stats.shares_rejected += 1
            logger.warning(f"[{self.session_id}] Share REJECTED: {error}")

    def _on_disconnect(self):
        if self._running:
            logger.warning(f"[{self.session_id}] Disconnected, reconnecting...")
            time.sleep(5)
            if self._running:
                self.stratum.connect()


# ═══════════════════════════════════════════════════════════════════════════
# AUREON MINER (MULTI-POOL ORCHESTRATOR)
# ═══════════════════════════════════════════════════════════════════════════

class AureonMiner:
    """
    Orchestrates mining across one or more pools.
    """
    
    def __init__(self, pool_host: str = None, pool_port: int = None, 
                 worker: str = None, password: str = 'x',
                 threads: int = 1):
        
        self.optimizer = HarmonicMiningOptimizer()
        self.sessions: List[MiningSession] = []
        self.global_threads = threads
        
        self._running = False
        self._stats_thread: Optional[threading.Thread] = None
        
        # Backward compatibility: if host/port provided in init, add as first pool
        if pool_host and pool_port and worker:
            self.add_pool(pool_host, pool_port, worker, password, "default")
    
    def add_pool(self, host: str, port: int, worker: str, password: str = 'x', name: str = "pool"):
        """Add a mining pool configuration"""
        session = MiningSession(host, port, worker, password, self.optimizer, name)
        self.sessions.append(session)
        logger.info(f"➕ Added mining pool: {name} ({host}:{port})")
    
    def start(self) -> bool:
        """Start all mining sessions"""
        if not self.sessions:
            logger.error("No mining pools configured")
            return False
            
        print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    ⛏️  AUREON MULTI-MINER STARTING  ⛏️                        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
        """)
        
        # Distribute threads
        threads_per_pool = max(1, self.global_threads // len(self.sessions))
        remainder = self.global_threads % len(self.sessions)
        
        self._running = True
        success_count = 0
        
        for i, session in enumerate(self.sessions):
            t_count = threads_per_pool + (1 if i < remainder else 0)
            if session.start(t_count):
                success_count += 1
        
        if success_count == 0:
            logger.error("❌ Failed to start any mining sessions")
            return False
            
        # Start stats thread
        self._stats_thread = threading.Thread(target=self._stats_loop, daemon=True, name='miner-stats')
        self._stats_thread.start()
        
        logger.info(f"✅ Mining started on {success_count}/{len(self.sessions)} pools with {self.global_threads} total threads")
        return True
    
    def stop(self):
        """Stop all sessions"""
        logger.info("🛑 Stopping all miners...")
        self._running = False
        for session in self.sessions:
            session.stop()
        if self._stats_thread:
            self._stats_thread.join(timeout=2)
            
        self._print_final_stats()

    def pause(self):
        for session in self.sessions:
            session.pause()
        logger.info("⏸️ All miners paused")

    def resume(self):
        for session in self.sessions:
            session.resume()
        logger.info("▶️ All miners resumed")
        
    def update_harmonic_state(self, solar_data: dict = None, planetary_data: dict = None):
        self.optimizer.update_state(solar_data, planetary_data)

    def _stats_loop(self):
        while self._running:
            time.sleep(HASH_REPORT_INTERVAL)
            if self._running:
                total_hr = sum(s.stats.hashrate for s in self.sessions)
                total_shares = sum(s.stats.shares_accepted for s in self.sessions)
                
                # Format total hashrate
                unit = 'H/s'
                if total_hr > 1e12: total_hr /= 1e12; unit = 'TH/s'
                elif total_hr > 1e9: total_hr /= 1e9; unit = 'GH/s'
                elif total_hr > 1e6: total_hr /= 1e6; unit = 'MH/s'
                elif total_hr > 1e3: total_hr /= 1e3; unit = 'KH/s'
                
                insight = self.optimizer.get_mining_insight()
                logger.info(
                    f"📊 TOTAL: {total_hr:.2f} {unit} | "
                    f"Pools: {len(self.sessions)} | "
                    f"Shares: {total_shares} | "
                    f"Coherence: {insight['coherence']:.3f}"
                )

    def _print_final_stats(self):
        print("\n╔════════════════════ FINAL MINING STATS ════════════════════╗")
        for session in self.sessions:
            hr, unit = session.stats.format_hashrate()
            print(f"║ {session.session_id:<15} | {hr:>8.2f} {unit:<4} | Shares: {session.stats.shares_accepted:>5} ║")
        print("╚════════════════════════════════════════════════════════════╝\n")


# ═══════════════════════════════════════════════════════════════════════════
# STANDALONE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Run miner standalone (for testing)"""
    import signal
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Configuration
    PLATFORM = os.getenv('MINING_PLATFORM')
    ENABLE_ALL = os.getenv('MINING_ENABLE_ALL', '0') == '1'
    WORKER = os.getenv('MINING_WORKER', 'your_btc_address.aureon')
    PASSWORD = os.getenv('MINING_PASSWORD', 'x')
    THREADS = int(os.getenv('MINING_THREADS', '1'))
    
    miner = AureonMiner(threads=THREADS)
    
    if ENABLE_ALL:
        print("🚀 ACTIVATING ALL AVAILABLE MINING PLATFORMS")
        for name, config in KNOWN_POOLS.items():
            miner.add_pool(config['host'], config['port'], WORKER, PASSWORD, name)
    else:
        # Single pool mode
        RAW_HOST = os.getenv('MINING_POOL_HOST')
        RAW_PORT = os.getenv('MINING_POOL_PORT')
        
        POOL_HOST, POOL_PORT = resolve_pool_config(
            platform=PLATFORM,
            host=RAW_HOST,
            port=int(RAW_PORT) if RAW_PORT else None
        )
        miner.add_pool(POOL_HOST, POOL_PORT, WORKER, PASSWORD, PLATFORM or "custom")
    
    # Handle shutdown
    def shutdown(sig, frame):
        print("\n⚠️ Shutdown signal received...")
        miner.stop()
        exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    if miner.start():
        logger.info("⛏️ Miner running... Press Ctrl+C to stop")
        while True:
            try:
                time.sleep(60)
                miner.update_harmonic_state()
            except KeyboardInterrupt:
                break
        miner.stop()
    else:
        exit(1)


if __name__ == "__main__":
    main()
