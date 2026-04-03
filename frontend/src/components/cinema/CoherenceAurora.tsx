/**
 * CoherenceAurora - Northern lights emanating from the Queen's consciousness
 * Ribbon geometry with vertex displacement and gradient bands
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface CoherenceAuroraProps {
  coherence: number;      // 0-1
  lambda: number;         // secondary metric
  gaiaFrequency: number;  // frequency state
  hasNewThought: boolean; // triggers bright pulse
}

const auroraVertexShader = `
  uniform float uTime;
  uniform float uCoherence;
  uniform float uPulse;

  varying vec2 vUv;
  varying float vDisplacement;

  // Simple noise
  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
  }

  void main() {
    vUv = uv;

    vec3 pos = position;

    // Multi-frequency wave displacement
    float wave1 = sin(pos.x * 0.5 + uTime * 0.6) * 2.0;
    float wave2 = sin(pos.x * 1.2 - uTime * 0.4) * 1.0;
    float wave3 = cos(pos.x * 0.8 + uTime * 0.8) * 0.5;

    // Noise-based displacement
    float n = noise(vec2(pos.x * 0.3 + uTime * 0.1, uTime * 0.05)) * 3.0;

    float displacement = (wave1 + wave2 + wave3 + n) * uCoherence;
    displacement += uPulse * sin(pos.x * 2.0 + uTime * 5.0) * 2.0;

    pos.y += displacement;
    pos.z += sin(pos.x * 0.3 + uTime * 0.2) * 1.5 * uCoherence;

    vDisplacement = displacement * 0.1;

    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;

const auroraFragmentShader = `
  uniform float uTime;
  uniform float uCoherence;
  uniform float uLambda;
  uniform float uPulse;

  varying vec2 vUv;
  varying float vDisplacement;

  void main() {
    // Aurora bands: green, cyan, purple
    vec3 green = vec3(0.1, 0.9, 0.4);
    vec3 cyan = vec3(0.1, 0.8, 0.9);
    vec3 purple = vec3(0.5, 0.1, 0.9);
    vec3 pink = vec3(0.9, 0.2, 0.6);

    // Band selection based on UV and displacement
    float band = sin(vUv.x * 6.28 + uTime * 0.3 + vDisplacement * 3.0) * 0.5 + 0.5;
    float band2 = cos(vUv.x * 4.0 - uTime * 0.5) * 0.5 + 0.5;

    vec3 color = mix(green, cyan, band);
    color = mix(color, purple, band2 * 0.5);
    color = mix(color, pink, uLambda * 0.3);

    // Pulse brightening
    color += vec3(0.2, 0.5, 0.3) * uPulse;

    // Vertical fade (stronger at bottom of ribbon, fading at top)
    float vertFade = smoothstep(0.0, 0.3, vUv.y) * smoothstep(1.0, 0.4, vUv.y);

    // Horizontal variation
    float horzVar = sin(vUv.x * 12.0 + uTime) * 0.3 + 0.7;

    float alpha = vertFade * horzVar * (0.1 + uCoherence * 0.4);

    // Edge softening
    alpha *= smoothstep(0.0, 0.05, vUv.x) * smoothstep(1.0, 0.95, vUv.x);

    gl_FragColor = vec4(color * (0.8 + uCoherence * 0.5), alpha);
  }
`;

function AuroraRibbon({
  yOffset,
  zOffset,
  coherence,
  lambda,
  pulse,
  widthScale = 1,
}: {
  yOffset: number;
  zOffset: number;
  coherence: number;
  lambda: number;
  pulse: number;
  widthScale?: number;
}) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uCoherence: { value: coherence },
    uLambda: { value: lambda },
    uPulse: { value: pulse },
  }), []);

  useFrame((state) => {
    if (!materialRef.current) return;
    const u = materialRef.current.uniforms;
    u.uTime.value = state.clock.elapsedTime;
    u.uCoherence.value = THREE.MathUtils.lerp(u.uCoherence.value, coherence, 0.05);
    u.uLambda.value = THREE.MathUtils.lerp(u.uLambda.value, lambda, 0.05);
    u.uPulse.value = THREE.MathUtils.lerp(u.uPulse.value, pulse, 0.1);
  });

  return (
    <mesh position={[0, yOffset, zOffset]}>
      <planeGeometry args={[30 * widthScale, 4, 100, 4]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={auroraVertexShader}
        fragmentShader={auroraFragmentShader}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

export function CoherenceAurora({
  coherence = 0.5,
  lambda = 0.5,
  gaiaFrequency = 432,
  hasNewThought = false,
}: CoherenceAuroraProps) {
  const pulseRef = useRef(0);

  useFrame((_, delta) => {
    if (hasNewThought) {
      pulseRef.current = Math.min(pulseRef.current + delta * 3, 1);
    } else {
      pulseRef.current = Math.max(pulseRef.current - delta * 0.5, 0);
    }
  });

  return (
    <group>
      <AuroraRibbon
        yOffset={8}
        zOffset={-2}
        coherence={coherence}
        lambda={lambda}
        pulse={pulseRef.current}
        widthScale={1.0}
      />
      <AuroraRibbon
        yOffset={10}
        zOffset={1}
        coherence={coherence * 0.7}
        lambda={lambda}
        pulse={pulseRef.current * 0.6}
        widthScale={0.8}
      />
      <AuroraRibbon
        yOffset={12}
        zOffset={-3}
        coherence={coherence * 0.4}
        lambda={lambda}
        pulse={pulseRef.current * 0.3}
        widthScale={0.6}
      />
    </group>
  );
}
