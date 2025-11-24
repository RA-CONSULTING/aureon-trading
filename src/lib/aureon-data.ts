import { NoteDef } from './aureon';

// ---------- Dictionary (C=256 Pythagorean)
export const NOTES: NoteDef[] = [
  { id:"C",  display:"C",   hz:256.000, color:"#FF0000", valence:0.60, arousal:0.25, tags:["Safety","Belonging","Grounding","Homeostasis","Presence","Roots"] },
  { id:"Cs", display:"C♯/D♭", hz:273.375, color:"#FF5500", valence:0.55, arousal:0.33, tags:["Curiosity","Initiation","Threshold","Change","Instigation"] },
  { id:"D",  display:"D",   hz:288.000, color:"#FFA500", valence:0.50, arousal:0.45, tags:["Hope","Yearning","Aspiration","Drive","Desire"] },
  { id:"Ds", display:"D♯/E♭", hz:307.547, color:"#FFCC00", valence:0.60, arousal:0.48, tags:["Wonder","Anticipation","Spark","Edge-of-Discovery","Suspense"] },
  { id:"E",  display:"E",   hz:324.000, color:"#FFFF00", valence:0.80, arousal:0.55, tags:["Joy","Possibility","Optimism","Celebration","Warmth"] },
  { id:"F",  display:"F",   hz:341.333, color:"#00FF00", valence:0.70, arousal:0.35, tags:["Heart","Healing","Compassion","Nurture","Integration"] },
  { id:"Fs", display:"F♯/G♭", hz:364.500, color:"#00CCAA", valence:0.65, arousal:0.50, tags:["Courage","Alignment","Choice","Integrity","Resolve"] },
  { id:"G",  display:"G",   hz:384.000, color:"#0000FF", valence:0.60, arousal:0.50, tags:["Confidence","Trust","Stability-in-Motion","Empowerment","Faith"] },
  { id:"Gs", display:"G♯/A♭", hz:410.063, color:"#3344FF", valence:0.70, arousal:0.52, tags:["Flow","Creativity","Play","Improvisation","Imagination"] },
  { id:"A",  display:"A",   hz:432.000, color:"#4B0082", valence:0.90, arousal:0.60, tags:["Inspiration","Transcendence","Higher Vision","Breath","Liberation"] },
  { id:"As", display:"A♯/B♭", hz:461.320, color:"#7F00FF", valence:0.85, arousal:0.46, tags:["Reverence","Insight","Intuition","Devotion","Sacred Awe"] },
  { id:"B",  display:"B",   hz:486.000, color:"#8A2BE2", valence:0.85, arousal:0.40, tags:["Awakening","Unity","Wholeness","Recognition","Synthesis"] },
  { id:"C5", display:"C′",  hz:512.000, color:"#FFFFFF", valence:0.95, arousal:0.30, tags:["Fulfillment","Completion","Return","Peace","Closure"] }
];

// Colors for blending accidentals are already set as intermediate hues.