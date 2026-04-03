/**
 * MarketNebula - Volumetric market data field surrounding the scene
 * Color and intensity shift with volatility, momentum, and coherence
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface MarketNebulaProps {
  volatility: number;   // 0-1
  momentum: number;     // can be negative
  coherence: number;    // 0-1
  hncFrequency: number; // Hz value
}

const nebulaVertexShader = `
  varying vec3 vPosition;
  varying vec3 vWorldNormal;

  void main() {
    vPosition = position;
    vWorldNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const nebulaFragmentShader = `
  uniform float uTime;
  uniform float uVolatility;
  uniform float uMomentum;
  uniform float uCoherence;
  uniform float uFrequency;

  varying vec3 vPosition;
  varying vec3 vWorldNormal;

  // 3D noise
  vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 permute(vec4 x) { return mod289(((x * 34.0) + 1.0) * x); }
  vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

  float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute(
      i.z + vec4(0.0, i1.z, i2.z, 1.0))
      + i.y + vec4(0.0, i1.y, i2.y, 1.0))
      + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0) * 2.0 + 1.0;
    vec4 s1 = floor(b1) * 2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }

  void main() {
    vec3 pos = normalize(vPosition);
    float freqMod = uFrequency / 432.0; // normalize around 432Hz
    float t = uTime * 0.03;

    // Multi-octave noise
    float n1 = snoise(pos * 1.5 * freqMod + t) * 0.5 + 0.5;
    float n2 = snoise(pos * 3.0 - t * 0.7) * 0.5 + 0.5;
    float n3 = snoise(pos * 5.0 + t * 0.5) * 0.5 + 0.5;

    float combined = n1 * 0.5 + n2 * 0.3 + n3 * 0.2;

    // Color channels mapped to market data
    float r = uVolatility * combined * 0.8;
    float g = max(uMomentum, 0.0) * n2 * 0.6;
    float b = uCoherence * (1.0 - combined * 0.3) * 0.7;

    // Base deep space tint
    vec3 color = vec3(r, g, b) + vec3(0.01, 0.02, 0.06);

    // Intensity modulation
    float intensity = 0.3 + combined * 0.7;
    color *= intensity;

    // Pulsing opacity
    float pulse = sin(uTime * 0.3) * 0.02 + sin(uTime * 0.7) * 0.01;
    float alpha = (0.04 + pulse + uVolatility * 0.06) * combined;

    // Fresnel-like edge brightening
    float fresnel = pow(1.0 - abs(dot(normalize(vWorldNormal), vec3(0.0, 0.0, 1.0))), 2.0);
    alpha *= (0.5 + fresnel * 1.5);

    gl_FragColor = vec4(color, alpha);
  }
`;

export function MarketNebula({
  volatility = 0.3,
  momentum = 0,
  coherence = 0.5,
  hncFrequency = 432,
}: MarketNebulaProps) {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uVolatility: { value: volatility },
    uMomentum: { value: momentum },
    uCoherence: { value: coherence },
    uFrequency: { value: hncFrequency },
  }), []);

  useFrame((state) => {
    if (!materialRef.current) return;
    const u = materialRef.current.uniforms;
    u.uTime.value = state.clock.elapsedTime;
    // Smooth interpolation for data-driven uniforms
    u.uVolatility.value = THREE.MathUtils.lerp(u.uVolatility.value, volatility, 0.03);
    u.uMomentum.value = THREE.MathUtils.lerp(u.uMomentum.value, Math.max(momentum, 0) / 100, 0.03);
    u.uCoherence.value = THREE.MathUtils.lerp(u.uCoherence.value, coherence, 0.03);
    u.uFrequency.value = THREE.MathUtils.lerp(u.uFrequency.value, hncFrequency, 0.03);
  });

  return (
    <mesh>
      <sphereGeometry args={[18, 48, 48]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={nebulaVertexShader}
        fragmentShader={nebulaFragmentShader}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        side={THREE.BackSide}
      />
    </mesh>
  );
}
