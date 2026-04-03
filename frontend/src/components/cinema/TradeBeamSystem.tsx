/**
 * TradeBeamSystem - Energy beams that fire from Queen to Exchange Gateways on trade execution
 * Curved tube geometry with animated progress and particle trails
 */

import { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface TradeData {
  time: string;
  side: string;
  symbol: string;
  quantity: number;
  pnl: number;
  exchange?: string;
}

interface TradeBeamSystemProps {
  recentTrades: TradeData[];
}

// Gateway positions (matching ExchangeGateways.tsx)
const GATEWAY_POSITIONS: Record<string, THREE.Vector3> = {
  kraken: new THREE.Vector3(-10.4, 0, -6),
  binance: new THREE.Vector3(10.4, 0, -6),
  capital: new THREE.Vector3(0, 0, 12),
};

const ORIGIN = new THREE.Vector3(0, 0, 0);

interface ActiveBeam {
  id: string;
  progress: number;
  curve: THREE.CatmullRomCurve3;
  color: THREE.Color;
  opacity: number;
  thickness: number;
  particlePositions: THREE.Vector3[];
}

function BeamMesh({ beam }: { beam: ActiveBeam }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const particlesRef = useRef<THREE.Points>(null);

  const tubeGeometry = useMemo(() => {
    const visibleCurve = new THREE.CatmullRomCurve3(
      beam.curve.getPoints(50).slice(0, Math.floor(beam.progress * 50) + 1)
    );
    if (visibleCurve.points.length < 2) return null;
    return new THREE.TubeGeometry(visibleCurve, 32, beam.thickness, 8, false);
  }, [beam.curve, beam.progress, beam.thickness]);

  // Particle trail at beam head
  const particleGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const positions: number[] = [];
    const headPoint = beam.curve.getPoint(Math.min(beam.progress, 1));

    for (let i = 0; i < 15; i++) {
      positions.push(
        headPoint.x + (Math.random() - 0.5) * 0.8,
        headPoint.y + (Math.random() - 0.5) * 0.8,
        headPoint.z + (Math.random() - 0.5) * 0.8
      );
    }
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    return geo;
  }, [beam.curve, beam.progress]);

  if (!tubeGeometry) return null;

  return (
    <group>
      <mesh ref={meshRef} geometry={tubeGeometry}>
        <meshBasicMaterial
          color={beam.color}
          transparent
          opacity={beam.opacity}
          depthWrite={false}
        />
      </mesh>
      <points ref={particlesRef} geometry={particleGeometry}>
        <pointsMaterial
          color={beam.color}
          size={0.15}
          transparent
          opacity={beam.opacity * 0.8}
          depthWrite={false}
          sizeAttenuation
        />
      </points>
    </group>
  );
}

export function TradeBeamSystem({ recentTrades = [] }: TradeBeamSystemProps) {
  const [activeBeams, setActiveBeams] = useState<ActiveBeam[]>([]);
  const processedTradesRef = useRef<Set<string>>(new Set());

  // Detect new trades and spawn beams
  useEffect(() => {
    if (recentTrades.length === 0) return;

    const newBeams: ActiveBeam[] = [];

    for (const trade of recentTrades.slice(0, 5)) {
      const tradeId = `${trade.time}-${trade.symbol}-${trade.side}`;
      if (processedTradesRef.current.has(tradeId)) continue;
      processedTradesRef.current.add(tradeId);

      // Keep set from growing indefinitely
      if (processedTradesRef.current.size > 100) {
        const entries = Array.from(processedTradesRef.current);
        processedTradesRef.current = new Set(entries.slice(-50));
      }

      // Determine target gateway
      const exchange = (trade.exchange || 'kraken').toLowerCase();
      const target = GATEWAY_POSITIONS[exchange] || GATEWAY_POSITIONS.kraken;

      // Create curved path from Queen to Gateway
      const midPoint = new THREE.Vector3(
        (ORIGIN.x + target.x) / 2 + (Math.random() - 0.5) * 4,
        3 + Math.random() * 3,
        (ORIGIN.z + target.z) / 2 + (Math.random() - 0.5) * 4
      );

      const curve = new THREE.CatmullRomCurve3([
        ORIGIN.clone(),
        midPoint,
        target.clone(),
      ]);

      const isBuy = trade.side.toUpperCase().includes('BUY') || trade.side.toUpperCase().includes('LONG');
      const color = isBuy
        ? new THREE.Color(0.0, 1.0, 0.5)
        : new THREE.Color(1.0, 0.2, 0.4);

      // Larger trades = thicker beams
      const notional = Math.abs(trade.quantity * (trade.pnl || 1));
      const thickness = Math.min(0.02 + notional * 0.001, 0.12);

      newBeams.push({
        id: tradeId,
        progress: 0,
        curve,
        color,
        opacity: 0.9,
        thickness,
        particlePositions: [],
      });
    }

    if (newBeams.length > 0) {
      setActiveBeams(prev => [...prev, ...newBeams].slice(-8)); // Max 8 active beams
    }
  }, [recentTrades]);

  // Animate beams
  useFrame((_, delta) => {
    setActiveBeams(prev => {
      let changed = false;
      const updated = prev.map(beam => {
        if (beam.progress < 1) {
          changed = true;
          return { ...beam, progress: Math.min(beam.progress + delta * 0.8, 1) };
        } else if (beam.opacity > 0) {
          changed = true;
          return { ...beam, opacity: Math.max(beam.opacity - delta * 0.4, 0) };
        }
        return beam;
      }).filter(beam => beam.opacity > 0.01);

      return changed ? updated : prev;
    });
  });

  return (
    <group>
      {activeBeams.map(beam => (
        <BeamMesh key={beam.id} beam={beam} />
      ))}
    </group>
  );
}
