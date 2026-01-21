// High-resolution clock with epoch alignment
// Provides both epochMillis (float) and epochMicros (bigint-like number)
export type HighResStamp = {
  epochMillis: number;   // e.g., 1725086400.123456e3 style (ms with sub-ms)
  epochMicros: number;   // integer microseconds (may exceed safe int over centuries; fine here)
  monoSeconds: number;   // monotonic seconds from timeOrigin
};

const origin = performance.timeOrigin;        // ms since UNIX epoch when the page's clock started

export function stampNow(): HighResStamp {
  // performance.now(): monotonic, fractional milliseconds
  const nowMs = performance.now();            // e.g., 12345.678901 (ms)
  const epochMs = origin + nowMs;             // ms since UNIX epoch
  const epochMicros = Math.floor(epochMs * 1000); // integer microseconds
  return {
    epochMillis: epochMs,
    epochMicros,
    monoSeconds: nowMs / 1000
  };
}

// Optional: audio-clock stamp for DSP sync
export function audioStamp(ctx: AudioContext): HighResStamp {
  const audioSec = ctx.currentTime;
  const nowMs = performance.now();
  const epochMs = origin + nowMs;
  return {
    epochMillis: epochMs,
    epochMicros: Math.floor(epochMs * 1000),
    monoSeconds: audioSec
  };
}