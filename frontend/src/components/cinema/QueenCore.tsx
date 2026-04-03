/**
 * QueenCore - The central luminous entity of the Queens trading system
 * Breathing icosahedron with shader-driven glow, color-mapped to system state
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface QueenCoreProps {
  coherence: number;       // 0-1, drives glow intensity
  prismState: string;      // FORMING, BLUE, GOLD, RED - drives color
  queenState: string;      // HOLD, BUY, SELL - drives pulse color
  hncMarketState: string;  // CONSOLIDATION, TRENDING, VOLATILE, BREAKOUT
  lambda: number;          // secondary metric
}

// Vertex shader: organic breathing displacement
const queenVertexShader = `
  uniform float uTime;
  uniform float uCoherence;
  varying vec3 vNormal;
  varying vec3 vPosition;
  varying float vDisplacement;

  // Simple noise for organic movement
  float noise3d(vec3 p) {
    return fract(sin(dot(p, vec3(12.9898, 78.233, 45.543))) * 43758.5453);
  }

  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = position;

    // Breathing displacement
    float breath = sin(uTime * 0.8) * 0.08 + sin(uTime * 1.3) * 0.04;

    // Organic surface undulation
    float wave1 = sin(position.x * 3.0 + uTime * 1.2) * 0.05;
    float wave2 = sin(position.y * 4.0 + uTime * 0.9) * 0.04;
    float wave3 = cos(position.z * 2.5 + uTime * 1.5) * 0.03;

    // Coherence amplifies the displacement
    float displacement = (breath + wave1 + wave2 + wave3) * (0.5 + uCoherence * 1.5);
    vDisplacement = displacement;

    vec3 newPosition = position + normal * displacement;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
  }
`;

// Fragment shader: emissive glow with state-driven color
const queenFragmentShader = `
  uniform float uTime;
  uniform float uCoherence;
  uniform vec3 uBaseColor;
  uniform vec3 uPulseColor;
  uniform float uPulseIntensity;
  varying vec3 vNormal;
  varying vec3 vPosition;
  varying float vDisplacement;

  void main() {
    // Fresnel effect for edge glow
    vec3 viewDir = normalize(cameraPosition - vPosition);
    float fresnel = pow(1.0 - abs(dot(viewDir, vNormal)), 2.5);

    // Core color with coherence-driven intensity
    float coreGlow = 0.3 + uCoherence * 0.7;
    vec3 core = uBaseColor * coreGlow;

    // Pulsing energy veins
    float vein = sin(vPosition.x * 8.0 + uTime * 2.0) *
                 sin(vPosition.y * 6.0 - uTime * 1.5) *
                 sin(vPosition.z * 7.0 + uTime * 1.8);
    vein = smoothstep(0.3, 0.8, vein) * 0.4;

    // Combine
    vec3 color = core + uBaseColor * fresnel * 2.0 + uBaseColor * vein;

    // Trade pulse overlay
    float pulse = sin(uTime * 4.0) * 0.5 + 0.5;
    color = mix(color, uPulseColor, pulse * uPulseIntensity * 0.3);

    // Surface shimmer
    float shimmer = sin(vPosition.x * 15.0 + uTime * 3.0) *
                    cos(vPosition.y * 12.0 - uTime * 2.5) * 0.1;
    color += vec3(shimmer) * uCoherence;

    float alpha = 0.7 + fresnel * 0.3;
    gl_FragColor = vec4(color, alpha);
  }
`;

// Outer halo ring
function HaloRing({ hncMarketState, coherence }: { hncMarketState: string; coherence: number }) {
  const ringRef = useRef<THREE.Mesh>(null);

  const haloColor = useMemo(() => {
    switch (hncMarketState) {
      case 'TRENDING': return '#00ff88';
      case 'VOLATILE': return '#ff4444';
      case 'BREAKOUT': return '#ffaa00';
      default: return '#4488ff'; // CONSOLIDATION
    }
  }, [hncMarketState]);

  useFrame((state) => {
    if (ringRef.current) {
      ringRef.current.rotation.z = state.clock.elapsedTime * 0.2;
      ringRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.15) * 0.3;
    }
  });

  return (
    <mesh ref={ringRef}>
      <torusGeometry args={[2.8, 0.03, 16, 64]} />
      <meshBasicMaterial
        color={haloColor}
        transparent
        opacity={0.4 + coherence * 0.4}
      />
    </mesh>
  );
}

// Second decorative ring at different angle
function InnerRing({ coherence }: { coherence: number }) {
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ringRef.current) {
      ringRef.current.rotation.z = -state.clock.elapsedTime * 0.3;
      ringRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });

  return (
    <mesh ref={ringRef} rotation={[Math.PI / 3, 0, 0]}>
      <torusGeometry args={[2.2, 0.015, 16, 48]} />
      <meshBasicMaterial
        color="#aa66ff"
        transparent
        opacity={0.2 + coherence * 0.3}
      />
    </mesh>
  );
}

// Pulse wave that emanates on BUY/SELL
function PulseWave({ queenState, coherence }: { queenState: string; coherence: number }) {
  const ringRef = useRef<THREE.Mesh>(null);
  const scaleRef = useRef(0);
  const opacityRef = useRef(0);

  const pulseColor = useMemo(() => {
    switch (queenState) {
      case 'BUY': return '#00ff66';
      case 'SELL': return '#ff4466';
      default: return '#4488ff';
    }
  }, [queenState]);

  useFrame((_, delta) => {
    if (!ringRef.current) return;

    // Continuous expanding pulse
    scaleRef.current += delta * 2;
    if (scaleRef.current > 6) {
      scaleRef.current = 0;
    }

    opacityRef.current = Math.max(0, 1 - scaleRef.current / 6) * 0.3 * coherence;
    const s = 1 + scaleRef.current;
    ringRef.current.scale.set(s, s, s);
    (ringRef.current.material as THREE.MeshBasicMaterial).opacity = opacityRef.current;
  });

  return (
    <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
      <ringGeometry args={[1.8, 2.0, 32]} />
      <meshBasicMaterial
        color={pulseColor}
        transparent
        opacity={0.3}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  );
}

export function QueenCore({
  coherence = 0.5,
  prismState = 'FORMING',
  queenState = 'HOLD',
  hncMarketState = 'CONSOLIDATION',
  lambda = 0.5,
}: QueenCoreProps) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const groupRef = useRef<THREE.Group>(null);

  // Map prism state to base color
  const baseColor = useMemo(() => {
    switch (prismState) {
      case 'BLUE': return new THREE.Color(0.1, 0.5, 1.0);
      case 'GOLD': return new THREE.Color(1.0, 0.7, 0.1);
      case 'RED': return new THREE.Color(1.0, 0.15, 0.2);
      default: return new THREE.Color(0.4, 0.3, 0.9); // FORMING - purple
    }
  }, [prismState]);

  // Map queen state to pulse color
  const pulseColor = useMemo(() => {
    switch (queenState) {
      case 'BUY': return new THREE.Color(0.0, 1.0, 0.4);
      case 'SELL': return new THREE.Color(1.0, 0.2, 0.3);
      default: return new THREE.Color(0.2, 0.4, 1.0);
    }
  }, [queenState]);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uCoherence: { value: coherence },
    uBaseColor: { value: baseColor },
    uPulseColor: { value: pulseColor },
    uPulseIntensity: { value: queenState === 'HOLD' ? 0.1 : 0.8 },
  }), []);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      materialRef.current.uniforms.uCoherence.value = THREE.MathUtils.lerp(
        materialRef.current.uniforms.uCoherence.value,
        coherence,
        0.05
      );
      materialRef.current.uniforms.uBaseColor.value.lerp(baseColor, 0.03);
      materialRef.current.uniforms.uPulseColor.value.lerp(pulseColor, 0.05);
      materialRef.current.uniforms.uPulseIntensity.value = queenState === 'HOLD' ? 0.1 : 0.8;
    }

    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.05;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Core icosahedron */}
      <mesh>
        <icosahedronGeometry args={[1.8, 4]} />
        <shaderMaterial
          ref={materialRef}
          vertexShader={queenVertexShader}
          fragmentShader={queenFragmentShader}
          uniforms={uniforms}
          transparent
          depthWrite={false}
        />
      </mesh>

      {/* Inner glow sphere */}
      <mesh>
        <sphereGeometry args={[1.5, 16, 16]} />
        <meshBasicMaterial
          color={baseColor}
          transparent
          opacity={0.15 + coherence * 0.2}
        />
      </mesh>

      {/* Point light at core */}
      <pointLight
        color={baseColor}
        intensity={1.0 + coherence * 4.0}
        distance={30}
        decay={2}
      />

      {/* Outer rings */}
      <HaloRing hncMarketState={hncMarketState} coherence={coherence} />
      <InnerRing coherence={coherence} />

      {/* Pulse wave */}
      <PulseWave queenState={queenState} coherence={coherence} />
    </group>
  );
}
