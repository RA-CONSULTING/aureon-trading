import { Badge } from '@/components/ui/badge';
import type { Mood } from '@/lib/mood';

const EMOJI: Record<Mood,string> = { 
  Happy:'😊', 
  Calm:'🫶', 
  Stressed:'😰', 
  Sad:'😔', 
  Neutral:'😐' 
};

export default function EmotionBadge({ mood }: { mood: Mood }) {
  return (
    <Badge variant="outline" className="text-xs">
      <span className="mr-1">{EMOJI[mood]}</span>
      {mood}
    </Badge>
  );
}