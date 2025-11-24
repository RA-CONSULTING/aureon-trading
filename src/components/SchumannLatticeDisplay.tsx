import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Slider } from './ui/slider';

interface LatticeNode {
  id: string;
  x: number;
  y: number;
  frequency: number;
  amplitude: number;
  phase: number;
  connections: string[];
  emotionalResonance?: number;
}

interface EmotionalState {
  emotion: string;
  frequency_hz: number;
  color: string;
  symbol: string;
  role: string;
  intensity: number;
}

export default function SchumannLatticeDisplay() {
  const [nodes, setNodes] = useState<LatticeNode[]>([]);
  const [resonanceFreq, setResonanceFreq] = useState([7.83]);
  const [isActive, setIsActive] = useState(false);
  const [harmonics, setHarmonics] = useState([14.3, 20.8, 27.3, 33.8]);
  const [currentEmotion, setCurrentEmotion] = useState<EmotionalState | null>(null);
  const [emotionalCodex, setEmotionalCodex] = useState<any>(null);
  const [userFrequency, setUserFrequency] = useState(0);

  // Load emotional codex
  useEffect(() => {
    fetch('/emotional_codex.json')
      .then(res => res.json())
      .then(data => setEmotionalCodex(data))
      .catch(err => console.log('Emotional codex not found'));
  }, []);

  // Simulate user's emotional frequency detection
  useEffect(() => {
    if (!isActive || !emotionalCodex) return;
    
    const detectEmotionalState = () => {
      // Simulate biometric/frequency detection
      const baseFreq = resonanceFreq[0];
      const variance = Math.random() * 100 + 50; // 50-150 Hz variance
      const detectedFreq = baseFreq + variance;
      setUserFrequency(detectedFreq);
      
      // Find closest emotional match
      let closestEmotion = null;
      let minDiff = Infinity;
      
      emotionalCodex.entries.forEach((entry: any) => {
        const diff = Math.abs(entry.frequency_hz - detectedFreq);
        if (diff < minDiff) {
          minDiff = diff;
          closestEmotion = {
            ...entry,
            intensity: Math.max(0.1, 1 - (diff / 200)) // Higher intensity for closer matches
          };
        }
      });
      
      setCurrentEmotion(closestEmotion);
    };

    detectEmotionalState();
    const interval = setInterval(detectEmotionalState, 3000);
    return () => clearInterval(interval);
  }, [isActive, emotionalCodex, resonanceFreq]);

  useEffect(() => {
    const generateLattice = () => {
      const newNodes: LatticeNode[] = [];
      const gridSize = 8;
      
      for (let i = 0; i < gridSize; i++) {
        for (let j = 0; j < gridSize; j++) {
          const x = (i / (gridSize - 1)) * 2 - 1;
          const y = (j / (gridSize - 1)) * 2 - 1;
          const distance = Math.sqrt(x * x + y * y);
          
          // Apply emotional influence
          let emotionalInfluence = 1;
          if (currentEmotion && isActive) {
            const emotionalDistance = Math.abs(resonanceFreq[0] - currentEmotion.frequency_hz / 100);
            emotionalInfluence = 1 + (currentEmotion.intensity * (1 - emotionalDistance));
          }
          
          const node: LatticeNode = {
            id: `node_${i}_${j}`,
            x,
            y,
            frequency: resonanceFreq[0] * (1 + distance * 0.1) * emotionalInfluence,
            amplitude: Math.exp(-distance * 1.5) * (isActive ? 1 : 0.3) * emotionalInfluence,
            phase: Math.atan2(y, x) + Date.now() * 0.001,
            connections: [],
            emotionalResonance: currentEmotion ? currentEmotion.intensity * (1 - distance) : 0
          };
          
          newNodes.push(node);
        }
      }
      
      // Add connections between nearby nodes
      newNodes.forEach(node => {
        newNodes.forEach(other => {
          if (node.id !== other.id) {
            const dist = Math.sqrt((node.x - other.x) ** 2 + (node.y - other.y) ** 2);
            if (dist < 0.4) {
              node.connections.push(other.id);
            }
          }
        });
      });
      
      setNodes(newNodes);
    };

    generateLattice();
    const interval = setInterval(generateLattice, 100);
    return () => clearInterval(interval);
  }, [resonanceFreq, isActive, currentEmotion]);

  const getNodeColor = (node: LatticeNode) => {
    if (currentEmotion && node.emotionalResonance && node.emotionalResonance > 0.3) {
      // Use emotional color mapping
      const emotionColors: { [key: string]: string } = {
        'Deep Gray/Black': '#1a1a1a',
        'Dull Red': '#8b4513',
        'Red': '#ff0000',
        'Red-Orange': '#ff4500',
        'Orange': '#ffa500',
        'Yellow-Brown': '#daa520',
        'Yellow': '#ffff00',
        'Light Yellow': '#ffffe0',
        'Green-Yellow': '#adff2f',
        'Green': '#00ff00',
        'Blue-Green': '#00ffff',
        'Emerald / Pink': '#ff69b4',
        'Golden Green': '#ffd700',
        'Yellow-Gold': '#ffd700',
        'Sky Blue': '#87ceeb',
        'Rose-Gold': '#e91e63',
        'Soft Violet': '#dda0dd',
        'Indigo': '#4b0082',
        'Violet': '#8a2be2',
        'White / Rainbow': '#ffffff'
      };
      return emotionColors[currentEmotion.color] || '#64c8ff';
    }
    
    const intensity = node.amplitude;
    const hue = (node.frequency - 7) * 20 + 180;
    return `hsl(${hue}, 70%, ${30 + intensity * 40}%)`;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl flex items-center gap-2">
            🌍 Schumann Resonance Lattice
            <Badge variant={isActive ? "default" : "secondary"}>
              {isActive ? "ACTIVE" : "STANDBY"}
            </Badge>
          </CardTitle>
          <Button 
            onClick={() => setIsActive(!isActive)}
            variant={isActive ? "destructive" : "default"}
          >
            {isActive ? "Deactivate" : "Activate"}
          </Button>
        </div>
        
        {/* Real-time Emotional State Display */}
        {isActive && currentEmotion && (
          <div className="mt-4 p-4 bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg border">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">{currentEmotion.symbol}</span>
              <div>
                <h3 className="font-bold text-lg text-white">
                  Detected Emotional State: {currentEmotion.emotion}
                </h3>
                <p className="text-sm text-gray-300">
                  Frequency: {currentEmotion.frequency_hz} Hz • User Resonance: {userFrequency.toFixed(1)} Hz
                </p>
              </div>
              <Badge 
                variant="outline" 
                className="ml-auto"
                style={{ 
                  borderColor: getNodeColor({ emotionalResonance: 1 } as LatticeNode),
                  color: getNodeColor({ emotionalResonance: 1 } as LatticeNode)
                }}
              >
                {(currentEmotion.intensity * 100).toFixed(0)}% Match
              </Badge>
            </div>
            <p className="text-xs text-gray-400">
              <strong>Lattice Effect:</strong> {currentEmotion.role}
            </p>
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">
            Base Frequency: {resonanceFreq[0].toFixed(2)} Hz
          </label>
          <Slider
            value={resonanceFreq}
            onValueChange={setResonanceFreq}
            min={6}
            max={10}
            step={0.01}
            className="w-full"
          />
        </div>

        <div className="flex justify-center">
          <svg width="400" height="400" className="border rounded-lg bg-black">
            {/* Grid lines */}
            <defs>
              <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#333" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            {/* Emotional field overlay */}
            {currentEmotion && isActive && (
              <circle
                cx="200"
                cy="200"
                r={100 * currentEmotion.intensity}
                fill={getNodeColor({ emotionalResonance: 1 } as LatticeNode)}
                opacity="0.1"
              >
                <animate
                  attributeName="r"
                  values={`${80 * currentEmotion.intensity};${120 * currentEmotion.intensity};${80 * currentEmotion.intensity}`}
                  dur="4s"
                  repeatCount="indefinite"
                />
              </circle>
            )}
            
            {/* Connections */}
            {nodes.map(node => 
              node.connections.map(connId => {
                const connNode = nodes.find(n => n.id === connId);
                if (!connNode) return null;
                
                const x1 = (node.x + 1) * 200;
                const y1 = (node.y + 1) * 200;
                const x2 = (connNode.x + 1) * 200;
                const y2 = (connNode.y + 1) * 200;
                
                const connectionColor = node.emotionalResonance && node.emotionalResonance > 0.3 
                  ? getNodeColor(node) 
                  : "rgba(100, 200, 255, 0.3)";
                
                return (
                  <line
                    key={`${node.id}-${connId}`}
                    x1={x1}
                    y1={y1}
                    x2={x2}
                    y2={y2}
                    stroke={connectionColor}
                    strokeWidth={node.amplitude * 2}
                    opacity={0.6}
                  />
                );
              })
            )}
            
            {/* Nodes */}
            {nodes.map(node => {
              const x = (node.x + 1) * 200;
              const y = (node.y + 1) * 200;
              const radius = 3 + node.amplitude * 5;
              
              return (
                <circle
                  key={node.id}
                  cx={x}
                  cy={y}
                  r={radius}
                  fill={getNodeColor(node)}
                  stroke="white"
                  strokeWidth="1"
                  opacity={0.8 + node.amplitude * 0.2}
                >
                  <animate
                    attributeName="r"
                    values={`${radius};${radius + 2};${radius}`}
                    dur={`${2 / node.frequency}s`}
                    repeatCount="indefinite"
                  />
                </circle>
              );
            })}
            
            {/* Center resonance indicator */}
            <circle
              cx="200"
              cy="200"
              r="20"
              fill="none"
              stroke={currentEmotion ? getNodeColor({ emotionalResonance: 1 } as LatticeNode) : "gold"}
              strokeWidth="2"
              opacity={isActive ? 0.8 : 0.3}
            >
              <animate
                attributeName="r"
                values="20;25;20"
                dur="2s"
                repeatCount="indefinite"
              />
            </circle>
            
            {/* Emotional symbol at center */}
            {currentEmotion && isActive && (
              <text
                x="200"
                y="205"
                textAnchor="middle"
                fontSize="16"
                fill="white"
                opacity="0.8"
              >
                {currentEmotion.symbol}
              </text>
            )}
          </svg>
        </div>

        <div className="grid grid-cols-4 gap-3 text-sm">
          <div className="text-center">
            <div className="font-semibold">Primary</div>
            <div className="text-green-400">{resonanceFreq[0].toFixed(2)} Hz</div>
          </div>
          {harmonics.slice(0, 3).map((freq, i) => (
            <div key={i} className="text-center">
              <div className="font-semibold">H{i + 2}</div>
              <div className="text-blue-400">{freq.toFixed(1)} Hz</div>
            </div>
          ))}
        </div>

        <div className="text-xs text-center text-muted-foreground">
          {isActive && currentEmotion 
            ? `Emotional resonance detected • ${currentEmotion.emotion} at ${currentEmotion.frequency_hz}Hz • Lattice synchronized`
            : `Earth's electromagnetic field resonance patterns • ${nodes.length} nodes • ${nodes.reduce((sum, n) => sum + n.connections.length, 0)} connections`
          }
        </div>
      </CardContent>
    </Card>
  );
}