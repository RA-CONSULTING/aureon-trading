/**
 * CinematicCamera - Auto-orbiting camera with event-driven movements
 * Slow majestic sweeps with dramatic responses to trade events
 */

import { useRef, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

interface CinematicCameraProps {
  volatility: number;      // 0-1, affects FOV tension
  tradeEvent?: {           // triggers camera movement
    timestamp: number;
    side: string;
  } | null;
}

export function CinematicCamera({ volatility = 0, tradeEvent = null }: CinematicCameraProps) {
  const controlsRef = useRef<any>(null);
  const { camera } = useThree();
  const targetFov = useRef(55);
  const lastTradeTimestamp = useRef(0);
  const dollyProgress = useRef(0);
  const isDollying = useRef(false);

  // Set initial camera position
  useEffect(() => {
    camera.position.set(0, 8, 25);
    (camera as THREE.PerspectiveCamera).fov = 55;
    (camera as THREE.PerspectiveCamera).near = 0.1;
    (camera as THREE.PerspectiveCamera).far = 200;
    camera.updateProjectionMatrix();
  }, [camera]);

  // Respond to trade events
  useEffect(() => {
    if (tradeEvent && tradeEvent.timestamp !== lastTradeTimestamp.current) {
      lastTradeTimestamp.current = tradeEvent.timestamp;
      isDollying.current = true;
      dollyProgress.current = 0;
    }
  }, [tradeEvent]);

  useFrame((_, delta) => {
    const cam = camera as THREE.PerspectiveCamera;

    // Smooth FOV interpolation based on volatility
    // Higher volatility = wider FOV for tension
    targetFov.current = 50 + volatility * 15;
    cam.fov = THREE.MathUtils.lerp(cam.fov, targetFov.current, 0.02);
    cam.updateProjectionMatrix();

    // Dolly effect on trade events
    if (isDollying.current) {
      dollyProgress.current += delta * 1.5;
      if (dollyProgress.current < 1) {
        // Quick zoom in then ease back out
        const t = dollyProgress.current;
        const ease = t < 0.3
          ? t / 0.3                        // zoom in
          : 1 - (t - 0.3) / 0.7;          // ease back
        const dollyAmount = ease * 3;
        cam.fov = targetFov.current - dollyAmount * 5;
        cam.updateProjectionMatrix();
      } else {
        isDollying.current = false;
      }
    }
  });

  return (
    <OrbitControls
      ref={controlsRef}
      autoRotate
      autoRotateSpeed={0.3}
      enableDamping
      dampingFactor={0.05}
      minDistance={10}
      maxDistance={50}
      maxPolarAngle={Math.PI * 0.8}
      minPolarAngle={Math.PI * 0.15}
      enablePan={false}
    />
  );
}
