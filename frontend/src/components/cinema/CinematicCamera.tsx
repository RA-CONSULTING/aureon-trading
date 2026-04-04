/**
 * CinematicCamera - Intelligent camera director
 *
 * Cycles through cinematic scenes with smooth spherical coordinate interpolation.
 * Responds to system events: trades trigger gateway focus, coherence spikes
 * trigger dramatic push-ins, fear surges trigger pull-backs.
 * User mouse interaction pauses auto-direction for 5 seconds.
 */

import { useRef, useEffect, useCallback } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import type { NarratorEventType } from './NarratorEngine';

// Gateway positions for camera focus targets
const GATEWAY_TARGETS: Record<string, THREE.Vector3> = {
  kraken: new THREE.Vector3(-10.4, 0, -6),
  binance: new THREE.Vector3(10.4, 0, -6),
  capital: new THREE.Vector3(0, 0, 12),
};

interface CameraScene {
  name: string;
  radius: number;
  phi: number;      // polar angle (0 = top, PI = bottom)
  thetaSpeed: number; // orbit speed (rad/s)
  fov: number;
  lookAt: THREE.Vector3;
  duration: number;  // ms
}

const ORIGIN = new THREE.Vector3(0, 0, 0);

const SCENES: CameraScene[] = [
  { name: 'wide_orbit', radius: 28, phi: 1.1, thetaSpeed: 0.08, fov: 55, lookAt: ORIGIN, duration: 25000 },
  { name: 'low_sweep', radius: 20, phi: 1.45, thetaSpeed: 0.06, fov: 50, lookAt: ORIGIN, duration: 15000 },
  { name: 'queen_closeup', radius: 12, phi: 1.3, thetaSpeed: 0.04, fov: 45, lookAt: ORIGIN, duration: 10000 },
  { name: 'overview', radius: 24, phi: 0.6, thetaSpeed: 0.05, fov: 58, lookAt: ORIGIN, duration: 12000 },
  { name: 'wide_orbit_alt', radius: 30, phi: 1.0, thetaSpeed: -0.06, fov: 52, lookAt: ORIGIN, duration: 20000 },
  { name: 'low_sweep_alt', radius: 18, phi: 1.5, thetaSpeed: -0.08, fov: 48, lookAt: ORIGIN, duration: 12000 },
];

interface CinematicCameraProps {
  volatility: number;
  activeEvent?: NarratorEventType | null;
  tradeExchange?: string;
}

