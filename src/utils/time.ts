export function nowMicros(): number {
  // performance.timeOrigin + performance.now() gives wall-clock microseconds
  // Convert to integer microseconds for precision display
  return Math.round((performance.timeOrigin + performance.now()) * 1000);
}

export function elapsedMicros(startTime: number): number {
  return nowMicros() - startTime;
}

export function formatMicros(micros: number): string {
  if (micros < 1000) return `${micros}μs`;
  if (micros < 1000000) return `${(micros / 1000).toFixed(1)}ms`;
  return `${(micros / 1000000).toFixed(2)}s`;
}

export function isoTimestamp(): string {
  return new Date().toISOString();
}