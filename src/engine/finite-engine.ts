import type { 
  Candidate, AngelSlot, TarotSpreadItem, Aura, MergedNexus, 
  TemporalSynthesis, EngineOutput, Insights, Milestone 
} from './types';

const PEACE_LEX = ['peace', 'calm', 'harmony', 'balance', 'gentle', 'serene', 'tranquil'];
const JOY_LEX = ['joy', 'abundance', 'success', 'celebration', 'prosperity', 'fulfillment'];

function containsAny(text: string, words: string[]): boolean {
  return words.some(w => text.includes(w));
}

export function generateTLID(name: string, dob: string, date: string): string {
  const input = `${name}+${dob}+${date}+Nexus:10-9-1+Peace+Joy`;
  const hash = btoa(input).slice(0, 16).toUpperCase();
  const initials = name.split(' ').map(n => n[0]).join('');
  return `NX-${date.replace(/-/g, '')}-${initials}-${hash.slice(0,4)}-${hash.slice(4,8)}-${hash.slice(8,12)}-${hash.slice(12,16)}`;
}

export function enumerateOutcomes(angelSlots: AngelSlot[], tarot: TarotSpreadItem[], nexus: MergedNexus[]): Candidate[] {
  const out: Candidate[] = [];
  
  angelSlots.forEach(slot => {
    const actions = [`Follow ${slot.card.name} guidance`, 'Take aligned action within 48 hours'];
    out.push({
      label: `Angel Path: ${slot.card.name}`,
      actions,
      rationale: slot.card.message || 'Divine guidance pathway',
      features: { alignment: 0, timing: 0, coherence: 0, risk: 0, effort: 0, support: 0 }
    });
  });

  tarot.forEach(item => {
    const message = item.reversed ? item.card.reversed : item.card.upright;
    const actions = [`Apply ${item.card.name} energy`, 'Integrate this wisdom today'];
    out.push({
      label: `Tarot Path: ${item.card.name}`,
      actions,
      rationale: message,
      features: { alignment: 0, timing: 0, coherence: 0, risk: 0, effort: 0, support: 0 }
    });
  });

  nexus.forEach(n => {
    out.push({
      label: `Nexus: ${n.field}`,
      actions: [`Focus on ${n.value}`, 'Align with this energy field'],
      rationale: `Nexus support: ${n.support}`,
      features: { alignment: 0, timing: 0, coherence: 0, risk: 0, effort: 0, support: 0 }
    });
  });

  return out.slice(0, 10);
}

export function enforcePeaceAndJoy(candidates: Candidate[]): Candidate[] {
  return candidates.filter(c => {
    const text = (c.label + ' ' + c.actions.join(' ')).toLowerCase();
    return containsAny(text, PEACE_LEX) || containsAny(text, JOY_LEX) || 
           text.includes('harmony') || text.includes('balance') || text.includes('joy');
  });
}

export function scoreCandidate(c: Candidate, aura: Aura, timing: any, consensusScore: number, tarotReversals: number, signalsSupport: number): Candidate {
  const text = (c.label + ' ' + c.actions.join(' ')).toLowerCase();
  const auraHit = aura.traits.some(t => text.includes(t.toLowerCase()));
  const alignment = auraHit ? 0.9 : 0.6;
  
  const timingScore = 0.7;
  const coherence = Math.min(1, 0.55 + 0.1 * consensusScore);
  const risk = Math.max(0, 1 - 0.1 * tarotReversals);
  const effort = Math.max(0.5, 1 - 0.05 * (c.actions.length - 2));
  
  const resonance = (containsAny(text, PEACE_LEX) ? 0.08 : 0) + (containsAny(text, JOY_LEX) ? 0.08 : 0);
  const support = Math.min(1, 0.6 + 0.05 * signalsSupport + resonance);
  
  c.features = { alignment, timing: timingScore, coherence, risk, effort, support };
  
  const weights = [0.28, 0.22, 0.18, 0.14, 0.08, 0.10];
  const scores = [alignment, timingScore, coherence, risk, effort, support];
  c.score = scores.reduce((sum, score, i) => sum + (weights[i] || 0) * score, 0);
  
  return c;
}

