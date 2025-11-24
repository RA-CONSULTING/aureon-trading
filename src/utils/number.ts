export function isFiniteNumber(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

export function fmt(
  x: unknown,
  digits = 2,
  fallback: string = "—"
): string {
  if (isFiniteNumber(x)) return (x as number).toFixed(digits);
  const coerced = Number(x);
  return Number.isFinite(coerced) ? coerced.toFixed(digits) : fallback;
}

export function fmtHz(x: unknown, digits = 2) {
  return `${fmt(x, digits)} Hz`;
}

export function fmtPct(x: unknown, digits = 1) {
  const n = Number(x);
  if (!Number.isFinite(n)) return "—";
  const val = Math.abs(n) <= 1 ? n * 100 : n;
  return `${val.toFixed(digits)}%`;
}