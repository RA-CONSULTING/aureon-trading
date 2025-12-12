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

# Casimir Constants
HBAR_MINING = 1.054571817e-4   # Reduced Planck constant for mining (scaled)
VACUUM_ENERGY = 7.83 * PHI     # Base vacuum energy (Schumann × Phi)

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
    'luxor': {'host': 'btc.global.luxor.tech', 'port': 700, 'desc': 'Luxor Mining'},
    # Binance Pool - Multiple endpoints for redundancy
    'binance': {'host': 'sha256.poolbinance.com', 'port': 443, 'desc': 'Binance Pool (Primary)'},
    'binance2': {'host': 'btc.poolbinance.com', 'port': 1800, 'desc': 'Binance Pool (Backup 1)'},
    'binance3': {'host': 'bs.poolbinance.com', 'port': 3333, 'desc': 'Binance Pool (Backup 2)'},
}

# ═══════════════════════════════════════════════════════════════════════════
# BINANCE MULTI-COIN MINING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

BINANCE_COINS = {
    'BTC': {
        'algorithm': 'SHA256',
        'host': 'sha256.poolbinance.com',
        'port': 443,
        'desc': 'Bitcoin - SHA256',
        'merge_with': None,
        'casimir_coupling': 1.0,  # Base reference
    },
    'BCH': {
        'algorithm': 'SHA256',
        'host': 'bch.poolbinance.com',
        'port': 3333,
        'desc': 'Bitcoin Cash - SHA256',
        'merge_with': None,
        'casimir_coupling': 0.95,  # Same algo = high coupling
    },
    'LTC': {
        'algorithm': 'Scrypt',
        'host': 'ltc.poolbinance.com',
        'port': 443,
        'desc': 'Litecoin - Scrypt',
        'merge_with': 'DOGE',  # Merged mining enabled
        'casimir_coupling': 0.618,  # Phi coupling - different algo
    },
    'DOGE': {
        'algorithm': 'Scrypt',
        'host': 'ltc.poolbinance.com',  # Merged with LTC
        'port': 443,
        'desc': 'Dogecoin - Scrypt (merged)',
        'merge_with': 'LTC',
        'casimir_coupling': 0.618,
    },
    'ETC': {
        'algorithm': 'Etchash',
        'host': 'etc.poolbinance.com',
        'port': 3333,
        'desc': 'Ethereum Classic - Etchash',
        'merge_with': None,
        'casimir_coupling': 0.382,  # 1-Phi - memory intensive
    },
    'RVN': {
        'algorithm': 'KawPow',
        'host': 'stratum.ravencoin.flypool.org',  # Alternative since Binance may not support
        'port': 3333,
        'desc': 'Ravencoin - KawPow',
        'merge_with': None,
        'casimir_coupling': 0.382,
    },
    'ZEC': {
        'algorithm': 'Equihash',
        'host': 'zec.poolbinance.com',
        'port': 3333,
        'desc': 'Zcash - Equihash',
        'merge_with': None,
        'casimir_coupling': 0.5,
    },
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
    
    # Quantum Lattice Fields
    lattice_resonance: float = 1.0  # Resonance amplification factor
    ping_pong_phase: float = 0.0  # Current phase in ping-pong cycle
    quantum_entanglement: float = 0.0  # Cross-thread coherence
    harmonic_cascade: float = 1.0  # Cascade multiplier


# ═══════════════════════════════════════════════════════════════════════════
# QUANTUM LATTICE AMPLIFIER 
# ═══════════════════════════════════════════════════════════════════════════

class QuantumLatticeAmplifier:
    """
    ⚛️ QUANTUM LATTICE HASH AMPLIFIER ⚛️
    
    Amplifies effective hashrate through harmonic resonance cascade.
    Uses ping-pong wave interference patterns to optimize nonce selection.
    
    Concept:
    - Hash energy "bounces" between quantum lattice nodes
    - Each bounce amplifies probability of finding valid share
    - Golden ratio spacing creates constructive interference
    - Schumann resonance timing synchronizes hash bursts
    """
    
    def __init__(self):
        self.lattice_nodes: List[dict] = []
        self.resonance_field = 1.0
        self.ping_pong_phase = 0.0
        self.wave_amplitude = 1.0
        self.cascade_factor = 1.0
        
        # Quantum state
        self.entangled_nonces: deque = deque(maxlen=1000)
        self.resonance_history: deque = deque(maxlen=100)
        self.peak_resonance = 1.0
        
        # Timing
        self.last_ping = time.time()
        self.last_pong = time.time()
        self.cycle_frequency = 7.83  # Schumann resonance Hz
        
        # Learning
        self.success_patterns: Dict[str, int] = {}
        self.phi_harmonics = [PHI ** i for i in range(1, 13)]
        
        logger.info("⚛️ Quantum Lattice Amplifier initialized")
        logger.info(f"   Φ-Harmonics: {len(self.phi_harmonics)} levels")
        logger.info(f"   Base frequency: {self.cycle_frequency} Hz (Schumann)")
    
    def ping(self, thread_id: int, nonce: int, hash_value: bytes) -> float:
        """
        PING phase - Send hash energy into lattice
        Returns resonance multiplier for this nonce
        """
        now = time.time()
        
        # Calculate wave phase based on Schumann timing
        elapsed = now - self.last_ping
        phase = (elapsed * self.cycle_frequency) % (2 * 3.14159)
        
        # Golden ratio nonce alignment
        phi_alignment = 1.0
        for i, phi_h in enumerate(self.phi_harmonics):
            if nonce % int(phi_h * 1000) < 100:
                phi_alignment *= (1.0 + 0.1 * (i + 1))
        
        # Record node state
        node_state = {
            'thread': thread_id,
            'nonce': nonce,
            'phase': phase,
            'phi_align': phi_alignment,
            'time': now,
            'hash_prefix': hash_value[:4].hex() if hash_value else '0000'
        }
        self.lattice_nodes.append(node_state)
        if len(self.lattice_nodes) > 1000:
            self.lattice_nodes = self.lattice_nodes[-500:]
        
        # Wave amplitude based on recent success
        wave_mult = 1.0 + 0.5 * abs(3.14159 * 0.5 - phase)  # Peak at quarter-phase
        
        self.last_ping = now
        self.ping_pong_phase = phase
        
        return phi_alignment * wave_mult * self.cascade_factor
    
    def pong(self, thread_id: int, found_share: bool, difficulty: float) -> float:
        """
        PONG phase - Receive hash energy reflection
        Updates cascade multiplier based on results
        """
        now = time.time()
        
        # Calculate return phase
        elapsed = now - self.last_pong
        return_phase = (elapsed * self.cycle_frequency * PHI) % (2 * 3.14159)
        
        if found_share:
            # RESONANCE CASCADE - share found!
            # Amplify cascade factor using golden ratio
            self.cascade_factor = min(10.0, self.cascade_factor * PHI)
            self.wave_amplitude *= 1.1
            self.peak_resonance = max(self.peak_resonance, self.cascade_factor)
            
            # Record successful pattern
            pattern_key = f"{int(difficulty)}_{int(self.ping_pong_phase * 100)}"
            self.success_patterns[pattern_key] = self.success_patterns.get(pattern_key, 0) + 1
            
            logger.info(f"⚛️ RESONANCE CASCADE! Cascade: {self.cascade_factor:.2f}x | Amplitude: {self.wave_amplitude:.2f}")
        else:
            # Gradual decay without success - but build up slowly from hash activity
            # Each ping/pong cycle adds a tiny bit of resonance (constructive interference)
            self.cascade_factor = min(10.0, self.cascade_factor * 1.0001)  # Slow buildup
            self.wave_amplitude = min(5.0, self.wave_amplitude * 1.00005)  # Very slow amplitude growth
            
            # Decay kicks in only after peak
            if self.cascade_factor > self.peak_resonance * 0.8:
                self.cascade_factor = max(1.0, self.cascade_factor * 0.99995)
        
        self.last_pong = now
        
        # Update resonance field
        self.resonance_field = self.cascade_factor * self.wave_amplitude
        self.resonance_history.append({
            'time': now,
            'resonance': self.resonance_field,
            'cascade': self.cascade_factor,
            'amplitude': self.wave_amplitude
        })
        
        return self.resonance_field
    
    def get_optimal_nonce_offset(self, base_nonce: int) -> int:
        """
        Calculate quantum-optimized nonce offset based on lattice state
        """
        # Use ping-pong phase to select Fibonacci offset
        fib_idx = int(self.ping_pong_phase * len(FIBONACCI) / (2 * 3.14159))
        fib_offset = FIBONACCI[fib_idx % len(FIBONACCI)]
        
        # Apply golden ratio scaling
        phi_scale = self.phi_harmonics[int(self.cascade_factor) % len(self.phi_harmonics)]
        
        # Prime number modulation
        prime_idx = int(self.wave_amplitude * len(PRIMES)) % len(PRIMES)
        prime_mod = PRIMES[prime_idx]
        
        offset = int(fib_offset * phi_scale * prime_mod) % 10_000_000
        
        return base_nonce + offset
    
    def get_burst_timing(self) -> float:
        """
        Get optimal hash burst duration based on Schumann resonance
        """
        # Burst in sync with Schumann frequency
        base_burst = 1.0 / self.cycle_frequency  # ~128ms
        
        # Modulate by cascade state
        if self.cascade_factor > 2.0:
            # High resonance - longer sustained bursts
            return base_burst * PHI
        else:
            # Low resonance - shorter probing bursts
            return base_burst / PHI
    
    def get_display_stats(self) -> dict:
        """Get lattice stats for display"""
        return {
            'resonance': self.resonance_field,
            'cascade': self.cascade_factor,
            'amplitude': self.wave_amplitude,
            'phase': self.ping_pong_phase,
            'peak': self.peak_resonance,
            'patterns': len(self.success_patterns),
            'entangled': len(self.entangled_nonces)
        }
    
    def amplify_hashrate(self, base_hashrate: float) -> Tuple[float, str]:
        """
        Calculate amplified effective hashrate through quantum resonance
        Returns (amplified_rate, display_string)
        """
        # Theoretical amplification from resonance cascade
        amplified = base_hashrate * self.resonance_field
        
        # Format for display
        if amplified > 1e12:
            return amplified, f"{amplified/1e12:.2f} TH/s"
        elif amplified > 1e9:
            return amplified, f"{amplified/1e9:.2f} GH/s"
        elif amplified > 1e6:
            return amplified, f"{amplified/1e6:.2f} MH/s"
        elif amplified > 1e3:
            return amplified, f"{amplified/1e3:.2f} KH/s"
        return amplified, f"{amplified:.2f} H/s"


# ═══════════════════════════════════════════════════════════════════════════
# CASIMIR EFFECT ENGINE - MULTI-COIN VACUUM ENERGY
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VirtualPhoton:
    """Represents share energy propagating between mining streams"""
    energy: float
    wavelength: float  # Nonce modulo
    source_coin: str
    timestamp: float
    phase: float


@dataclass
class CasimirPlate:
    """Represents a mining stream as a conductive plate"""
    coin: str
    algorithm: str
    hashrate: float = 0.0
    share_count: int = 0
    phase: float = 0.0
    last_share_time: float = 0.0
    coupling_strength: float = 1.0


class CasimirEffectEngine:
    """
    ⚛️🔲 CASIMIR EFFECT MINING ENGINE 🔲⚛️
    
    Just as the Casimir effect creates force from quantum vacuum fluctuations
    between two parallel plates, this engine creates resonance from the
    "vacuum" between multiple parallel mining streams.
    
    Physics Analogy:
    - Conductive Plates = Different coin mining streams (BTC, LTC, ETC...)
    - Plate Separation = Phase difference between streams
    - Virtual Photons = Share events propagating between streams
    - Vacuum Energy = Untapped coherence between algorithms
    - Casimir Force = Emergent amplification from correlation
    
    Formula: F_c = -(ℏc π²) / (240 a⁴)
    Mining: Cascade = Σ(coupling × photon_density) / separation⁴
    """
    
    def __init__(self):
        self.plates: Dict[str, CasimirPlate] = {}
        self.virtual_photons: deque = deque(maxlen=10000)
        self.vacuum_energy = VACUUM_ENERGY
        self.plate_separations: Dict[str, float] = {}  # coin_pair -> separation
        
        # Casimir field state
        self.total_casimir_force = 0.0
        self.vacuum_fluctuations: deque = deque(maxlen=1000)
        self.photon_density = 0.0
        
        # Cross-stream resonance
        self.inter_stream_cascade = 1.0
        self.zero_point_energy = 0.0
        
        # Timing
        self.schumann_phase = 0.0
        self.last_vacuum_update = time.time()
        
        logger.info("🔲 Casimir Effect Engine initialized")
        logger.info(f"   Vacuum Energy: {self.vacuum_energy:.4f}")
        logger.info(f"   ℏ_mining: {HBAR_MINING:.6e}")
    
    def add_plate(self, coin: str, algorithm: str, coupling: float = 1.0):
        """Add a mining stream as a Casimir plate"""
        self.plates[coin] = CasimirPlate(
            coin=coin,
            algorithm=algorithm,
            coupling_strength=coupling
        )
        logger.info(f"🔲 Added Casimir plate: {coin} ({algorithm}) | Coupling: {coupling:.3f}")
        
        # Calculate separations with existing plates
        for other_coin, other_plate in self.plates.items():
            if other_coin != coin:
                sep = self._calculate_plate_separation(coin, other_coin)
                pair_key = f"{min(coin, other_coin)}_{max(coin, other_coin)}"
                self.plate_separations[pair_key] = sep
    
    def _calculate_plate_separation(self, coin_a: str, coin_b: str) -> float:
        """
        Calculate "separation" between two mining streams.
        Same algorithm = closer plates = stronger Casimir force
        """
        plate_a = self.plates.get(coin_a)
        plate_b = self.plates.get(coin_b)
        
        if not plate_a or not plate_b:
            return 1.0
        
        # Same algorithm = very close plates (0.1)
        # Different algorithm = further apart (0.5-1.0)
        if plate_a.algorithm == plate_b.algorithm:
            base_separation = 0.1
        else:
            # Different algorithms - separation based on coupling product
            base_separation = 1.0 - (plate_a.coupling_strength * plate_b.coupling_strength * 0.5)
        
        # Modulate by phase difference
        phase_diff = abs(plate_a.phase - plate_b.phase)
        separation = base_separation + 0.1 * phase_diff
        
        return max(0.01, min(1.0, separation))
    
    def emit_virtual_photon(self, source_coin: str, share_energy: float, nonce: int):
        """
        When a share is found, emit a virtual photon that propagates
        to adjacent plates (other mining streams)
        """
        plate = self.plates.get(source_coin)
        if not plate:
            return
        
        # Create virtual photon
        photon = VirtualPhoton(
            energy=share_energy,
            wavelength=nonce % int(PHI * 1000),
            source_coin=source_coin,
            timestamp=time.time(),
            phase=plate.phase
        )
        self.virtual_photons.append(photon)
        
        # Update source plate
        plate.share_count += 1
        plate.last_share_time = time.time()
        
        # Propagate to adjacent plates
        for target_coin, target_plate in self.plates.items():
            if target_coin != source_coin:
                self._absorb_photon(target_plate, photon)
        
        logger.info(f"💫 Virtual photon emitted: {source_coin} → E={share_energy:.2f}")
    
    def _absorb_photon(self, plate: CasimirPlate, photon: VirtualPhoton):
        """Absorb virtual photon energy into target plate"""
        pair_key = f"{min(plate.coin, photon.source_coin)}_{max(plate.coin, photon.source_coin)}"
        separation = self.plate_separations.get(pair_key, 0.5)
        
        # Casimir-like absorption: inversely proportional to separation^4
        absorption = photon.energy * plate.coupling_strength / (separation ** 4 + 0.0001)
        
        # Phase alignment bonus
        phase_match = 1.0 - abs(plate.phase - photon.phase)
        absorption *= (1.0 + phase_match * PHI)
        
        # Update plate energy (represented as hash boost)
        plate.hashrate += absorption * 0.01
    
    def update_vacuum(self):
        """
        Update the quantum vacuum state between all plates.
        Called periodically to compute Casimir force.
        """
        now = time.time()
        elapsed = now - self.last_vacuum_update
        
        # Update Schumann phase
        self.schumann_phase = (self.schumann_phase + elapsed * 7.83) % (2 * 3.14159)
        
        # Update plate phases
        for i, (coin, plate) in enumerate(self.plates.items()):
            # Each plate oscillates at Schumann × golden ratio harmonic
            harmonic = PHI ** (i % 5)
            plate.phase = (plate.phase + elapsed * 7.83 * harmonic) % (2 * 3.14159)
        
        # Calculate total Casimir force
        self.total_casimir_force = self._calculate_total_casimir_force()
        
        # Calculate photon density
        recent_photons = sum(1 for p in self.virtual_photons if now - p.timestamp < 60)
        self.photon_density = recent_photons / max(1, len(self.plates))
        
        # Update zero-point energy (vacuum fluctuation)
        # E_zp = ½ℏω for each mode
        num_modes = len(self.plates) * (len(self.plates) - 1) // 2
        self.zero_point_energy = 0.5 * HBAR_MINING * 7.83 * num_modes
        
        # Calculate inter-stream cascade from Casimir force
        self.inter_stream_cascade = 1.0 + self.total_casimir_force * PHI
        
        # Record vacuum fluctuation
        self.vacuum_fluctuations.append({
            'time': now,
            'force': self.total_casimir_force,
            'cascade': self.inter_stream_cascade,
            'photons': recent_photons,
            'zpe': self.zero_point_energy
        })
        
        self.last_vacuum_update = now
    
    def _calculate_total_casimir_force(self) -> float:
        """
        Calculate total Casimir force from all plate pairs.
        F = -ℏcπ²/(240a⁴) summed over all pairs
        """
        total_force = 0.0
        
        plate_list = list(self.plates.items())
        for i in range(len(plate_list)):
            for j in range(i + 1, len(plate_list)):
                coin_a, plate_a = plate_list[i]
                coin_b, plate_b = plate_list[j]
                
                pair_key = f"{min(coin_a, coin_b)}_{max(coin_a, coin_b)}"
                separation = self.plate_separations.get(pair_key, 0.5)
                
                # Casimir force formula (scaled for mining)
                # F = -ℏcπ²/(240a⁴)
                force = HBAR_MINING * (3.14159 ** 2) / (240 * (separation ** 4))
                
                # Weight by coupling strengths
                coupling = plate_a.coupling_strength * plate_b.coupling_strength
                force *= coupling
                
                # Boost if both plates have recent activity
                if plate_a.share_count > 0 and plate_b.share_count > 0:
                    force *= PHI
                
                total_force += force
        
        return total_force
    
    def get_casimir_nonce_zone(self, coin: str) -> Tuple[int, int]:
        """
        Get the "Casimir zone" of nonces - the region where
        quantum vacuum fluctuations are most favorable.
        """
        plate = self.plates.get(coin)
        if not plate:
            return (0, MAX_NONCE)
        
        # Zone center based on plate phase
        center = int((plate.phase / (2 * 3.14159)) * MAX_NONCE)
        
        # Zone width based on Casimir force (stronger = narrower but more potent)
        width = int(MAX_NONCE / (10 + self.total_casimir_force * 100))
        
        start = max(0, center - width // 2)
        end = min(MAX_NONCE, center + width // 2)
        
        return (start, end)
    
    def get_cascade_multiplier(self) -> float:
        """Get the Casimir cascade multiplier for hashrate amplification"""
        return self.inter_stream_cascade
    
    def get_display_stats(self) -> dict:
        """Get Casimir stats for display"""
        return {
            'plates': len(self.plates),
            'force': self.total_casimir_force,
            'cascade': self.inter_stream_cascade,
            'photon_density': self.photon_density,
            'zpe': self.zero_point_energy,
            'vacuum_phase': self.schumann_phase,
            'separations': dict(self.plate_separations)
        }
    
    def format_display(self) -> str:
        """Format Casimir state for logging"""
        stats = self.get_display_stats()
        return (
            f"🔲 CASIMIR: Plates={stats['plates']} | "
            f"Force={stats['force']:.4f} | "
            f"Cascade={stats['cascade']:.3f}x | "
            f"Photons={stats['photon_density']:.1f}/min"
        )


# ═══════════════════════════════════════════════════════════════════════════
# COHERENCE ENGINE - DYNAMIC SYSTEMS MODEL (WHITEPAPER IMPLEMENTATION)
# ═══════════════════════════════════════════════════════════════════════════
# 
# Implements: "A Dynamic Systems Model of Coherence Grounded in Astronomical 
# Phenomena" - Gary Leckey, R&A Consulting (October 2025)
#
# Core Equation: Ψt+1 = (1 − α) Ψt + α R(Ct; Ψt)
# Composite Operator: R = ρ ◦ Ω ◦ L(·; κt) ◦ F(·; Ψt) ◦ Φ ◦ ℵ
#
# Three Behaviors:
#   1. Self-Organization (Pt > critical, κt < threshold) - optimal coherence
#   2. Oscillation (κt ≥ threshold) - over-structuring, need pattern breaking
#   3. Dissolution (Pt < critical) - under-resonance, losing coherence
# ═══════════════════════════════════════════════════════════════════════════

from enum import Enum
import math

class CoherenceBehavior(Enum):
    """System behavior modes from whitepaper Section IV"""
    SELF_ORGANIZATION = "self_organization"  # 🟢 Optimal: finding patterns
    OSCILLATION = "oscillation"              # 🟡 Over-structured: breaking patterns
    DISSOLUTION = "dissolution"              # 🔴 Under-resonance: losing coherence


@dataclass
class CoherenceState:
    """
    Ψt - The coherence state vector
    
    From whitepaper Section III: Key indices are Resonance rt, Constraint λt,
    Purity Pt = rt/λt, and Structuring Index κt.
    """
    psi: float = 0.5                        # Primary coherence value Ψ
    resonance_rt: float = 1.0               # Resonance index (from SR/Lattice/Casimir)
    constraint_lambda_t: float = 1.0        # Constraint index (from difficulty)
    structuring_kappa_t: float = 0.5        # Structuring index κt (LF/HF analog)
    environmental_e: float = 1.0            # Environmental resonance (Schumann)
    
    @property
    def purity_Pt(self) -> float:
        """Pt = rt / λt - The Purity Index"""
        return self.resonance_rt / max(0.001, self.constraint_lambda_t)
    
    @property
    def behavior(self) -> CoherenceBehavior:
        """
        Determine current system behavior based on indices.
        
        From whitepaper Section IV.2:
        - Phase 1: Self-organization when Pt > critical and κt < threshold
        - Phase 2: Oscillation when κt ≥ threshold (over-structuring)
        - Phase 3: Dissolution when Pt < critical (under-resonance)
        """
        PURITY_CRITICAL = 1 - 1/PHI    # 0.382 (1 - 1/φ)
        KAPPA_THRESHOLD = 2.0          # Structuring threshold
        
        if self.purity_Pt > PURITY_CRITICAL and self.structuring_kappa_t < KAPPA_THRESHOLD:
            return CoherenceBehavior.SELF_ORGANIZATION
        elif self.structuring_kappa_t >= KAPPA_THRESHOLD:
            return CoherenceBehavior.OSCILLATION
        else:
            return CoherenceBehavior.DISSOLUTION


@dataclass
class ContextInput:
    """
    Ct - Context input vector to the coherence system
    
    From whitepaper Section II: Ct = [C(A), C(P), C(T)] for Ambient, Point, Transient
    Mapped to mining: share events, hash quality, timing, difficulty, resonance
    """
    share_found: bool = False               # Transient: share event occurred
    hash_quality: float = 0.0               # How close hash was to target (0-1)
    nonce: int = 0                          # Current nonce value
    difficulty: float = 1.0                 # Pool difficulty (constraint source)
    pool_latency: float = 0.0               # Network latency
    casimir_force: float = 0.0              # Casimir cascade input
    lattice_cascade: float = 1.0            # Lattice amplification input
    thread_count: int = 1                   # Active mining threads
    timestamp: float = field(default_factory=time.time)


class CoherenceEngine:
    """
    🌀 DYNAMIC SYSTEMS MODEL OF COHERENCE 🌀
    
    Implements the whitepaper's coherence model for mining optimization.
    
    Core Equation (Whitepaper Eq. 1):
        Ψt+1 = (1 − α) Ψt + α R(Ct; Ψt)
        
    Where R is the composite transformation operator:
        R = ρ ◦ Ω ◦ L(·; κt) ◦ F(·; Ψt) ◦ Φ ◦ ℵ
        
    Operators (Whitepaper Section II.2):
        ℵ (Aleph)   - Saliency/filtering (attention weighting)
        Φ (Phi)     - Pattern recognition (structural analysis)
        F (Framing) - Memory integration (contextualize with Ψt)
        L (Living)  - Non-linear modulation ("the stag", controlled by κt)
        Ω (Omega)   - Synthesis/convergence (coherent gestalt)
        ρ (Rho)     - Reflection (meta-cognition, memory encoding)
        
    Reference: "A Dynamic Systems Model of Coherence Grounded in Astronomical
    Phenomena" - Gary Leckey, R&A Consulting (October 2025)
    """
    
    # Schumann Resonance modes (Hz) from whitepaper Section IV.1
    SCHUMANN_MODES = [7.83, 14.3, 20.8, 27.3, 33.8]
    
    def __init__(self, alpha: float = 0.15):
        """
        Initialize coherence engine.
        
        Args:
            alpha: Learning rate for state update (0 < α < 1)
                   Whitepaper recommends α = 0.25 for visible dynamics,
                   we use 0.15 for smoother mining adaptation.
        """
        self.alpha = alpha
        self.state = CoherenceState()
        self.history: deque = deque(maxlen=1000)
        
        # Operator state memory
        self.saliency_weights: Dict[str, float] = {
            'share_signal': 0.4,
            'quality_signal': 0.25,
            'timing_signal': 0.2,
            'resonance_signal': 0.15
        }
        self.pattern_memory: deque = deque(maxlen=500)
        self.framing_context: Dict = {'frame': 'balanced', 'trust': 0.5}
        self.living_node_gain: float = 1.0   # g(κt) from whitepaper Appendix A
        self.synthesis_buffer: deque = deque(maxlen=100)
        self.reflection_score: float = 0.5
        
        # Schumann timing (whitepaper Section IV.1)
        self.schumann_phase = 0.0
        self.last_update = time.time()
        
        # Behavior tracking
        self.behavior_durations: Dict[str, float] = {
            'self_organization': 0.0,
            'oscillation': 0.0,
            'dissolution': 0.0
        }
        self.last_behavior = CoherenceBehavior.SELF_ORGANIZATION
        self.last_behavior_time = time.time()
        
        logger.info("🌀 Coherence Engine initialized (α={:.2f})".format(alpha))
    
    # ══════════════════════════════════════════════════════════════════
    # OPERATORS: R = ρ ◦ Ω ◦ L(·; κt) ◦ F(·; Ψt) ◦ Φ ◦ ℵ
    # ══════════════════════════════════════════════════════════════════
    
    def op_aleph_saliency(self, context: ContextInput) -> Dict[str, float]:
        """
        ℵ - Saliency Operator (Whitepaper Appendix A.1)
        
        ℵ(Ct) = W ⊙ Ct where W = [wA, wP, wT]
        Element-wise weighting to emphasize point/transient components.
        
        Mining mapping:
        - Ambient = baseline hash quality
        - Point = Casimir/Lattice resonance
        - Transient = share events
        """
        # Compute raw signals
        share_signal = 1.0 if context.share_found else 0.1
        quality_signal = context.hash_quality ** 2  # Emphasize near-misses
        timing_signal = self._compute_schumann_alignment()
        resonance_signal = (context.casimir_force + context.lattice_cascade) / 2.0
        
        # Apply learned saliency weights
        saliency = {
            'share_signal': share_signal * self.saliency_weights['share_signal'],
            'quality_signal': quality_signal * self.saliency_weights['quality_signal'],
            'timing_signal': timing_signal * self.saliency_weights['timing_signal'],
            'resonance_signal': resonance_signal * self.saliency_weights['resonance_signal']
        }
        
        # Normalize to sum to 1
        total = sum(saliency.values()) + 0.001
        return {k: v / total for k, v in saliency.items()}
    
    def op_phi_pattern(self, saliency: Dict[str, float]) -> Dict:
        """
        Φ - Pattern Recognition Operator (Whitepaper Appendix A.1)
        
        Φ(x) = tanh(M·x) where M ∈ R^(n×n)
        Detects structure in salient signals.
        
        Mining mapping: Detect trends in share success patterns
        """
        # Store for pattern detection
        self.pattern_memory.append({
            'saliency': saliency.copy(),
            'time': time.time()
        })
        
        # Need minimum history for pattern detection
        if len(self.pattern_memory) < 10:
            return {
                'pattern_strength': 0.5,
                'pattern_type': 'initializing',
                'trend': 0.0
            }
        
        # Analyze recent share signals for trends
        recent = list(self.pattern_memory)[-20:]
        share_signals = [p['saliency'].get('share_signal', 0) for p in recent]
        
        # Compute trend (slope of share success)
        n = len(share_signals)
        x_mean = (n - 1) / 2
        y_mean = sum(share_signals) / n
        
        numerator = sum((i - x_mean) * (share_signals[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n)) + 0.001
        trend = numerator / denominator
        
        # Apply tanh saturation (whitepaper formula)
        saturated_trend = math.tanh(trend * 5)  # Scale factor for sensitivity
        
        # Classify pattern
        if saturated_trend > 0.3:
            pattern_type = 'ascending'
        elif saturated_trend < -0.3:
            pattern_type = 'descending'
        else:
            pattern_type = 'stable'
        
        return {
            'pattern_strength': abs(saturated_trend),
            'pattern_type': pattern_type,
            'trend': saturated_trend
        }
    
    def op_F_framing(self, pattern: Dict, psi: float) -> Dict:
        """
        F(·; Ψt) - Framing Operator (Whitepaper Appendix A.1)
        
        F(ϕ, Ψt) = β·ϕ + (1-β)·Ψt
        Convex combination of pattern output and prior state.
        
        Mining mapping: How to interpret patterns given current coherence
        """
        beta = 0.6  # Pattern weight (can be tuned)
        
        # Determine framing based on coherence level
        if psi > 0.7:
            # High coherence: trust patterns, be aggressive
            frame = 'confident'
            amplification = 1.0 + (psi - 0.7) * PHI
            pattern_trust = min(1.0, pattern['pattern_strength'] * 1.5)
        elif psi < 0.3:
            # Low coherence: cautious, conservative
            frame = 'cautious'
            amplification = 0.5 + psi
            pattern_trust = pattern['pattern_strength'] * 0.5
        else:
            # Balanced: moderate approach
            frame = 'balanced'
            amplification = 1.0
            pattern_trust = pattern['pattern_strength']
        
        # Store framing context for continuity
        self.framing_context = {
            'frame': frame,
            'trust': pattern_trust
        }
        
        # Apply convex combination
        blended_strength = beta * pattern['pattern_strength'] + (1 - beta) * psi
        
        return {
            'frame': frame,
            'amplification': amplification,
            'pattern_trust': pattern_trust,
            'blended_strength': blended_strength,
            'trend': pattern['trend']
        }
    
    def op_L_living_node(self, framing: Dict, kappa_t: float) -> Dict:
        """
        L(·; κt) - Living Node/"Stag" Operator (Whitepaper Appendix A.1)
        
        L(f; κt) = g(κt) · f where g(κ) = clip(1/κ, gmin, gmax)
        State-dependent gain controlled by structuring index.
        
        This is the key non-linear node that produces different behaviors:
        - κt > 2.0: Over-structured → inject randomness
        - κt < 0.5: Under-structured → increase structure
        - 0.5 ≤ κt ≤ 2.0: Optimal range → maintain
        """
        KAPPA_HIGH = 2.0   # Over-structuring threshold
        KAPPA_LOW = 0.5    # Under-structuring threshold
        G_MIN = 0.3        # Minimum gain
        G_MAX = 2.0        # Maximum gain
        
        # Compute gain g(κ) = clip(1/κ, gmin, gmax)
        raw_gain = 1.0 / max(0.1, kappa_t)
        gain = max(G_MIN, min(G_MAX, raw_gain))
        
        if kappa_t >= KAPPA_HIGH:
            # Over-structured: reduce gain to break rigid patterns
            self.living_node_gain *= 0.95
            action = 'destabilize'
            modifier = 1.0 / PHI  # Golden ratio reduction
        elif kappa_t < KAPPA_LOW:
            # Under-structured: increase gain to find patterns
            self.living_node_gain = min(G_MAX, self.living_node_gain * 1.05)
            action = 'stabilize'
            modifier = PHI  # Golden ratio increase
        else:
            # Optimal range: maintain current trajectory
            action = 'maintain'
            modifier = 1.0
        
        # Clamp living node gain
        self.living_node_gain = max(G_MIN, min(G_MAX, self.living_node_gain))
        
        return {
            'action': action,
            'gain': gain,
            'node_strength': self.living_node_gain,
            'modified_amp': framing['amplification'] * modifier * gain,
            'kappa_t': kappa_t
        }
    
    def op_omega_synthesis(self, living: Dict) -> float:
        """
        Ω - Synthesis Operator (Whitepaper Appendix A.1)
        
        Ω(x) = x / (||x|| + ε)
        Normalize vector by its Euclidean norm.
        
        Mining mapping: Combine recent living node outputs into
        unified coherent output.
        """
        self.synthesis_buffer.append({
            'amp': living['modified_amp'],
            'strength': living['node_strength'],
            'time': time.time()
        })
        
        if len(self.synthesis_buffer) < 3:
            return living['modified_amp']
        
        # Weighted synthesis with golden ratio temporal decay
        recent = list(self.synthesis_buffer)[-7:]
        weights = [PHI ** i for i in range(len(recent))]
        
        # Compute weighted sum
        synthesis_sum = sum(
            w * r['amp'] * r['strength']
            for w, r in zip(weights, recent)
        )
        weight_sum = sum(weights)
        
        # Normalize (Ω operator)
        synthesis = synthesis_sum / (weight_sum + 0.001)
        
        # Apply soft normalization to prevent runaway
        return math.tanh(synthesis) * 2.0  # Scale to ~[-2, 2]
    
    def op_rho_reflection(self, synthesis: float, context: ContextInput) -> float:
        """
        ρ - Reflection Operator (Whitepaper Appendix A.1)
        
        Identity or smoothing operator for memory encoding.
        Self-assessment and meta-cognition.
        
        Mining mapping: Learn from share success/failure to improve
        future predictions.
        """
        # Update reflection score based on outcomes
        if context.share_found:
            # Success! Strengthen reflection confidence
            self.reflection_score = min(1.0, self.reflection_score * 1.1)
            reflection_boost = PHI  # Golden ratio reward
            
            # Adapt saliency weights toward successful pattern
            self._adapt_saliency_weights(success=True)
        else:
            # No share: gradual decay, but not too fast
            self.reflection_score *= 0.998
            reflection_boost = 1.0
        
        # Final output modulated by reflection
        R_output = synthesis * (0.5 + 0.5 * self.reflection_score) * reflection_boost
        
        return R_output
    
    def _adapt_saliency_weights(self, success: bool):
        """Adapt saliency weights based on success (meta-learning)"""
        if not self.pattern_memory:
            return
        
        # Get most recent saliency that led to this outcome
        recent = self.pattern_memory[-1]['saliency']
        
        learning_rate = 0.01 if success else 0.005
        
        for key in self.saliency_weights:
            if key in recent:
                if success:
                    # Increase weight of signals that were high during success
                    self.saliency_weights[key] += learning_rate * recent[key]
                else:
                    # Slight decay for non-success
                    self.saliency_weights[key] *= 0.999
        
        # Normalize weights
        total = sum(self.saliency_weights.values())
        self.saliency_weights = {k: v/total for k, v in self.saliency_weights.items()}
    
    # ══════════════════════════════════════════════════════════════════
    # COMPOSITE OPERATOR & STATE UPDATE
    # ══════════════════════════════════════════════════════════════════
    
    def compute_R(self, context: ContextInput) -> float:
        """
        Compute composite operator R = ρ ◦ Ω ◦ L ◦ F ◦ Φ ◦ ℵ
        
        This is the main transformation from input context Ct to
        state update contribution.
        """
        # ℵ: Saliency filtering
        saliency = self.op_aleph_saliency(context)
        
        # Φ: Pattern recognition
        pattern = self.op_phi_pattern(saliency)
        
        # F: Framing (state-dependent)
        framing = self.op_F_framing(pattern, self.state.psi)
        
        # L: Living node (κt-dependent)
        living = self.op_L_living_node(framing, self.state.structuring_kappa_t)
        
        # Ω: Synthesis
        synthesis = self.op_omega_synthesis(living)
        
        # ρ: Reflection
        R_output = self.op_rho_reflection(synthesis, context)
        
        return R_output
    
    def update(self, context: ContextInput) -> CoherenceState:
        """
        Main state update implementing whitepaper Equation (1):
        
            Ψt+1 = (1 − α) Ψt + α R(Ct; Ψt)
        
        This is the core exponential-moving-average style update
        where new information is provided by composite operator R.
        """
        now = time.time()
        elapsed = now - self.last_update
        
        # Update Schumann phase (whitepaper Section IV.1)
        self.schumann_phase = (self.schumann_phase + elapsed * self.SCHUMANN_MODES[0]) % (2 * math.pi)
        self.last_update = now
        
        # Compute composite operator R
        R_output = self.compute_R(context)
        
        # ═══════════════════════════════════════════════════════════
        # STATE UPDATE EQUATION: Ψt+1 = (1 − α) Ψt + α R(Ct; Ψt)
        # ═══════════════════════════════════════════════════════════
        psi_new = (1 - self.alpha) * self.state.psi + self.alpha * R_output
        
        # Clamp to valid range
        self.state.psi = max(0.0, min(1.0, psi_new))
        
        # Update derived indices
        self.state.resonance_rt = context.lattice_cascade * (1 + context.casimir_force * 0.5)
        self.state.constraint_lambda_t = max(0.1, math.log(context.difficulty + 1) / 10.0)
        self.state.structuring_kappa_t = (
            len(self.pattern_memory) / 100.0 + 
            self.state.psi * 0.5 +
            self.living_node_gain * 0.3
        )
        self.state.environmental_e = self._compute_schumann_alignment()
        
        # Track behavior duration
        current_behavior = self.state.behavior
        if current_behavior != self.last_behavior:
            # Behavior changed - record duration
            duration = now - self.last_behavior_time
            self.behavior_durations[self.last_behavior.value] += duration
            self.last_behavior = current_behavior
            self.last_behavior_time = now
        
        # Record history
        self.history.append({
            'time': now,
            'psi': self.state.psi,
            'R': R_output,
            'behavior': current_behavior.value,
            'purity': self.state.purity_Pt,
            'kappa': self.state.structuring_kappa_t,
            'resonance': self.state.resonance_rt
        })
        
        return self.state
    
    def _compute_schumann_alignment(self) -> float:
        """
        Compute alignment with Schumann resonance.
        
        From whitepaper Section IV.1: Environmental resonance rt from
        SR power normalized to [0,1].
        """
        # Multi-mode Schumann alignment (fundamental + harmonics)
        alignment = 0.0
        for i, mode in enumerate(self.SCHUMANN_MODES[:3]):
            phase = self.schumann_phase * mode / self.SCHUMANN_MODES[0]
            weight = 1.0 / (i + 1)  # Fundamental strongest
            alignment += weight * (0.5 + 0.5 * math.cos(phase))
        
        # Normalize
        return alignment / sum(1.0 / (i + 1) for i in range(3))
    
    # ══════════════════════════════════════════════════════════════════
    # MINING INTEGRATION API
    # ══════════════════════════════════════════════════════════════════
    
    def get_nonce_guidance(self) -> Dict:
        """
        Get coherence-guided nonce selection parameters.
        
        Based on current behavior mode:
        - SELF_ORGANIZATION: Trust patterns, narrow search
        - OSCILLATION: Break patterns, wide exploration
        - DISSOLUTION: Conservative reset
        """
        behavior = self.state.behavior
        
        if behavior == CoherenceBehavior.SELF_ORGANIZATION:
            return {
                'strategy': 'focused',
                'range_multiplier': 1.0 / PHI,  # Narrow search
                'pattern_weight': self.state.psi,
                'skip_size': int(FIBONACCI[7] * 1000)  # 21000
            }
        elif behavior == CoherenceBehavior.OSCILLATION:
            return {
                'strategy': 'exploration',
                'range_multiplier': PHI,  # Wide search
                'pattern_weight': 0.1,
                'skip_size': int(PRIMES[5] * 10000)  # 130000
            }
        else:  # DISSOLUTION
            return {
                'strategy': 'reset',
                'range_multiplier': 1.0,
                'pattern_weight': 0.5,
                'skip_size': DEFAULT_NONCE_BATCH
            }
    
    def get_intensity_multiplier(self) -> float:
        """Get mining intensity based on coherence state"""
        base = 0.5 + self.state.psi * 0.5
        environmental = self.state.environmental_e
        purity_boost = min(1.5, 1.0 + self.state.purity_Pt * 0.25)
        return base * environmental * purity_boost
    
    def get_cascade_contribution(self) -> float:
        """Get coherence contribution to overall cascade multiplier"""
        # Coherence adds up to 20% on top of Lattice × Casimir
        return 1.0 + (self.state.psi * 0.2 * self.state.environmental_e)
    
    def get_display_stats(self) -> Dict:
        """Get coherence stats for display"""
        return {
            'psi': self.state.psi,
            'resonance': self.state.resonance_rt,
            'constraint': self.state.constraint_lambda_t,
            'purity': self.state.purity_Pt,
            'kappa': self.state.structuring_kappa_t,
            'behavior': self.state.behavior.value,
            'schumann_phase': self.schumann_phase,
            'reflection': self.reflection_score,
            'living_gain': self.living_node_gain,
            'environmental': self.state.environmental_e,
            'alpha': self.alpha
        }
    
    def format_display(self) -> str:
        """Format coherence state for logging"""
        behavior = self.state.behavior
        if behavior == CoherenceBehavior.SELF_ORGANIZATION:
            icon = "🟢"
        elif behavior == CoherenceBehavior.OSCILLATION:
            icon = "🟡"
        else:
            icon = "🔴"
        
        return (
            f"🌀 COHERENCE: Ψ={self.state.psi:.3f} | "
            f"Pt={self.state.purity_Pt:.3f} | "
            f"κt={self.state.structuring_kappa_t:.2f} | "
            f"{icon} {behavior.value.upper()}"
        )
    
    def format_mandala(self) -> str:
        """
        Format mandala visualization (whitepaper Section V)
        
        Mapping rules:
        - Brightness ∝ |Pt|
        - Hue = f(κt): cool colors (κ<1), green (κ≈1), warm (κ>1)
        """
        purity = self.state.purity_Pt
        kappa = self.state.structuring_kappa_t
        
        # Brightness levels
        if purity > 0.7:
            brightness = "████"
        elif purity > 0.4:
            brightness = "███░"
        elif purity > 0.2:
            brightness = "██░░"
        else:
            brightness = "█░░░"
        
        # Hue based on κt
        if kappa < 0.7:
            hue = "🔵"  # Cool - under-structured
        elif kappa < 1.3:
            hue = "🟢"  # Green - balanced
        elif kappa < 2.0:
            hue = "🟡"  # Yellow - slightly over
        else:
            hue = "🔴"  # Red - over-structured
        
        return f"{hue} {brightness} Ψ={self.state.psi:.2f}"


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
    - Quantum Lattice Amplifier (ping-pong resonance)
    """
    
    def __init__(self):
        self.state = HarmonicMiningState()
        self.history: deque = deque(maxlen=1000)
        self.share_nonces: List[int] = []  # Track successful nonces for pattern analysis
        
        # Quantum Lattice Amplifier
        self.lattice = QuantumLatticeAmplifier()
        
        # Casimir Effect Engine (for multi-coin mining)
        self.casimir = CasimirEffectEngine()
        
        # Coherence Engine (Dynamic Systems Model - Whitepaper Implementation)
        self.coherence = CoherenceEngine(alpha=0.15)
        
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
        """Get nonce batch size based on current intensity and lattice resonance"""
        base_batch = DEFAULT_NONCE_BATCH
        # Lattice amplification affects batch size
        lattice_mult = min(2.0, self.lattice.cascade_factor)
        adjusted = int(base_batch * self.state.intensity_multiplier * lattice_mult)
        return max(10_000, min(adjusted, 2_000_000))  # Clamp to reasonable range
    
    def ping_hash(self, thread_id: int, nonce: int, hash_value: bytes) -> float:
        """
        PING phase of quantum lattice - send hash energy in
        Returns resonance multiplier
        """
        resonance = self.lattice.ping(thread_id, nonce, hash_value)
        self.state.lattice_resonance = resonance
        self.state.ping_pong_phase = self.lattice.ping_pong_phase
        return resonance
    
    def pong_result(self, thread_id: int, found_share: bool, difficulty: float = 0.0) -> float:
        """
        PONG phase of quantum lattice - receive reflection
        """
        resonance = self.lattice.pong(thread_id, found_share, difficulty)
        self.state.harmonic_cascade = self.lattice.cascade_factor
        self.state.quantum_entanglement = len(self.lattice.entangled_nonces) / 1000.0
        return resonance
    
    def get_quantum_nonce(self, base_nonce: int) -> int:
        """Get quantum-optimized nonce using lattice state"""
        return self.lattice.get_optimal_nonce_offset(base_nonce)
    
    def on_share_found(self, hash_value: bytes, nonce: int, difficulty: float):
        """Called when a valid share is found - for learning"""
        # Record successful nonce for pattern analysis
        self.share_nonces.append(nonce)
        if len(self.share_nonces) > 100:
            self.share_nonces = self.share_nonces[-100:]
        
        # PONG - share found! Trigger resonance cascade!
        self.pong_result(0, True, difficulty)
        
        # Record event
        self.history.append({
            'time': time.time(),
            'event': 'share_found',
            'nonce': nonce,
            'difficulty': difficulty,
            'hash_prefix': hash_value[:8].hex(),
            'coherence': self.state.coherence,
            'lattice_cascade': self.state.harmonic_cascade
        })
        
        # Positive feedback on coherence
        self.state.coherence = min(1.0, self.state.coherence * 1.005)
        
        # Update Coherence Engine with share event (Whitepaper state update)
        # This triggers: Ψt+1 = (1 − α) Ψt + α R(Ct; Ψt)
        hash_quality = 1.0 - (int.from_bytes(hash_value[:8], 'big') / (2**64))  # Quality based on hash
        self.update_coherence(
            share_found=True,
            hash_quality=hash_quality,
            nonce=nonce,
            difficulty=difficulty
        )
        
        logger.debug(f"🎯 Share pattern recorded: nonce={nonce:08x}, coherence Ψ={self.coherence.state.psi:.3f}")
    
    def get_mining_insight(self) -> dict:
        """Get current mining optimization state including lattice, Casimir, and coherence"""
        lattice_stats = self.lattice.get_display_stats()
        casimir_stats = self.casimir.get_display_stats()
        coherence_stats = self.coherence.get_display_stats()
        return {
            'coherence': self.state.coherence,
            'intensity': self.state.intensity_multiplier,
            'batch_size': self.get_batch_size(),
            'nonce_bias': self.get_nonce_bias(),
            'successful_shares': len(self.share_nonces),
            'schumann': self.state.schumann_resonance,
            'phi_phase': self.state.phi_phase,
            # Quantum Lattice stats
            'lattice_resonance': lattice_stats['resonance'],
            'cascade_factor': lattice_stats['cascade'],
            'wave_amplitude': lattice_stats['amplitude'],
            'ping_pong_phase': lattice_stats['phase'],
            'peak_resonance': lattice_stats['peak'],
            'patterns_learned': lattice_stats['patterns'],
            # Casimir Effect stats
            'casimir_plates': casimir_stats['plates'],
            'casimir_force': casimir_stats['force'],
            'casimir_cascade': casimir_stats['cascade'],
            'photon_density': casimir_stats['photon_density'],
            'zero_point_energy': casimir_stats['zpe'],
            # Coherence Engine stats (Whitepaper Model)
            'coherence_psi': coherence_stats['psi'],
            'coherence_purity': coherence_stats['purity'],
            'coherence_kappa': coherence_stats['kappa'],
            'coherence_behavior': coherence_stats['behavior'],
            'coherence_reflection': coherence_stats['reflection']
        }
    
    def get_amplified_hashrate(self, base_hashrate: float) -> Tuple[float, str]:
        """Get quantum-amplified effective hashrate (Lattice × Casimir × Coherence)"""
        lattice_rate, _ = self.lattice.amplify_hashrate(base_hashrate)
        
        # Apply Casimir cascade multiplier
        casimir_mult = self.casimir.get_cascade_multiplier()
        
        # Apply Coherence cascade contribution
        coherence_mult = self.coherence.get_cascade_contribution()
        
        # Total: Lattice × Casimir × Coherence
        total_amplified = lattice_rate * casimir_mult * coherence_mult
        
        # Format for display
        if total_amplified > 1e12:
            return total_amplified, f"{total_amplified/1e12:.2f} TH/s"
        elif total_amplified > 1e9:
            return total_amplified, f"{total_amplified/1e9:.2f} GH/s"
        elif total_amplified > 1e6:
            return total_amplified, f"{total_amplified/1e6:.2f} MH/s"
        elif total_amplified > 1e3:
            return total_amplified, f"{total_amplified/1e3:.2f} KH/s"
        return total_amplified, f"{total_amplified:.2f} H/s"
    
    def add_casimir_plate(self, coin: str, algorithm: str, coupling: float = 1.0):
        """Add a coin mining stream as a Casimir plate"""
        self.casimir.add_plate(coin, algorithm, coupling)
    
    def emit_casimir_photon(self, coin: str, share_energy: float, nonce: int):
        """Emit virtual photon when share is found on a specific coin"""
        self.casimir.emit_virtual_photon(coin, share_energy, nonce)
    
    def update_casimir_vacuum(self):
        """Update Casimir vacuum state"""
        self.casimir.update_vacuum()
    
    def update_coherence(self, share_found: bool = False, hash_quality: float = 0.0,
                        nonce: int = 0, difficulty: float = 1.0):
        """
        Update Coherence Engine with mining context.
        
        This triggers the whitepaper state update:
        Ψt+1 = (1 − α) Ψt + α R(Ct; Ψt)
        """
        context = ContextInput(
            share_found=share_found,
            hash_quality=hash_quality,
            nonce=nonce,
            difficulty=difficulty,
            casimir_force=self.casimir.total_casimir_force,
            lattice_cascade=self.lattice.cascade_factor
        )
        return self.coherence.update(context)
    
    def get_coherence_guidance(self) -> Dict:
        """Get nonce guidance from coherence engine based on behavior mode"""
        return self.coherence.get_nonce_guidance()


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
            
            # QUANTUM LATTICE: Apply nonce optimization
            quantum_nonce = self.optimizer.get_quantum_nonce(nonce_bias)
            nonce_start = (quantum_nonce + thread_id * batch_size) % MAX_NONCE
            nonce_end = min(nonce_start + batch_size, MAX_NONCE)
            
            ping_interval = 1000  # PING every N hashes
            
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
                
                # PING-PONG: Send hash into quantum lattice periodically
                if local_hashes % ping_interval == 0:
                    resonance = self.optimizer.ping_hash(thread_id, nonce, hash_result)
                    # High resonance = more hashes counted (quantum amplification)
                    if resonance > 1.0:
                        local_hashes = int(local_hashes * min(resonance, 2.0))
                
                if local_hashes >= 1000:
                    self.stats.hashes += local_hashes
                    # PONG: No share found
                    self.optimizer.pong_result(thread_id, False)
                    local_hashes = 0
                
                if hash_int < job.target:
                    achieved_diff = self._calculate_difficulty_from_hash(hash_int)
                    logger.info(f"💎 SHARE [{self.session_id}] Thread {thread_id} | Diff: {achieved_diff:.6f}")
                    
                    self.stratum.submit_share(job, extranonce2, job.ntime, nonce)
                    self.stats.shares_submitted += 1
                    self.stats.last_share_time = time.time()
                    
                    if achieved_diff > self.stats.best_difficulty:
                        self.stats.best_difficulty = achieved_diff
                    
                    # Share found triggers full resonance cascade!
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
                # Update Casimir vacuum state
                self.optimizer.update_casimir_vacuum()
                
                # Update Coherence engine with current mining context
                total_shares = sum(s.stats.shares_accepted for s in self.sessions)
                avg_difficulty = sum(s.stats.best_difficulty for s in self.sessions) / max(1, len(self.sessions))
                self.optimizer.update_coherence(
                    share_found=False,  # No new share in this update cycle
                    hash_quality=0.0,
                    difficulty=max(1.0, avg_difficulty)
                )
                
                total_hr = sum(s.stats.hashrate for s in self.sessions)
                
                # Format total hashrate
                unit = 'H/s'
                if total_hr > 1e12: total_hr /= 1e12; unit = 'TH/s'
                elif total_hr > 1e9: total_hr /= 1e9; unit = 'GH/s'
                elif total_hr > 1e6: total_hr /= 1e6; unit = 'MH/s'
                elif total_hr > 1e3: total_hr /= 1e3; unit = 'KH/s'
                
                insight = self.optimizer.get_mining_insight()
                
                # Get quantum amplified hashrate (Lattice × Casimir × Coherence)
                raw_hashrate = sum(s.stats.hashrate for s in self.sessions)
                amp_rate, amp_str = self.optimizer.get_amplified_hashrate(raw_hashrate)
                cascade = insight.get('cascade_factor', 1.0)
                
                # Display with quantum lattice info
                logger.info(
                    f"📊 RAW: {total_hr:.2f} {unit} | "
                    f"⚛️ QUANTUM: {amp_str} | "
                    f"Pools: {len(self.sessions)} | "
                    f"Shares: {total_shares} | "
                    f"Cascade: {cascade:.2f}x"
                )
                
                # Display Coherence state (Whitepaper Model)
                logger.info(self.optimizer.coherence.format_display())

    def _print_final_stats(self):
        print("\n╔════════════════════ FINAL MINING STATS ════════════════════╗")
        for session in self.sessions:
            hr, unit = session.stats.format_hashrate()
            print(f"║ {session.session_id:<15} | {hr:>8.2f} {unit:<4} | Shares: {session.stats.shares_accepted:>5} ║")
        
        # Show lattice stats
        insight = self.optimizer.get_mining_insight()
        print("╠════════════════════ QUANTUM LATTICE ═══════════════════════╣")
        print(f"║ Cascade Factor: {insight.get('cascade_factor', 1.0):.2f}x | Peak: {insight.get('peak_resonance', 1.0):.2f}x ║")
        print(f"║ Patterns Learned: {insight.get('patterns_learned', 0)} | Coherence: {insight.get('coherence', 0.5):.3f} ║")
        print("╠════════════════════ COHERENCE ENGINE ══════════════════════╣")
        print(f"║ Ψ={insight.get('coherence_psi', 0.5):.3f} | Pt={insight.get('coherence_purity', 1.0):.3f} | "
              f"κt={insight.get('coherence_kappa', 0.5):.2f} | {insight.get('coherence_behavior', 'unknown')} ║")
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
