// ---------- Utilities
export function normalizeToWindow(f: number, lo = 256, hi = 512): number {
  if (!isFinite(f) || f <= 0) return NaN;
  while (f < lo) f *= 2;
  while (f >= hi) f /= 2;
  return f;
}

export function logistic(x: number): number {
  return 1 / (1 + Math.exp(-x));
}

export function clamp(x: number, lo = 0, hi = 1): number {
  return Math.max(lo, Math.min(hi, x));
}

function hexToRgb(hex: string): {r:number,g:number,b:number} {
  const m = /^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(hex) as RegExpExecArray;
  return { r: parseInt(m[1],16), g: parseInt(m[2],16), b: parseInt(m[3],16) };
}

function rgbToHex(r:number,g:number,b:number): string {
  const h = (n:number)=> n.toString(16).padStart(2,'0');
  return `#${h(r)}${h(g)}${h(b)}`.toUpperCase();
}

export function blendHex(colors: string[], weights: number[]): string {
  let R=0,G=0,B=0, S=weights.reduce((a,b)=>a+b,0) || 1;
  for (let i=0;i<colors.length;i++) {
    const {r,g,b} = hexToRgb(colors[i]);
    const w = weights[i]/S;
    R += r*w; G += g*w; B += b*w;
  }
  return rgbToHex(Math.round(R),Math.round(G),Math.round(B));
}