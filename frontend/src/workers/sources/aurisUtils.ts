import type { AurisClassification } from './aurisSandbox';

const DEFAULT: AurisClassification = {
  valence: 0.5,
  arousal: 0.5,
  emotion: "neutral",
  tags: [],
};

const ENV = {
  OPENAI_KEY: import.meta.env.VITE_OPENAI_API_KEY as string | undefined,
  AURIS_MODEL: (import.meta.env.VITE_AURIS_MODEL as string | undefined) || "gpt-4o-mini",
};

/**
 * Mode B: OpenAI JSON fallback
 */
export async function classifyViaOpenAI(texts: string[], opts?: Partial<RequestInit>): Promise<AurisClassification[]> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 25_000);
  try {
    const prompt = buildJsonPrompt(texts);
    const r = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        Authorization: `Bearer ${ENV.OPENAI_KEY}`,
      },
      body: JSON.stringify({
        model: ENV.AURIS_MODEL,
        temperature: 0,
        response_format: { type: "json_object" },
        messages: [
          {
            role: "system",
            content: "You are Auris, an analyst. For each input text, return valence (0..1), arousal (0..1), primary emotion, and up to 4 context tags. Keep JSON concise.",
          },
          { role: "user", content: prompt },
        ],
      }),
      signal: controller.signal,
      ...opts,
    });
    if (!r.ok) throw new Error(`OpenAI ${r.status}`);
    const json = await r.json();
    const content = json?.choices?.[0]?.message?.content ?? "{}";
    const parsed = safeParseJSON(content, { items: [] as unknown[] });
    return normalizeArray(parsed.items, texts.length);
  } finally {
    clearTimeout(id);
  }
}

export function normalizeArray(items: unknown[], expected: number): AurisClassification[] {
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

function buildJsonPrompt(texts: string[]): string {
  return JSON.stringify(
    {
      instruction: "Classify each item. Output JSON { items: [{ valence, arousal, emotion, tags }] } in the exact order.",
      schema: {
        items: [
          {
            valence: "number in [0,1]",
            arousal: "number in [0,1]",
            emotion: "string",
            tags: ["string", "... (<=4)"]
          },
        ],
      },
      items: texts,
    },
    null,
    0,
  );
}

function toNumber(x: unknown, fb = 0): number {
  const n = typeof x === "number" ? x : typeof x === "string" ? Number(x) : NaN;
  return Number.isFinite(n) ? n : fb;
}

function clamp01(n: number): number { 
  return Math.max(0, Math.min(1, n)); 
}

function safeParseJSON<T>(s: string, fb: T): T {
  try { return JSON.parse(s) as T; } catch { return fb; }
}