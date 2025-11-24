import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import * as THREE from 'three';

interface FieldMetric {
  time: number;
  entropy: number;
  coherence: number;
}

interface LatticeFieldVisualizerProps {
  data?: FieldMetric[];
  className?: string;
}

export function LatticeFieldVisualizer({ data = [], className }: LatticeFieldVisualizerProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const cameraRef = useRef<THREE.PerspectiveCamera>();
  const [isRotating, setIsRotating] = useState(true);
  const [pointCount, setPointCount] = useState(0);

  const getCoherenceColor = (coherence: number): THREE.Color => {
    if (coherence > 0.7) return new THREE.Color('gold');
    if (coherence < 0.3) return new THREE.Color('red');
    return new THREE.Color('cyan');
  };

  useEffect(() => {
    if (!mountRef.current || data.length === 0) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(75, 400 / 300, 0.1, 1000);
    camera.position.set(10, 10, 10);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(400, 300);
    renderer.shadowMap.enabled = true;
    rendererRef.current = renderer;
    mountRef.current.appendChild(renderer.domElement);

    // Normalize data for visualization
    const maxTime = Math.max(...data.map(d => d.time));
    const maxEntropy = Math.max(...data.map(d => d.entropy));

    // Create geometry for points and lines
    const pointsGeometry = new THREE.BufferGeometry();
    const lineGeometry = new THREE.BufferGeometry();
    const positions: number[] = [];
    const colors: number[] = [];
    const linePositions: number[] = [];

    data.forEach((point, index) => {
      const x = (point.time / maxTime) * 20 - 10;
      const y = (point.entropy / maxEntropy) * 20 - 10;
      const z = point.coherence * 20 - 10;

      positions.push(x, y, z);
      linePositions.push(x, y, z);

      const color = getCoherenceColor(point.coherence);
      colors.push(color.r, color.g, color.b);
    });

    pointsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    pointsGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));

    // Create points
    const pointsMaterial = new THREE.PointsMaterial({ 
      size: 0.3, 
      vertexColors: true,
      transparent: true,
      opacity: 0.9
    });
    const points = new THREE.Points(pointsGeometry, pointsMaterial);
    scene.add(points);

    // Create connecting line
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.5, transparent: true });
    const line = new THREE.Line(lineGeometry, lineMaterial);
    scene.add(line);

    // Add axis helpers
    const axesHelper = new THREE.AxesHelper(15);
    scene.add(axesHelper);

    // Add grid
    const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
    scene.add(gridHelper);

    setPointCount(data.length);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      
      if (isRotating) {
        points.rotation.y += 0.005;
        line.rotation.y += 0.005;
      }
      
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [data, isRotating]);

  const loadSampleData = () => {
    // Generate sample data similar to field pull metrics
    const sampleData: FieldMetric[] = [];
    for (let i = 0; i < 50; i++) {
      sampleData.push({
        time: i,
        entropy: Math.random() * 0.8 + 0.1,
        coherence: Math.random() * 0.9 + 0.1
      });
    }
    return sampleData;
  };

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold">Lattice Field Map</CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant="outline">{pointCount} points</Badge>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setIsRotating(!isRotating)}
          >
            {isRotating ? 'Pause' : 'Rotate'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div 
          ref={mountRef} 
          className="w-full h-[300px] border rounded-lg bg-black"
          style={{ minHeight: '300px' }}
        />
        <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
          <div className="text-center">
            <div className="text-muted-foreground">X-Axis</div>
            <div className="font-medium">Time</div>
          </div>
          <div className="text-center">
            <div className="text-muted-foreground">Y-Axis</div>
            <div className="font-medium">Entropy</div>
          </div>
          <div className="text-center">
            <div className="text-muted-foreground">Z-Axis</div>
            <div className="font-medium">Coherence</div>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>High Coherence (&gt;0.7)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-cyan-500 rounded-full"></div>
            <span>Mid Coherence</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>Low Coherence (&lt;0.3)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}