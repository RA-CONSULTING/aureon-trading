import { useRef, useState, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, Line, Text } from '@react-three/drei';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import * as THREE from 'three';

interface FieldNode {
  position: [number, number, number];
  phase: number;
  label: string;
  color: string;
}

interface PhaseFieldProps {
  amplitude: number;
  rotationSpeed: number;
}

function PhaseFieldVisualization({ amplitude, rotationSpeed }: PhaseFieldProps) {
  const groupRef = useRef<THREE.Group>(null);
  
  // Define the 9 Auris nodes in 3D space arranged in a tandem pattern
  const nodes: FieldNode[] = useMemo(() => [
    // Center node (Observer)
    { position: [0, 0, 0], phase: 0, label: 'Observer', color: '#9b87f5' },
    
    // Inner ring (3 nodes)
    { position: [2, 0, 0], phase: Math.PI / 3, label: 'Tiger', color: '#f97316' },
    { position: [-1, 1.732, 0], phase: Math.PI, label: 'Falcon', color: '#0EA5E9' },
    { position: [-1, -1.732, 0], phase: 5 * Math.PI / 3, label: 'Dolphin', color: '#06b6d4' },
    
    // Outer ring (5 nodes)
    { position: [4, 0, 0], phase: 0, label: 'Hummingbird', color: '#10b981' },
    { position: [2, 3.464, 0], phase: Math.PI / 2, label: 'Deer', color: '#8b5cf6' },
    { position: [-2, 3.464, 0], phase: 3 * Math.PI / 4, label: 'Owl', color: '#f59e0b' },
    { position: [-4, 0, 0], phase: Math.PI, label: 'Panda', color: '#ec4899' },
    { position: [-2, -3.464, 0], phase: 5 * Math.PI / 4, label: 'CargoShip', color: '#6366f1' },
  ], []);

  // Auto-rotation
  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * rotationSpeed;
    }
  });

  // Generate connections between nodes
  const connections = useMemo(() => {
    const lines: [FieldNode, FieldNode][] = [];
    // Connect center to inner ring
    for (let i = 1; i <= 3; i++) {
      lines.push([nodes[0], nodes[i]]);
    }
    // Connect inner ring to outer ring
    lines.push([nodes[1], nodes[4]]);
    lines.push([nodes[2], nodes[6]]);
    lines.push([nodes[2], nodes[7]]);
    lines.push([nodes[3], nodes[8]]);
    lines.push([nodes[1], nodes[5]]);
    // Connect within outer ring
    for (let i = 4; i < 8; i++) {
      lines.push([nodes[i], nodes[i + 1]]);
    }
    lines.push([nodes[8], nodes[4]]); // Close the outer ring
    return lines;
  }, [nodes]);

  return (
    <group ref={groupRef}>
      {/* Ambient field effect */}
      <Sphere args={[6, 32, 32]}>
        <meshBasicMaterial 
          color="#9b87f5" 
          opacity={0.05} 
          transparent 
          wireframe 
        />
      </Sphere>

      {/* Field nodes */}
      {nodes.map((node, index) => (
        <group key={index} position={node.position}>
          {/* Pulsing sphere */}
          <PulsingNode 
            color={node.color} 
            phase={node.phase} 
            amplitude={amplitude}
          />
          
          {/* Node label */}
          <Text
            position={[0, 0.8, 0]}
            fontSize={0.3}
            color="#ffffff"
            anchorX="center"
            anchorY="middle"
          >
            {node.label}
          </Text>
        </group>
      ))}

      {/* Connections between nodes */}
      {connections.map((connection, index) => (
        <Line
          key={index}
          points={[connection[0].position, connection[1].position]}
          color="#9b87f5"
          lineWidth={2}
          opacity={0.6}
          transparent
        />
      ))}

      {/* Phase field rings */}
      <PhaseRing radius={2} amplitude={amplitude} color="#0EA5E9" />
      <PhaseRing radius={4} amplitude={amplitude} color="#9b87f5" />
    </group>
  );
}

