import type { AurisClassification } from './aurisSandbox';

const ENV = {
  AURIS_URL: import.meta.env.VITE_AURIS_SANDBOX_URL as string | undefined,
  AURIS_KEY: import.meta.env.VITE_AURIS_SANDBOX_KEY as string | undefined,
};

/**
 * Mode A: Custom Auris webhook
 * POST { texts: string[] }
 * headers: { Authorization: `Bearer ${VITE_AURIS_SANDBOX_KEY}` }
 * response: { items: AurisClassification[] }
 */
export async function classifyViaWebhook(texts: string[], opts?: Partial<RequestInit>): Promise<AurisClassification[]> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 15_000);
  try {
    const r = await fetch(ENV.AURIS_URL as string, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        Authorization: `Bearer ${ENV.AURIS_KEY}`,
      },
      body: JSON.stringify({ texts }),
      signal: controller.signal,
      ...opts,
    });
    if (!r.ok) throw new Error(`Auris webhook ${r.status}`);
    const data = await r.json();
    const items = Array.isArray(data?.items) ? data.items : [];
    return normalizeArray(items, texts.length);
  } finally {
    clearTimeout(id);
  }
}

function normalizeArray(items: unknown[], expected: number): AurisClassification[] {
  const out: AurisClassification[] = [];
  for (let i = 0; i < expected; i++) {
    const raw = items?.[i] as any;
    const v = clamp01(toNumber(raw?.valence, 0.5));
    const a = clamp01(toNumber(raw?.arousal, 0.5));
    const emotion = (raw?.emotion ?? "neutral").toString();
    const tags = Array.isArray(raw?.tags) ? raw.tags.map((t: any) => String(t)).slice(0, 4) : [];
    out.push({ valence: v, arousal: a, emotion, tags, raw });
  }
  return out;
}

function toNumber(x: unknown, fb = 0): number {
  const n = typeof x === "number" ? x : typeof x === "string" ? Number(x) : NaN;
  return Number.isFinite(n) ? n : fb;
}

function clamp01(n: number): number { 
  return Math.max(0, Math.min(1, n)); 
}