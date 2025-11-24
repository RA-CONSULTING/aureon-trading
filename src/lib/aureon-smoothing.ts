/**
io-smoothing (Aureon v1.0)

Temporal smoothing + hysteresis for stable emotion states.
Designed to plug into io-resonance-engine without tight coupling.
*/

export type NoteID = | "C" | "Cs" | "D" | "Ds" | "E" | "F" | "Fs" | "G" | "Gs" | "A" | "As" | "B" | "C5";

export interface BlendWeight { note: NoteID; w: number }

export interface EmotionState {
  fIn: number;
  fNorm: number;
  primary: NoteID;
  weights: BlendWeight[];
  valence: number;
  arousal: number;
  color: string;
  confidence: number;
  tags: string[];
}

export interface SmoothingOptions {
  tauMs?: number;
  minHoldMs?: number;
  hysteresisHz?: number;
  timeSource?: () => number;
}

function clamp(x:number, lo=0, hi=1){ return Math.max(lo, Math.min(hi, x)); }

function hexToRgb(hex: string): {r:number,g:number,b:number} {
  const m = /^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})$/i.exec(hex) as RegExpExecArray;
  return { r: parseInt(m[1],16), g: parseInt(m[2],16), b: parseInt(m[3],16) };
}

function rgbToHex(r:number,g:number,b:number): string {
  const h = (n:number)=> n.toString(16).padStart(2,'0');
  return `#${h(r)}${h(g)}${h(b)}`.toUpperCase();
}

function toHSV({r,g,b}:{r:number,g:number,b:number}){
  const R=r/255,G=g/255,B=b/255;
  const max=Math.max(R,G,B), min=Math.min(R,G,B);
  const d=max-min;
  let h=0;
  if(d!==0){
    if(max===R){ h=((G-B)/d)%6; }
    else if(max===G){ h=(B-R)/d+2; }
    else { h=(R-G)/d+4; }
    h*=60;
    if(h<0) h+=360;
  }
  const s = max===0 ? 0 : d/max;
  const v = max;
  return {h,s,v};
}

function fromHSV({h,s,v}:{h:number,s:number,v:number}){
  const c=v*s;
  const x=c*(1-Math.abs(((h/60)%2)-1));
  const m=v-c;
  let r=0,g=0,b=0;
  if (0<=h && h<60){ r=c; g=x; b=0; }
  else if (60<=h && h<120){ r=x; g=c; b=0; }
  else if (120<=h && h<180){ r=0; g=c; b=x; }
  else if (180<=h && h<240){ r=0; g=x; b=c; }
  else if (240<=h && h<300){ r=x; g=0; b=c; }
  else { r=c; g=0; b=x; }
  return {
    r: Math.round((r+m)*255),
    g: Math.round((g+m)*255),
    b: Math.round((b+m)*255)
  };
}

function blendHexHSV(colors: string[], weights: number[]): string {
  const S = weights.reduce((a,b)=>a+b,0) || 1;
  const w = weights.map(x=> x/S);
  const hsv = colors.map(c=> toHSV(hexToRgb(c)));
  
  let refIdx = 0;
  for(let i=1;i<w.length;i++){
    if(w[i]>w[refIdx]) refIdx=i;
  }
  
  const hRef = hsv[refIdx].h;
  const hueDiff = (h:number)=>{
    let d=h-hRef;
    while(d>180) d-=360;
    while(d<-180) d+=360;
    return d;
  };
  
  let h=0,s=0,v=0;
  for(let i=0;i<hsv.length;i++){
    const d=hueDiff(hsv[i].h);
    h += (hRef+d)*w[i];
    s += hsv[i].s*w[i];
    v += hsv[i].v*w[i];
  }
  h=((h%360)+360)%360;
  
  const {r,g,b}=fromHSV({h,s,v});
  return rgbToHex(r,g,b);
}

export class EmotionSmoother {
  private readonly tauMs: number;
  private readonly minHoldMs: number;
  private readonly hysteresisHz: number;
  private readonly now: () => number;
  private readonly getHz: (id: NoteID) => number;

  private last: EmotionState | null = null;
  private lastTs: number | null = null;

  constructor(getNoteHz: (id: NoteID) => number, opts: SmoothingOptions = {}){
    this.getHz = getNoteHz;
    this.tauMs = opts.tauMs ?? 2000;
    this.minHoldMs = opts.minHoldMs ?? 1000;
    this.hysteresisHz = opts.hysteresisHz ?? 3;
    this.now = opts.timeSource ?? (()=> Date.now());
  }

  private alpha(dtMs: number){
    const a = 1 - Math.exp(-Math.max(0,dtMs)/Math.max(1,this.tauMs));
    return clamp(a, 0, 1);
  }

  update(input: EmotionState, timestampMs?: number): EmotionState {
    const t = timestampMs ?? this.now();
    if (!this.last){
      this.last = input;
      this.lastTs = t;
      return input;
    }

    const dt = t - (this.lastTs ?? t);
    let primary = this.last.primary;

    const oldHz = this.getHz(this.last.primary);
    const newHz = this.getHz(input.primary);
    const dPrev = Math.abs(input.fNorm - oldHz);
    const dNew = Math.abs(input.fNorm - newHz);

    const hold = dt < this.minHoldMs;
    const switchAllowed = !hold && (dNew + this.hysteresisHz < dPrev);
    if (switchAllowed) primary = input.primary;

    const a = this.alpha(dt);
    const valence = (1-a)*(this.last.valence) + a*(input.valence);
    const arousal = (1-a)*(this.last.arousal) + a*(input.arousal);
    const confidence = (1-a)*(this.last.confidence) + a*(input.confidence);

    const color = blendHexHSV([this.last.color, input.color], [1-a, a]);

    const out: EmotionState = {
      ...input,
      primary,
      valence,
      arousal,
      confidence,
      color,
    };

    this.last = out;
    this.lastTs = t;
    return out;
  }
}

export default { EmotionSmoother };