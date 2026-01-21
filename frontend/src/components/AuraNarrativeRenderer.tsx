import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { AuraReading } from '@/lib/aura-engine';

interface Props {
  reading: AuraReading;
  voice: 'mythic' | 'plain';
  name: string;
  dob: string;
}

export const AuraNarrativeRenderer: React.FC<Props> = ({ reading, voice, name, dob }) => {
  const formatPercent = (val: number) => Math.round(val * 100);
  
  if (voice === 'mythic') {
    return (
      <div className="space-y-6">
        <Card className="bg-gradient-to-br from-purple-900/30 to-indigo-900/30 border-purple-500/30">
          <CardHeader>
            <CardTitle className="text-2xl text-center text-purple-200">
              The Reading of {name} — In Tandem with Source
            </CardTitle>
          </CardHeader>
        </Card>

        <Card className="bg-slate-800/50 border-amber-500/30">
          <CardHeader>
            <CardTitle className="text-amber-400">Pillar I — All That Was (Origins)</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-200 leading-relaxed">
              From before the veils of time, you came bearing the archetype of <strong>{reading.state_profile.archetype.primary}</strong> (with the gift of <strong>{reading.state_profile.archetype.secondary}</strong>). Your strengths—{reading.state_profile.strengths.join(', ')}—have traveled with you. Your lessons—{reading.state_profile.challenges.join(', ')}—call you to refine what you once began.
            </p>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-emerald-500/30">
          <CardHeader>
            <CardTitle className="text-emerald-400">Pillar II — All That Is (Present Crossroads)</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-200 leading-relaxed mb-4">
              You stand where paths part: <strong>{reading.state_profile.crossroad.theme.replace('_', ' vs ')}</strong>. Your heart shows {formatPercent(reading.chakra.heart)}% vitality; your voice {formatPercent(reading.chakra.throat)}% truth; your vision {formatPercent(reading.chakra.third_eye)}% sight. The aura sings green ({formatPercent(reading.color.green)}% love) and blue ({formatPercent(reading.color.blue)}% peace)—a sign to speak gently and lead with care.
            </p>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="bg-purple-500/20 text-purple-400">
                {reading.cosmic.note}
              </Badge>
              <Badge variant="outline" className="bg-blue-500/20 text-blue-400">
                {reading.earth.note}
              </Badge>
              <Badge variant="outline" className="bg-green-500/20 text-green-400">
                Coherence: {formatPercent(reading.chakra.coherence)}%
              </Badge>
              <Badge variant="outline" className="bg-amber-500/20 text-amber-400">
                Confidence: {formatPercent(reading.state_profile.confidence)}%
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-cyan-500/30">
          <CardHeader>
            <CardTitle className="text-cyan-400">Pillar III — All That Shall Be (Future Paths)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-green-900/30 p-4 rounded-lg border border-green-500/30">
                <h4 className="font-bold text-green-400 mb-2">Aligned Path (Awakening — {formatPercent(reading.timelines.aligned.likelihood)}%)</h4>
                <p className="text-sm text-gray-300">Outcomes: {reading.timelines.aligned.outcomes.join(', ')}</p>
                <p className="text-sm text-gray-400 mt-2">Drivers: {reading.timelines.aligned.drivers.join(', ')}</p>
              </div>
              <div className="bg-yellow-900/30 p-4 rounded-lg border border-yellow-500/30">
                <h4 className="font-bold text-yellow-400 mb-2">Middle Path (Patience — {formatPercent(reading.timelines.middle.likelihood)}%)</h4>
                <p className="text-sm text-gray-300">Outcomes: {reading.timelines.middle.outcomes.join(', ')}</p>
                <p className="text-sm text-gray-400 mt-2">Drivers: {reading.timelines.middle.drivers.join(', ')}</p>
              </div>
              <div className="bg-red-900/30 p-4 rounded-lg border border-red-500/30">
                <h4 className="font-bold text-red-400 mb-2">Resistant Path (Stagnation — {formatPercent(reading.timelines.resistant.likelihood)}%)</h4>
                <p className="text-sm text-gray-300">Outcomes: {reading.timelines.resistant.outcomes.join(', ')}</p>
                <p className="text-sm text-gray-400 mt-2">Drivers: {reading.timelines.resistant.drivers.join(', ')}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-violet-500/30">
          <CardHeader>
            <CardTitle className="text-violet-400">Pillar IV — All That Moves in Unity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-200 leading-relaxed">
              The threads converge. Your {reading.state_profile.archetype.primary} nature calls you to serve through {reading.state_profile.archetype.secondary} wisdom. Trust the process, for you are exactly where you need to be in this cosmic dance of becoming.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Plain voice
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Personal Reading for {name}</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Based on your birth date ({dob}) and current cosmic conditions, here's your personalized guidance.</p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Your Core Nature</CardTitle>
          </CardHeader>
          <CardContent>
            <p>You are primarily a <strong>{reading.state_profile.archetype.primary}</strong> with <strong>{reading.state_profile.archetype.secondary}</strong> qualities. Your main strengths include {reading.state_profile.strengths.join(', ')}.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Current Situation</CardTitle>
          </CardHeader>
          <CardContent>
            <p>You're navigating {reading.state_profile.crossroad.theme.replace('_', ' vs ')}. Your energy centers are well-balanced, with your heart at {formatPercent(reading.chakra.heart)}% and overall coherence at {formatPercent(reading.chakra.coherence)}%.</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recommended Practices</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>Meditation: {formatPercent(reading.practices.meditation)}% beneficial</div>
            <div>Grounding: {formatPercent(reading.practices.grounding)}% beneficial</div>
            <div>Service: {formatPercent(reading.practices.service)}% beneficial</div>
            <div>Movement: {formatPercent(reading.practices.movement)}% beneficial</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AuraNarrativeRenderer;