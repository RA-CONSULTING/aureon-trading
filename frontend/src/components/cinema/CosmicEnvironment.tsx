/**
 * CosmicEnvironment - Deep space backdrop for the cinematic observatory
 * Starfield, floating dust particles, and nebula fog
 */

import { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Stars } from '@react-three/drei';
import * as THREE from 'three';

// Floating dust motes - instanced for performance
function DustParticles({ count = 2000 }: { count?: number }) {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  const particles = useMemo(() => {
    const data = [];
    for (let i = 0; i < count; i++) {
      data.push({
        position: new THREE.Vector3(
          (Math.random() - 0.5) * 80,
          (Math.random() - 0.5) * 80,
          (Math.random() - 0.5) * 80
        ),
        speed: 0.01 + Math.random() * 0.03,
        offset: Math.random() * Math.PI * 2,
        scale: 0.02 + Math.random() * 0.06,
      });
    }
    return data;
  }, [count]);

  useFrame((state) => {
    if (!meshRef.current) return;
    const t = state.clock.elapsedTime;

    for (let i = 0; i < count; i++) {
      const p = particles[i];
      dummy.position.set(
        p.position.x + Math.sin(t * p.speed + p.offset) * 2,
        p.position.y + Math.cos(t * p.speed * 0.7 + p.offset) * 1.5,
        p.position.z + Math.sin(t * p.speed * 0.5 + p.offset * 2) * 2
      );
      dummy.scale.setScalar(p.scale * (0.8 + Math.sin(t * 0.5 + p.offset) * 0.2));
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    }
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, count]}>
      <sphereGeometry args={[1, 4, 4]} />
      <meshBasicMaterial color="#4488cc" transparent opacity={0.3} />
    </instancedMesh>
  );
}

// Nebula backdrop sphere with animated shader
const nebulaVertexShader = `
  varying vec3 vPosition;
  varying vec2 vUv;
  void main() {
    vPosition = position;
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const nebulaFragmentShader = `
  uniform float uTime;
  varying vec3 vPosition;
  varying vec2 vUv;

  // Simplex-style noise
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
    vec3 pos = normalize(vPosition) * 2.0;
    float t = uTime * 0.02;

    float n1 = snoise(pos + t) * 0.5 + 0.5;
    float n2 = snoise(pos * 2.0 - t * 0.5) * 0.5 + 0.5;
    float n3 = snoise(pos * 4.0 + t * 0.3) * 0.5 + 0.5;

    // Deep space colors: dark blue, purple, subtle cyan
    vec3 color1 = vec3(0.02, 0.01, 0.08); // deep purple
    vec3 color2 = vec3(0.01, 0.03, 0.12); // deep blue
    vec3 color3 = vec3(0.05, 0.02, 0.10); // midnight violet

    vec3 color = mix(color1, color2, n1);
    color = mix(color, color3, n2 * 0.5);
    color += vec3(0.0, 0.02, 0.05) * n3; // subtle cyan highlights

    float alpha = 0.6 + n1 * 0.3;

    gl_FragColor = vec4(color, alpha);
  }
`;

function NebulaBackdrop() {
  const materialRef = useRef<THREE.ShaderMaterial>(null);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
  }), []);

  useFrame((state) => {
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
    }
  });

  return (
    <mesh>
      <sphereGeometry args={[60, 32, 32]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={nebulaVertexShader}
        fragmentShader={nebulaFragmentShader}
        uniforms={uniforms}
        side={THREE.BackSide}
        transparent
        depthWrite={false}
      />
    </mesh>
  );
}

// Scene fog setup
function SceneFog() {
  const { scene } = useThree();
  useMemo(() => {
    scene.fog = new THREE.FogExp2('#000011', 0.008);
    scene.background = new THREE.Color('#000005');
  }, [scene]);
  return null;
}

export function CosmicEnvironment() {
  return (
    <>
      <SceneFog />
      <Stars
        radius={100}
        depth={80}
        count={6000}
        factor={4}
        saturation={0.2}
        fade
        speed={0.3}
      />
      <NebulaBackdrop />
      <DustParticles count={1500} />
      <ambientLight intensity={0.05} color="#4466aa" />
    </>
  );
}
