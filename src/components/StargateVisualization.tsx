import { useEffect, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, Line, Html } from '@react-three/drei';
import * as THREE from 'three';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { stargateLayer } from '@/core/stargateLattice';
import type { StargateNode } from '@/core/stargateLattice';

// Convert lat/lng to 3D sphere coordinates
const latLngToVector3 = (lat: number, lng: number, radius: number = 2) => {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);
  
  return new THREE.Vector3(
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta)
  );
};

// Animated stargate node
const StargateMarker = ({ node, index }: { node: StargateNode; index: number }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);
  
  const position = latLngToVector3(node.coordinates.lat, node.coordinates.lng);
  
  useFrame((state) => {
    if (meshRef.current) {
      // Pulse animation based on node cycle
      const scale = 1 + Math.sin(state.clock.elapsedTime * (60 / node.cycle)) * 0.2;
      meshRef.current.scale.setScalar(scale);
    }
  });
  
  // Color based on primary frequency
  const getNodeColor = () => {
    const freq = node.frequencies[0];
    if (freq < 400) return '#FF6B35'; // Orange-red (root/sacral)
    if (freq < 550) return '#00FF88'; // Green (heart - 528Hz)
    if (freq < 750) return '#4169E1'; // Blue (throat/third eye)
    return '#9370DB'; // Purple (crown)
  };
  
  return (
    <group>
      <Sphere
        ref={meshRef}
        args={[0.05, 16, 16]}
        position={position}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={getNodeColor()}
          emissive={getNodeColor()}
          emissiveIntensity={hovered ? 1.5 : 0.8}
          transparent
          opacity={0.9}
        />
      </Sphere>
      
      {hovered && (
        <Html position={position} center>
          <div className="bg-background/95 border border-border rounded-lg p-3 shadow-xl backdrop-blur-sm min-w-[200px]">
            <h4 className="font-bold text-sm mb-1">{node.name}</h4>
            <p className="text-xs text-muted-foreground mb-2">{node.description}</p>
            <div className="flex flex-wrap gap-1">
              {node.frequencies.map((freq, i) => (
                <Badge key={i} variant="secondary" className="text-xs">
                  {freq}Hz
                </Badge>
              ))}
            </div>
          </div>
        </Html>
      )}
    </group>
  );
};

// Ley lines connecting nodes
const LeyLines = ({ nodes }: { nodes: StargateNode[] }) => {
  const connections: [THREE.Vector3, THREE.Vector3][] = [];
  
  // Connect each node to its 3 nearest neighbors (simplified sacred geometry)
  nodes.forEach((node, i) => {
    const pos1 = latLngToVector3(node.coordinates.lat, node.coordinates.lng);
    
    // Calculate distances to other nodes
    const distances = nodes
      .map((otherNode, j) => ({
        index: j,
        distance: pos1.distanceTo(
          latLngToVector3(otherNode.coordinates.lat, otherNode.coordinates.lng)
        )
      }))
      .filter(d => d.index !== i)
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 3); // Connect to 3 nearest
    
    distances.forEach(d => {
      const pos2 = latLngToVector3(
        nodes[d.index].coordinates.lat,
        nodes[d.index].coordinates.lng
      );
      connections.push([pos1, pos2]);
    });
  });
  
  return (
    <>
      {connections.map((points, i) => (
        <Line
          key={i}
          points={points}
          color="#00FF88"
          lineWidth={0.5}
          transparent
          opacity={0.3}
        />
      ))}
    </>
  );
};

// Earth sphere with texture
const Earth = () => {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame(() => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.001; // Slow rotation
    }
  });
  
  return (
    <Sphere ref={meshRef} args={[2, 64, 64]}>
      <meshPhongMaterial
        color="#1e3a5f"
        emissive="#0a1929"
        emissiveIntensity={0.5}
        transparent
        opacity={0.8}
        wireframe={false}
      />
    </Sphere>
  );
};

// Energy field visualization
const EnergyField = () => {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.1;
      meshRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.2) * 0.1;
    }
  });
  
  return (
    <Sphere ref={meshRef} args={[2.3, 32, 32]}>
      <meshBasicMaterial
        color="#00FF88"
        transparent
        opacity={0.05}
        wireframe
      />
    </Sphere>
  );
};

// Main 3D scene
const Scene = ({ nodes }: { nodes: StargateNode[] }) => {
  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.5} />
      
      <Earth />
      <EnergyField />
      <LeyLines nodes={nodes} />
      
      {nodes.map((node, i) => (
        <StargateMarker key={node.name} node={node} index={i} />
      ))}
      
      <OrbitControls
        enablePan={false}
        enableZoom={true}
        minDistance={3}
        maxDistance={10}
        autoRotate
        autoRotateSpeed={0.5}
      />
    </>
  );
};

export const StargateVisualization = () => {
  const [nodes, setNodes] = useState<StargateNode[]>([]);
  const [gridEnergy, setGridEnergy] = useState(0);
  
  useEffect(() => {
    setNodes(stargateLayer.getAllNodes());
    setGridEnergy(stargateLayer.calculateGridEnergy());
    
    // Update grid energy every minute
    const interval = setInterval(() => {
      setGridEnergy(stargateLayer.calculateGridEnergy());
    }, 60000);
    
    return () => clearInterval(interval);
  }, []);
  
  return (
    <Card className="bg-card shadow-card">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">🌍</span>
              Stargate Lattice Network
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              12-node planetary sacred geometry grid
            </p>
          </div>
          <div className="text-right">
            <div className="text-xs text-muted-foreground mb-1">Grid Energy</div>
            <Badge variant="default" className="text-lg font-mono">
              {(gridEnergy * 100).toFixed(1)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[600px] rounded-lg overflow-hidden border border-border bg-background/50">
          <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
            <Scene nodes={nodes} />
          </Canvas>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
          {nodes.slice(0, 8).map((node) => (
            <div
              key={node.name}
              className="p-3 rounded-lg border border-border bg-muted/20 hover:bg-muted/40 transition-colors"
            >
              <h4 className="font-semibold text-sm mb-1">{node.name}</h4>
              <div className="flex flex-wrap gap-1">
                {node.frequencies.map((freq, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {freq}Hz
                  </Badge>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                {node.vibration}
              </p>
            </div>
          ))}
        </div>
        
        <div className="mt-6 p-4 rounded-lg bg-primary/5 border border-primary/20">
          <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
            <span>💚</span>
            Integration with AUREON
          </h4>
          <p className="text-xs text-muted-foreground leading-relaxed">
            The Stargate Lattice enhances AUREON's coherence field by providing geolocation-based 
            frequency adjustments. Trading near sacred nodes receives up to +20% coherence boost 
            from the planetary grid. The system integrates with Rainbow Bridge and The Prism for 
            unified consciousness-based market analysis.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
