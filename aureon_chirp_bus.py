#!/usr/bin/env python3
"""
Aureon Chirp Bus
----------------
Ultra-compact kHz-rate signaling between running components using
8-byte chirp packets and shared-memory ring buffer transport.
"""

from __future__ import annotations

import os
import sys
import time
import zlib
import struct
from dataclasses import dataclass, field
from enum import IntEnum
from multiprocessing import shared_memory
from typing import Optional

# Windows UTF-8 Fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

CHIRP_MAGIC = 0xC1
CHIRP_SIZE = 8
HEADER_SIZE = 16  # write_idx (8) + read_idx (8)

CHIRP_STRUCT = struct.Struct(">BBBBHBB")


class ChirpType(IntEnum):
    PING = 0
    OPPORTUNITY = 1
    EXECUTE = 2
    OUTCOME = 3
    ALERT = 4
    STATUS = 5


class ChirpDirection(IntEnum):
    DOWN = 0
    UP = 1


@dataclass
class ChirpPacket:
    message_type: ChirpType
    direction: ChirpDirection
    coherence: float = 1.0
    confidence: float = 1.0
    symbol_id: int = 0
    frequency: int = 528
    amplitude: int = 128
    timestamp_bucket: int = 0

    def to_bytes(self) -> bytes:
        type_dir = ((int(self.message_type) & 0x0F) << 4) | (int(self.direction) & 0x0F)
        coh = max(0, min(15, int(round(self.coherence * 15))))
        conf = max(0, min(15, int(round(self.confidence * 15))))
        coh_conf = (coh << 4) | conf
        freq = max(0, min(0xFFFF, int(self.frequency)))
        amp = max(0, min(0xFF, int(self.amplitude)))
        tsb = max(0, min(0xFF, int(self.timestamp_bucket)))
        return CHIRP_STRUCT.pack(CHIRP_MAGIC, type_dir, coh_conf, self.symbol_id & 0xFF, freq, amp, tsb)

    @classmethod
    def from_bytes(cls, data: bytes) -> "ChirpPacket":
        if len(data) != CHIRP_SIZE:
            raise ValueError("Invalid chirp size")
        magic, type_dir, coh_conf, symbol_id, freq, amp, tsb = CHIRP_STRUCT.unpack(data)
        if magic != CHIRP_MAGIC:
            raise ValueError("Invalid chirp magic")
        message_type = ChirpType((type_dir >> 4) & 0x0F)
        direction = ChirpDirection(type_dir & 0x0F)
        coherence = ((coh_conf >> 4) & 0x0F) / 15.0
        confidence = (coh_conf & 0x0F) / 15.0
        return cls(
            message_type=message_type,
            direction=direction,
            coherence=coherence,
            confidence=confidence,
            symbol_id=symbol_id,
            frequency=freq,
            amplitude=amp,
            timestamp_bucket=tsb,
        )


@dataclass
class ChirpRingBuffer:
    name: str
    slots: int = 512
    create: bool = False
    shm: Optional[shared_memory.SharedMemory] = field(init=False, default=None)
    buf: Optional[memoryview] = field(init=False, default=None)

    def __post_init__(self) -> None:
        size = HEADER_SIZE + (self.slots * CHIRP_SIZE)
        self.shm = shared_memory.SharedMemory(name=self.name, create=self.create, size=size)
        self.buf = self.shm.buf
        if self.create:
            self.buf[:HEADER_SIZE] = b"\x00" * HEADER_SIZE

    def _read_idx(self) -> int:
        return struct.unpack("Q", self.buf[8:16])[0]

    def _write_idx(self) -> int:
        return struct.unpack("Q", self.buf[0:8])[0]

    def _set_write_idx(self, value: int) -> None:
        struct.pack_into("Q", self.buf, 0, value)

    def _set_read_idx(self, value: int) -> None:
        struct.pack_into("Q", self.buf, 8, value)

    def write(self, chirp_bytes: bytes) -> bool:
        if len(chirp_bytes) != CHIRP_SIZE:
            return False
        write_idx = self._write_idx()
        read_idx = self._read_idx()
        next_write = (write_idx + CHIRP_SIZE) % (self.slots * CHIRP_SIZE)
        if next_write == read_idx:
            return False
        offset = HEADER_SIZE + write_idx
        self.buf[offset:offset + CHIRP_SIZE] = chirp_bytes
        self._set_write_idx(next_write)
        return True

    def read(self) -> Optional[bytes]:
        write_idx = self._write_idx()
        read_idx = self._read_idx()
        if read_idx == write_idx:
            return None
        offset = HEADER_SIZE + read_idx
        chirp_bytes = bytes(self.buf[offset:offset + CHIRP_SIZE])
        next_read = (read_idx + CHIRP_SIZE) % (self.slots * CHIRP_SIZE)
        self._set_read_idx(next_read)
        return chirp_bytes

    def close(self) -> None:
        if self.shm:
            self.shm.close()