export function CinematicCamera({
  volatility = 0,
  activeEvent = null,
  tradeExchange,
}: CinematicCameraProps) {
  const controlsRef = useRef<any>(null);
  const { camera } = useThree();

  // Camera state
  const theta = useRef(0);
  const currentRadius = useRef(28);
  const currentPhi = useRef(1.1);
  const currentFov = useRef(55);
  const currentLookAt = useRef(new THREE.Vector3(0, 0, 0));
  const targetRadius = useRef(28);
  const targetPhi = useRef(1.1);
  const targetFov = useRef(55);
  const targetLookAt = useRef(new THREE.Vector3(0, 0, 0));
  const thetaSpeed = useRef(0.08);

  // Scene cycling
  const sceneIndex = useRef(0);
  const sceneStartTime = useRef(Date.now());
  const sceneDuration = useRef(SCENES[0].duration);

  // Event interrupt
  const eventOverrideUntil = useRef(0);
  const lastEventRef = useRef<NarratorEventType | null>(null);

  // User interaction pause
  const userInteractedAt = useRef(0);
  const USER_PAUSE_MS = 5000;

  // Initialize camera
  useEffect(() => {
    camera.position.set(0, 10, 28);
    const cam = camera as THREE.PerspectiveCamera;
    cam.fov = 55;
    cam.near = 0.1;
    cam.far = 200;
    cam.updateProjectionMatrix();
  }, [camera]);

  // Transition to a scene
  const transitionTo = useCallback((scene: CameraScene) => {
    targetRadius.current = scene.radius;
    targetPhi.current = scene.phi;
    targetFov.current = scene.fov;
    targetLookAt.current.copy(scene.lookAt);
    thetaSpeed.current = scene.thetaSpeed;
    sceneDuration.current = scene.duration;
    sceneStartTime.current = Date.now();
  }, []);

  // Respond to narrator events
  useEffect(() => {
    if (!activeEvent || activeEvent === lastEventRef.current) return;
    lastEventRef.current = activeEvent;

    const now = Date.now();

    switch (activeEvent) {
      case 'trade_buy':
      case 'trade_sell': {
        // Focus on the exchange gateway
        const gateway = GATEWAY_TARGETS[tradeExchange || 'kraken'] || GATEWAY_TARGETS.kraken;
        targetLookAt.current.copy(gateway);
        targetRadius.current = 18;
        targetPhi.current = 1.2;
        targetFov.current = 48;
        thetaSpeed.current = 0.02;
        eventOverrideUntil.current = now + 6000;
        break;
      }
      case 'coherence_spike':
      case 'level_up': {
        // Dramatic push toward Queen
        targetRadius.current = 10;
        targetPhi.current = 1.25;
        targetFov.current = 42;
        targetLookAt.current.copy(ORIGIN);
        thetaSpeed.current = 0.03;
        eventOverrideUntil.current = now + 5000;
        break;
      }
      case 'fear_surge':
      case 'drawdown': {
        // Tension pull-back
        targetRadius.current = 35;
        targetPhi.current = 0.9;
        targetFov.current = 62;
        targetLookAt.current.copy(ORIGIN);
        thetaSpeed.current = 0.04;
        eventOverrideUntil.current = now + 6000;
        break;
      }
      case 'mood_shift':
      case 'market_shift': {
        // Gentle overview
        targetRadius.current = 24;
        targetPhi.current = 0.7;
        targetFov.current = 56;
        targetLookAt.current.copy(ORIGIN);
        thetaSpeed.current = 0.05;
        eventOverrideUntil.current = now + 5000;
        break;
      }
      default:
        break;
    }
  }, [activeEvent, tradeExchange]);

  // Detect user interaction
  const onUserInteract = useCallback(() => {
    userInteractedAt.current = Date.now();
  }, []);

  useEffect(() => {
    const el = document.querySelector('canvas');
    if (el) {
      el.addEventListener('pointerdown', onUserInteract);
      el.addEventListener('wheel', onUserInteract);
    }
    return () => {
      if (el) {
        el.removeEventListener('pointerdown', onUserInteract);
        el.removeEventListener('wheel', onUserInteract);
      }
    };
  }, [onUserInteract]);

  useFrame((_, delta) => {
    const cam = camera as THREE.PerspectiveCamera;
    const now = Date.now();
    const userPaused = (now - userInteractedAt.current) < USER_PAUSE_MS;

    // If user is interacting, let OrbitControls handle it
    if (userPaused) {
      if (controlsRef.current) {
        controlsRef.current.autoRotate = false;
      }
      return;
    }

    if (controlsRef.current) {
      controlsRef.current.autoRotate = false;
    }

    // Scene cycling (only when not in event override)
    if (now > eventOverrideUntil.current) {
      const elapsed = now - sceneStartTime.current;
      if (elapsed > sceneDuration.current) {
        sceneIndex.current = (sceneIndex.current + 1) % SCENES.length;
        transitionTo(SCENES[sceneIndex.current]);
      }
    }

    // Volatility affects FOV
    const volFov = targetFov.current + volatility * 8;

    // Smooth interpolation (cinematic speed)
    const lerpRate = 0.012;
    currentRadius.current = THREE.MathUtils.lerp(currentRadius.current, targetRadius.current, lerpRate);
    currentPhi.current = THREE.MathUtils.lerp(currentPhi.current, targetPhi.current, lerpRate);
    currentFov.current = THREE.MathUtils.lerp(currentFov.current, volFov, lerpRate);
    currentLookAt.current.lerp(targetLookAt.current, lerpRate);

    // Advance orbit angle
    theta.current += delta * thetaSpeed.current;

    // Convert spherical to cartesian
    const r = currentRadius.current;
    const phi = currentPhi.current;
    const th = theta.current;

    cam.position.set(
      r * Math.sin(phi) * Math.cos(th),
      r * Math.cos(phi),
      r * Math.sin(phi) * Math.sin(th)
    );

    cam.lookAt(currentLookAt.current);
    cam.fov = currentFov.current;
    cam.updateProjectionMatrix();

    // Sync orbit controls target (so manual interaction works smoothly)
    if (controlsRef.current) {
      controlsRef.current.target.copy(currentLookAt.current);
      controlsRef.current.update();
    }
  });

  return (
    <OrbitControls
      ref={controlsRef}
      autoRotate={false}
      enableDamping
      dampingFactor={0.05}
      minDistance={6}
      maxDistance={60}
      maxPolarAngle={Math.PI * 0.85}
      minPolarAngle={Math.PI * 0.1}
      enablePan={false}
    />
  );
}
