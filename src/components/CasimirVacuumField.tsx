import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Sphere } from '@react-three/drei';

interface CasimirVacuumFieldProps {
  strength: number;
}

export function CasimirVacuumField({ strength }: CasimirVacuumFieldProps) {
  const particlesRef = useRef<THREE.Points>(null);
  const coreRef = useRef<THREE.Mesh>(null);
  
  // Create quantum vacuum particles
  const particleCount = 500;
  const particles = new Float32Array(particleCount * 3);
  
  for (let i = 0; i < particleCount * 3; i += 3) {
    const radius = 5 + Math.random() * 2;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.random() * Math.PI;
    
    particles[i] = radius * Math.sin(phi) * Math.cos(theta);
    particles[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
    particles[i + 2] = radius * Math.cos(phi);
  }
  
  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y += 0.0005;
      particlesRef.current.rotation.x += 0.0002;
      
      // Pulsing effect
      const pulse = Math.sin(state.clock.elapsedTime * 2) * 0.05 + 1;
      particlesRef.current.scale.setScalar(pulse * strength);
    }
    
    if (coreRef.current) {
      // Core pulsing
      const corePulse = Math.sin(state.clock.elapsedTime * 3) * 0.1 + 1;
      coreRef.current.scale.setScalar(corePulse * strength);
      
      // Rotation
      coreRef.current.rotation.x += 0.001;
      coreRef.current.rotation.y += 0.002;
    }
  });
  
  return (
    <group>
      {/* Quantum vacuum particles */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particleCount}
            array={particles}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.05}
          color="#00FF88"
          transparent
          opacity={0.6 * strength}
          sizeAttenuation={true}
          blending={THREE.AdditiveBlending}
        />
      </points>
      
      {/* Central Casimir core */}
      <Sphere ref={coreRef} args={[0.5, 32, 32]}>
        <meshStandardMaterial
          color="#00FF88"
          emissive="#00FF88"
          emissiveIntensity={2 * strength}
          transparent
          opacity={0.4 * strength}
        />
      </Sphere>
      
      {/* Casimir energy rings */}
      <group>
        {[1, 1.5, 2, 2.5].map((radius, idx) => (
          <mesh key={idx} rotation={[Math.PI / 2, 0, idx * Math.PI / 4]}>
            <torusGeometry args={[radius, 0.02, 16, 100]} />
            <meshStandardMaterial
              color="#00FF88"
              emissive="#00FF88"
              emissiveIntensity={1.5 * strength}
              transparent
              opacity={0.5 * strength}
            />
          </mesh>
        ))}
      </group>
      
      {/* Quantum flux lines */}
      {Array.from({ length: 12 }).map((_, idx) => {
        const angle = (idx / 12) * Math.PI * 2;
        const x = Math.cos(angle) * 3;
        const z = Math.sin(angle) * 3;
        
        return (
          <group key={idx}>
            <mesh position={[x, 0, z]} rotation={[0, angle, 0]}>
              <cylinderGeometry args={[0.01, 0.01, 6, 8]} />
              <meshStandardMaterial
                color="#00FF88"
                emissive="#00FF88"
                emissiveIntensity={1 * strength}
                transparent
                opacity={0.3 * strength}
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}