function PulsingNode({ 
  color, 
  phase, 
  amplitude 
}: { 
  color: string; 
  phase: number; 
  amplitude: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (meshRef.current) {
      const pulse = Math.sin(state.clock.elapsedTime * 2 + phase) * 0.2 * amplitude + 1;
      meshRef.current.scale.setScalar(pulse);
    }
  });

  return (
    <>
      <Sphere ref={meshRef} args={[0.3, 16, 16]}>
        <meshStandardMaterial 
          color={color} 
          emissive={color}
          emissiveIntensity={0.5}
        />
      </Sphere>
      {/* Glow effect */}
      <Sphere args={[0.4, 16, 16]}>
        <meshBasicMaterial 
          color={color} 
          opacity={0.3} 
          transparent 
        />
      </Sphere>
    </>
  );
}

function PhaseRing({ 
  radius, 
  amplitude, 
  color 
}: { 
  radius: number; 
  amplitude: number; 
  color: string;
}) {
  const ringRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ringRef.current) {
      const wave = Math.sin(state.clock.elapsedTime) * 0.1 * amplitude;
      ringRef.current.scale.set(1 + wave, 1 + wave, 1 + wave);
      ringRef.current.rotation.z += 0.001;
    }
  });

  return (
    <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
      <torusGeometry args={[radius, 0.05, 16, 100]} />
      <meshStandardMaterial 
        color={color} 
        emissive={color}
        emissiveIntensity={0.3}
        transparent
        opacity={0.6}
      />
    </mesh>
  );
}

export function HarmonicNexusPhaseField3D() {
  const [amplitude, setAmplitude] = useState(1);
  const [rotationSpeed, setRotationSpeed] = useState(0.2);

  return (
    <Card className="p-6 bg-card border-border">
      <div className="space-y-4">
        <div>
          <h3 className="text-xl font-semibold text-foreground mb-2">
            🌀 Harmonic Nexus Phase Field (Tandem View)
          </h3>
          <p className="text-sm text-muted-foreground">
            Interactive 3D visualization of the 9-node Auris substrate with real-time phase dynamics
          </p>
        </div>

        {/* 3D Canvas */}
        <div className="h-[500px] bg-black/20 rounded-lg border border-border overflow-hidden">
          <Canvas camera={{ position: [0, 5, 10], fov: 60 }}>
            <ambientLight intensity={0.3} />
            <pointLight position={[10, 10, 10]} intensity={1} />
            <pointLight position={[-10, -10, -10]} intensity={0.5} />
            
            <PhaseFieldVisualization 
              amplitude={amplitude} 
              rotationSpeed={rotationSpeed}
            />
            
            <OrbitControls 
              enablePan={true}
              enableZoom={true}
              minDistance={5}
              maxDistance={20}
            />
          </Canvas>
        </div>

        {/* Controls */}
        <div className="space-y-4 border-t border-border pt-4">
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label htmlFor="amplitude" className="text-sm text-foreground">
                Field Amplitude
              </Label>
              <span className="text-sm text-muted-foreground">
                {amplitude.toFixed(2)}x
              </span>
            </div>
            <Slider
              id="amplitude"
              min={0}
              max={2}
              step={0.1}
              value={[amplitude]}
              onValueChange={(value) => setAmplitude(value[0])}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label htmlFor="rotation" className="text-sm text-foreground">
                Rotation Speed
              </Label>
              <span className="text-sm text-muted-foreground">
                {rotationSpeed.toFixed(2)}x
              </span>
            </div>
            <Slider
              id="rotation"
              min={0}
              max={1}
              step={0.05}
              value={[rotationSpeed]}
              onValueChange={(value) => setRotationSpeed(value[0])}
              className="w-full"
            />
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-3 gap-2 border-t border-border pt-4">
          <div className="text-xs">
            <span className="inline-block w-3 h-3 rounded-full bg-[#9b87f5] mr-1" />
            <span className="text-muted-foreground">Observer Core</span>
          </div>
          <div className="text-xs">
            <span className="inline-block w-3 h-3 rounded-full bg-[#0EA5E9] mr-1" />
            <span className="text-muted-foreground">Inner Ring</span>
          </div>
          <div className="text-xs">
            <span className="inline-block w-3 h-3 rounded-full bg-[#10b981] mr-1" />
            <span className="text-muted-foreground">Outer Ring</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
