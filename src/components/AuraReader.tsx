import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { generateReading, AuraReading, AuraInput } from '@/lib/aura-engine';
import AuraNarrativeRenderer from './AuraNarrativeRenderer';
import { LongFormNarrativeEngine } from './LongFormNarrativeEngine';

const AuraReader: React.FC = () => {
  const [name, setName] = useState('');
  const [dob, setDob] = useState('');
  const [tob, setTob] = useState('');
  const [reading, setReading] = useState<AuraReading | null>(null);
  const [mode, setMode] = useState<'symbolic' | 'technical' | 'dual' | 'story'>('dual');
  const [voice, setVoice] = useState<'mythic' | 'plain'>('mythic');
  const [isScanning, setIsScanning] = useState(false);

  const sacredImages = [
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718714428_b8ae7650.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718716214_250e492f.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718718036_c6de1f3d.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718720116_57414370.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718722029_c681cdea.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718723358_0714925e.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718724672_cd4edc6a.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718725882_2f84aef2.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718727299_a30c1e40.png",
    "https://d64gsuwffb70l.cloudfront.net/68a07fabd73c7b43a97325cc_1756718728702_8b456d0f.png"
  ];

  const handleScan = async () => {
    if (!name.trim() || !dob.trim()) return;
    
    setIsScanning(true);
    try {
      const input: AuraInput = {
        name: name.trim(),
        dob,
        tob: tob || undefined,
        now_timestamp: new Date().toISOString(),
        mode,
        options: {
          use_astrology: true,
          use_earth: true,
          use_db_cache: true
        }
      };
      
      const auraReading = generateReading(input);
      setReading(auraReading);
    } catch (error) {
      console.error('Aura scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="bg-gradient-to-br from-purple-900/20 to-indigo-900/20 border-purple-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-purple-200">
            🔮 Multiverseal Aura Reader
            <Badge variant="outline" className="bg-purple-500/20 text-purple-400">
              Deterministic Engine v2.0
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <Input
              placeholder="Full name..."
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Input
              type="date"
              placeholder="Date of birth"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
            />
            <Input
              type="time"
              placeholder="Time of birth (optional)"
              value={tob}
              onChange={(e) => setTob(e.target.value)}
            />
          </div>
          <div className="flex gap-2 items-center">
            <Button onClick={handleScan} disabled={isScanning || !name.trim() || !dob.trim()}>
              {isScanning ? 'Generating Reading...' : 'Generate Aura Reading'}
            </Button>
            {reading && (
              <div className="flex gap-2">
                <Button
                  variant={voice === 'mythic' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setVoice('mythic')}
                >
                  Mythic Voice
                </Button>
                <Button
                  variant={voice === 'plain' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setVoice('plain')}
                >
                  Plain Voice
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {reading && (
        <Tabs value={mode} onValueChange={(v) => setMode(v as any)} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="symbolic">Symbolic</TabsTrigger>
            <TabsTrigger value="technical">Technical</TabsTrigger>
            <TabsTrigger value="dual">Dual View</TabsTrigger>
            <TabsTrigger value="story">Story Mode</TabsTrigger>
          </TabsList>

          <TabsContent value="story" className="space-y-6">
            <LongFormNarrativeEngine 
              auraData={{
                name,
                archetype: reading.state_profile.archetype,
                karmic: reading.karmic,
                strengths: reading.state_profile.strengths,
                challenges: reading.state_profile.challenges,
                colors: reading.colors,
                chakra: reading.chakra,
                crossroad: reading.state_profile.crossroad,
                confidence: reading.state_profile.confidence,
                timelines: reading.timelines,
                practices: reading.practices,
                cosmic: reading.cosmic,
                earth: reading.earth
              }}
              qaid={reading.qaid}
            />
          </TabsContent>
          <TabsContent value="symbolic" className="space-y-6">
            <AuraNarrativeRenderer reading={reading} voice={voice} name={name} dob={dob} />
          </TabsContent>

          <TabsContent value="technical" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Quantum Signature</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="font-mono text-xs space-y-2">
                    <div>QAID: {reading.qaid}</div>
                    <div>QSEED: {reading.qseed}</div>
                    <div>Confidence: {(reading.state_profile.confidence * 100).toFixed(1)}%</div>
                    <div>Coherence: {(reading.chakra.coherence * 100).toFixed(1)}%</div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Chakra Matrix</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(reading.chakra).filter(([key]) => key !== 'coherence').map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-sm capitalize">{key.replace('_', ' ')}:</span>
                        <div className="flex items-center gap-2">
                          <Progress value={value * 100} className="w-20" />
                          <span className="text-xs font-mono">{(value * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
            
            <Card>
              <CardHeader>
                <CardTitle>Timeline Probabilities</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {Object.entries(reading.timelines).map(([path, data]) => (
                    <div key={path} className="bg-slate-700/50 p-3 rounded">
                      <h4 className="font-bold capitalize mb-2">{path}</h4>
                      <div className="text-sm">
                        <div>Likelihood: {(data.likelihood * 100).toFixed(1)}%</div>
                        <Progress value={data.likelihood * 100} className="my-2" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="dual" className="space-y-6">
            <div className="text-center mb-6">
              <img src={sacredImages[8]} alt="Portal" className="w-48 h-48 mx-auto rounded-lg opacity-80" />
            </div>
            
            <AuraNarrativeRenderer reading={reading} voice={voice} name={name} dob={dob} />
            
            <Card>
              <CardHeader>
                <CardTitle>Practices & Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(reading.practices).map(([practice, strength]) => (
                    <div key={practice} className="text-center">
                      <div className="capitalize font-medium mb-2">{practice}</div>
                      <Progress value={strength * 100} />
                      <div className="text-xs text-gray-400 mt-1">{(strength * 100).toFixed(0)}% beneficial</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

export default AuraReader;