function softmax(scores: number[]): number[] {
  const max = Math.max(...scores);
  const exps = scores.map(s => Math.exp(s - max));
  const sum = exps.reduce((a, b) => a + b, 0);
  return exps.map(e => e / sum);
}

export function temporalSynthesis(
  angelSlots: AngelSlot[], 
  tarot: TarotSpreadItem[], 
  aura: Aura, 
  timing: any, 
  consensusScore: number, 
  mergedNexus: MergedNexus[], 
  observerIntent?: string
): TemporalSynthesis {
  const tarotReversals = tarot.filter(t => t.reversed).length;
  const signalsSupport = mergedNexus.reduce((acc, n) => acc + (n.support || 0), 0);

  let allCandidates = enumerateOutcomes(angelSlots, tarot, mergedNexus);
  
  let candidates = enforcePeaceAndJoy(allCandidates);
  if (!candidates.length) {
    candidates = [{
      label: 'Restore Harmony & Invite Joy',
      actions: ['Resolve one tension kindly', 'Create a small joy moment'],
      window: { tag: 'near' },
      rationale: 'Synthesized directive anchors calm, constructive path',
      features: { alignment: 0.8, timing: 0.7, coherence: 0.9, risk: 0.2, effort: 0.6, support: 0.9 }
    }];
  }

  candidates = candidates.map(c => scoreCandidate(c, aura, timing, consensusScore, tarotReversals, signalsSupport));

  const intentBoost = 0.1;
  candidates.forEach(c => {
    const intentMatch = observerIntent && c.label.toLowerCase().includes(observerIntent.toLowerCase()) ? 1 : 0;
    c.score = (c.score || 0) * (1 + intentBoost * intentMatch);
  });

  const scores = candidates.map(c => c.score || 0);
  const probabilities = softmax(scores);
  
  candidates.forEach((c, i) => {
    c.confidence = probabilities[i];
  });

  const bestIndex = probabilities.indexOf(Math.max(...probabilities));
  const best = candidates[bestIndex];
  const alternates = candidates.filter((_, i) => i !== bestIndex).slice(0, 2);

  const directive = `Prime Timeline: ${best.label} - ${best.actions[0]}`;

  const diagnostics = candidates.map(c => ({
    label: c.label,
    confidence: c.confidence || 0,
    features: c.features
  }));

  return { best, alternates, directive, diagnostics };
}

export function runFiniteEngine(
  name: string,
  dob: string,
  intent: string,
  angelSlots: AngelSlot[],
  tarot: TarotSpreadItem[],
  aura: Aura,
  mergedNexus: MergedNexus[]
): EngineOutput {
  const today = new Date().toISOString().split('T')[0];
  const tlid = generateTLID(name, dob, today);
  
  const timing = { A: { window: 'near' }, B: { window: 'later' } };
  const consensusScore = 0.8;
  
  const tms = temporalSynthesis(angelSlots, tarot, aura, timing, consensusScore, mergedNexus, intent);
  
  const insights: Insights = {
    consensus_score: consensusScore,
    tensions: ['Balance work and rest', 'Align action with values'],
    opportunities: ['New creative projects', 'Relationship harmony'],
    risks: ['Overcommitment', 'Neglecting self-care'],
    affirmation: 'I move forward with clarity and peace',
    journal_prompts: ['What brings me joy today?', 'How can I create more harmony?'],
    micro_advice: angelSlots.slice(0, 3).map(slot => ({
      slot: slot.slot,
      card: slot.card.name,
      tip: 'Trust your intuition'
    }))
  };

  const milestones: Milestone[] = [
    { label: 'Immediate Action', start: today, suggestion: tms.best.actions[0] },
    { label: 'Weekly Review', suggestion: 'Assess progress and adjust course' }
  ];

  return {
    tlid,
    aura,
    angel: { spread: angelSlots, timing, merged_nexus: mergedNexus },
    tarot: { spread: tarot },
    synthesis: tms.directive,
    plan: {
      day1: [tms.best.actions[0] || 'Focus on alignment'],
      day2: [tms.best.actions[1] || 'Take inspired action'],
      day3: ['Review and integrate insights']
    },
    insights,
    milestones,
    tms,
    nexus_source_law: '10-9-1: Ten outcomes, nine harmonic filters, one prime directive',
    constraints: { peace_and_joy: true }
  };
}