try:
    from aureon_harmonic_symbol_table import get_symbol_id
    _SYMBOL_TABLE_AVAILABLE = True
except Exception:
    _SYMBOL_TABLE_AVAILABLE = False
    def get_symbol_id(symbol: str) -> int:
        if not symbol:
            return 0
        return zlib.crc32(symbol.encode("utf-8")) & 0xFF


@dataclass
class ChirpBus:
    name: str = "aureon_chirp_bus"
    create: bool = False
    ring: ChirpRingBuffer = field(init=False)

    def __post_init__(self) -> None:
        self.ring = ChirpRingBuffer(name=self.name, create=self.create)

    def emit(self, packet: ChirpPacket) -> bool:
        return self.ring.write(packet.to_bytes())

    def emit_message(
        self,
        message: str,
        *,
        direction: ChirpDirection = ChirpDirection.DOWN,
        coherence: float = 1.0,
        confidence: float = 1.0,
        symbol: Optional[str] = None,
        frequency: int = 528,
        amplitude: int = 128,
        message_type: Optional[ChirpType] = None,
    ) -> bool:
        packet = ChirpPacket(
            message_type=message_type or classify_message(message),
            direction=direction,
            coherence=coherence,
            confidence=confidence,
            symbol_id=get_symbol_id(symbol) if symbol else 0,
            frequency=frequency,
            amplitude=amplitude,
            timestamp_bucket=_timestamp_bucket(),
        )
        return self.emit(packet)

    def emit_signal(
        self,
        *,
        message: str,
        direction: ChirpDirection,
        coherence: float,
        confidence: float,
        symbol: Optional[str],
        frequency: int,
        amplitude: int = 128,
    ) -> bool:
        return self.emit_message(
            message,
            direction=direction,
            coherence=coherence,
            confidence=confidence,
            symbol=symbol,
            frequency=frequency,
            amplitude=amplitude,
        )


_chirp_bus: Optional[ChirpBus] = None


def get_chirp_bus(create_if_missing: bool = True) -> Optional[ChirpBus]:
    global _chirp_bus
    if _chirp_bus is not None:
        return _chirp_bus
    try:
        _chirp_bus = ChirpBus(create=create_if_missing)
        return _chirp_bus
    except Exception:
        return None


def _timestamp_bucket() -> int:
    return int((time.time_ns() // 1_000_000) % 256)


def classify_message(message: str) -> ChirpType:
    text = (message or "").upper()
    if "EXECUTE" in text or "FIRE" in text:
        return ChirpType.EXECUTE
    if "BUY" in text or "ENTRY" in text:
        return ChirpType.OPPORTUNITY
    if "SELL" in text or "EXIT" in text:
        return ChirpType.ALERT
    if "WIN" in text or "PROFIT" in text:
        return ChirpType.OUTCOME
    if "STATUS" in text or "HEALTH" in text:
        return ChirpType.STATUS
    return ChirpType.PING
