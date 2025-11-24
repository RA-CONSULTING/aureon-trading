import type { AurisClassification } from './aurisSandbox';

const ENV = {
  AURIS_URL: import.meta.env.VITE_AURIS_SANDBOX_URL as string | undefined,
  AURIS_KEY: import.meta.env.VITE_AURIS_SANDBOX_KEY as string | undefined,
  OPENAI_KEY: import.meta.env.VITE_OPENAI_API_KEY as string | undefined,
  AURIS_MODEL: (import.meta.env.VITE_AURIS_MODEL as string | undefined) || "gpt-4o-mini",
};

const DEFAULT: AurisClassification = {
  valence: 0.5,
  arousal: 0.5,
  emotion: "neutral",
  tags: [],
};

/**
 * Public API: classify a single text.
 */
export async function classifyWithAuris(text: string, opts?: Partial<RequestInit>): Promise<AurisClassification> {
  const [res] = await classifyBatchWithAuris([text], opts);
  return res;
}

/**
 * Public API: classify multiple texts in one go (more efficient & rate-limit friendly).
 */
export async function classifyBatchWithAuris(texts: string[], opts?: Partial<RequestInit>): Promise<AurisClassification[]> {
  const clean = (texts || []).map(t => (t ?? "").toString().trim());
  if (!clean.length) return [];

  // Prefer custom webhook if present, otherwise use OpenAI fallback.
  if (ENV.AURIS_URL && ENV.AURIS_KEY) {
    try {
      return await classifyViaWebhook(clean, opts);
    } catch (e) {
      console.warn("Auris webhook failed, falling back to OpenAI:", e);
    }
  }
  if (ENV.OPENAI_KEY) {
    return await classifyViaOpenAI(clean, opts);
  }

  // Last resort: return neutral defaults to keep the UI stable.
  return clean.map(() => ({ ...DEFAULT }));
}