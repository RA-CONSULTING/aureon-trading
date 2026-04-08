#!/usr/bin/env python3
"""
Minimal Kimi/Aureon voice adapter for local microphone transcription.

This is intentionally small and focused: it provides a stable local
recognition interface for the conversation loop while keeping the
existing Aureon routing and safety controls in place.
"""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from typing import Optional

try:
    import speech_recognition as sr  # type: ignore
except Exception:
    sr = None  # type: ignore


HAS_SPEECH_RECOGNITION = sr is not None
HAS_POCKETSPHINX = importlib.util.find_spec("pocketsphinx") is not None


@dataclass
class KimiRecognitionResult:
    ok: bool
    text: str = ""
    backend: str = "unavailable"
    reason: str = ""


class KimiVoiceAdapter:
    """Local-first speech recognizer used by the Aureon conversation loop."""

    def __init__(self, backend: str = "auto") -> None:
        self.backend = (backend or "auto").strip().lower()
        self.last_backend = "unavailable"
        self.dynamic_energy_threshold = _read_bool("AUREON_DYNAMIC_ENERGY", True)
        self.energy_threshold = _read_int("AUREON_ENERGY_THRESHOLD", 300)
        self.pause_threshold = _read_float("AUREON_PAUSE_THRESHOLD", 0.8)
        self.non_speaking_duration = _read_float("AUREON_NON_SPEAKING_DURATION", 0.5)
        self.phrase_threshold = _read_float("AUREON_PHRASE_THRESHOLD", 0.3)
        self.operation_timeout = _read_float("AUREON_OPERATION_TIMEOUT", 8.0)
        self.adjust_duration = _read_float("AUREON_ADJUST_DURATION", 1.0)
        self.google_retries = max(1, _read_int("AUREON_GOOGLE_RETRIES", 2))
        self.capture_retries = max(1, _read_int("AUREON_CAPTURE_RETRIES", 2))
        self.microphone_index = _read_optional_int("AUREON_MIC_DEVICE_INDEX")

    def recognize_microphone(
        self,
        timeout: float = 5.0,
        phrase_time_limit: float = 8.0,
        adjust_duration: float = 0.5,
    ) -> KimiRecognitionResult:
        if not HAS_SPEECH_RECOGNITION or sr is None:
            self.last_backend = "unavailable"
            return KimiRecognitionResult(ok=False, backend=self.last_backend, reason="speech_recognition_unavailable")

        last_error = "recognition_failed"
        for _ in range(self.capture_retries):
            recognizer = sr.Recognizer()
            self._configure_recognizer(recognizer)
            try:
                with sr.Microphone(device_index=self.microphone_index) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=max(adjust_duration, self.adjust_duration))
                    audio = recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit,
                    )
                return self.recognize_audio(recognizer, audio)
            except Exception as exc:
                last_error = str(exc)
        self.last_backend = self._backend_order()[-1] if self._backend_order() else "unavailable"
        return KimiRecognitionResult(ok=False, backend=self.last_backend, reason=last_error)

    def recognize_audio(self, recognizer: "sr.Recognizer", audio: "sr.AudioData") -> KimiRecognitionResult:
        backends = self._backend_order()
        last_error = "recognition_failed"
        for backend in backends:
            try:
                if backend == "sphinx":
                    text = recognizer.recognize_sphinx(audio)
                elif backend == "google":
                    text = self._recognize_google_with_retries(recognizer, audio)
                else:
                    continue
                text = (text or "").strip()
                if text:
                    self.last_backend = backend
                    return KimiRecognitionResult(ok=True, text=text, backend=backend)
            except Exception as exc:
                last_error = str(exc)
                continue
        self.last_backend = backends[-1] if backends else "unavailable"
        return KimiRecognitionResult(ok=False, backend=self.last_backend, reason=last_error)

    def status(self) -> dict:
        return {
            "speech_recognition_available": HAS_SPEECH_RECOGNITION,
            "pocketsphinx_available": HAS_POCKETSPHINX,
            "configured_backend": self.backend,
            "last_backend": self.last_backend,
            "microphone_index": self.microphone_index,
            "dynamic_energy_threshold": self.dynamic_energy_threshold,
            "energy_threshold": self.energy_threshold,
            "pause_threshold": self.pause_threshold,
            "non_speaking_duration": self.non_speaking_duration,
            "phrase_threshold": self.phrase_threshold,
            "adjust_duration": self.adjust_duration,
            "google_retries": self.google_retries,
            "capture_retries": self.capture_retries,
        }

    def _backend_order(self) -> list[str]:
        if self.backend == "sphinx":
            return ["sphinx"] if HAS_POCKETSPHINX else []
        if self.backend == "google":
            return ["google"]
        if self.backend == "google_first":
            order = ["google"]
            if HAS_POCKETSPHINX:
                order.append("sphinx")
            return order
        order: list[str] = []
        if HAS_POCKETSPHINX:
            order.append("sphinx")
        order.append("google")
        return order

    def _configure_recognizer(self, recognizer: "sr.Recognizer") -> None:
        recognizer.dynamic_energy_threshold = self.dynamic_energy_threshold
        recognizer.energy_threshold = self.energy_threshold
        recognizer.pause_threshold = self.pause_threshold
        recognizer.non_speaking_duration = self.non_speaking_duration
        recognizer.phrase_threshold = self.phrase_threshold
        recognizer.operation_timeout = self.operation_timeout

    def _recognize_google_with_retries(self, recognizer: "sr.Recognizer", audio: "sr.AudioData") -> str:
        last_error = "google_recognition_failed"
        for _ in range(self.google_retries):
            try:
                return recognizer.recognize_google(audio)
            except Exception as exc:
                last_error = str(exc)
        raise RuntimeError(last_error)


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except Exception:
        return default


def _read_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value.strip())
    except Exception:
        return default


def _read_optional_int(name: str) -> Optional[int]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    try:
        return int(value.strip())
    except Exception:
        return None
