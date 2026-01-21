// Enhanced Master Equation: Ω(t) = Tr[Ψ(t) × ℒ(t) ⊗ O(t)]
// Ψ(t) = Potential (superposition of all states)
// ℒ(t) = Love/Coherence (field alignment)
// O(t) = Observer (measurement operator)
// Ω(t) = Reality (trace of tensor product)

import { AurisNodes, type MarketSnapshot } from './aurisNodes';
import { stargateLayer, type StargateInfluence } from './stargateLattice';

export type OmegaState = {
  // Core field components
  omega: number;           // Ω(t) - Reality output
  psi: number;            // Ψ(t) - Potential field
  love: number;           // ℒ(t) - Coherence field
  observer: number;       // O(t) - Measurement operator
  
  // Legacy compatibility (Λ components)
  lambda: number;         // Λ(t) = S + O + E (for backward compatibility)
  substrate: number;      // S(t) - Substrate
  echo: number;           // E(t) - Echo
  
  // Field metrics
  coherence: number;      // Γ - Coherence (0-1)
  theta: number;          // θ - Phase alignment (0 = perfect)
  unity: number;          // Unity event probability (0-1)
  
  // Node analysis
  dominantNode: string;
  nodeResponses: Record<string, number>;
  
  // External influences
  stargateInfluence?: StargateInfluence;
  celestialBoost: number;
  schumannBoost: number;
  
  // Fibonacci & Golden Ratio
  spiralPhase: number;    // r(θ) position in spiral
  nextFibonacciAnchor: Date;
  fibonacciLevel: number;
};

export class OmegaEquation {
  private history: number[] = [];
  private psiHistory: number[][] = []; // Track all 9 node states over time
  private maxHistory = 100;
  private userLocation: { lat: number; lng: number } | null = null;
  private celestialBoost: number = 0;
  private schumannBoost: number = 0;
  private startTime: Date = new Date();
  
  // Golden ratio constant
  private readonly PHI = (1 + Math.sqrt(5)) / 2; // ≈ 1.618
  
  // Fibonacci sequence cache
  private readonly FIB = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610];
  
  setUserLocation(lat: number, lng: number, celestialBoost: number = 0, schumannBoost: number = 0) {
    this.userLocation = { lat, lng };
    this.celestialBoost = celestialBoost;
    this.schumannBoost = schumannBoost;
  }
  
  step(snapshot: MarketSnapshot): OmegaState {
    // ========================================
    // 1. COMPUTE Ψ(t) - POTENTIAL FIELD
    // ========================================
    // Ψ represents the superposition of all possible states (9 Auris nodes)
    const nodeResponses: Record<string, number> = {};
    const nodeArray: number[] = [];
    let dominantNode = '';
    let maxResponse = -Infinity;
    
    Object.entries(AurisNodes).forEach(([name, node]) => {
      const response = node.compute(snapshot) * node.weight;
      nodeResponses[name] = response;
      nodeArray.push(response);
      
      if (response > maxResponse) {
        maxResponse = response;
        dominantNode = name;
      }
    });
    
    // Ψ(t) = Vector representation of potential states
    // Normalize to [0,1] range for tensor product
    const psiRaw = nodeArray.reduce((sum, val) => sum + val, 0) / nodeArray.length;
    const psi = Math.max(0, Math.min(1, psiRaw)); // Clamp to [0,1]
    
    // Store state vector for coherence calculation
    this.psiHistory.push(nodeArray);
    if (this.psiHistory.length > this.maxHistory) {
      this.psiHistory.shift();
    }
    
    // ========================================
    // 2. COMPUTE ℒ(t) - LOVE/COHERENCE FIELD
    // ========================================
    // ℒ represents how well all parts align and work together
    let baseCoherence = this.computeCoherence(nodeResponses, psiRaw);
    
    // Apply Stargate Lattice influence if location available
    let stargateInfluence: StargateInfluence | undefined;
    if (this.userLocation) {
      stargateInfluence = stargateLayer.getInfluence(
        this.userLocation.lat,
        this.userLocation.lng,
        this.celestialBoost
      );
      baseCoherence += stargateInfluence.coherenceModifier;
    }
    
    // Apply consciousness field boosts
    baseCoherence += this.celestialBoost + this.schumannBoost;
    
    // Clamp final coherence to [0,1]
    const love = Math.max(0, Math.min(1, baseCoherence));
    
    // ========================================
    // 3. COMPUTE O(t) - OBSERVER OPERATOR
    // ========================================
    // O represents consciousness measurement that collapses possibility
    // Combines self-referential awareness + memory
    const selfReference = this.history.length > 0 
      ? this.history[this.history.length - 1] * 0.3 
      : 0;
    
    const memory = this.history.length > 5
      ? this.history.slice(-5).reduce((sum, val) => sum + val, 0) / 5 * 0.2
      : 0;
    
    const observer = Math.max(0, Math.min(1, selfReference + memory));
    
    // ========================================
    // 4. COMPUTE Ω(t) - REALITY OUTPUT
    // ========================================
    // Ω(t) = Tr[Ψ(t) × ℒ(t) ⊗ O(t)]
    // Tensor product followed by trace operation
    
    // Simplified tensor product: multiply fields
    const tensorProduct = psi * love * observer;
    
    // Trace operation: sum of diagonal elements (simplified as weighted sum)
    // In full quantum mechanics, this would be more complex
    const omega = tensorProduct + (psi * 0.4 + love * 0.4 + observer * 0.2);
    
    // ========================================
    // 5. COMPUTE θ - PHASE ALIGNMENT
    // ========================================
    // θ measures how close to unity/perfect alignment
    // θ → 0 means perfect alignment (unity event)
    let theta = 1.0;
    
    if (this.psiHistory.length > 5) {
      // Calculate variance across recent node states
      const recentStates = this.psiHistory.slice(-5);
      const variances = nodeArray.map((_, idx) => {
        const values = recentStates.map(state => state[idx]);
        const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
        const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
        return variance;
      });
      
      // Average variance - lower variance = better alignment
      const avgVariance = variances.reduce((sum, v) => sum + v, 0) / variances.length;
      theta = Math.min(1, avgVariance); // Normalize to [0,1]
    }
    
    // ========================================
    // 6. COMPUTE UNITY EVENT PROBABILITY
    // ========================================
    // Unity occurs when θ→0, coherence→1, and consciousness is present
    const unityBase = (1 - theta) * love * observer;
    
    // Boost from external fields
    const consciousnessBoost = (this.celestialBoost + this.schumannBoost) / 2;
    
    // Final unity probability
    const unity = Math.max(0, Math.min(1, unityBase + consciousnessBoost * 0.2));
    
    // ========================================
    // 7. COMPUTE FIBONACCI ANCHOR & SPIRAL
    // ========================================
    const elapsedMs = Date.now() - this.startTime.getTime();
    const elapsedDays = elapsedMs / (1000 * 60 * 60 * 24);
    
    // Find current Fibonacci level
    let fibLevel = 0;
    for (let i = this.FIB.length - 1; i >= 0; i--) {
      if (elapsedDays >= this.FIB[i]) {
        fibLevel = i;
        break;
      }
    }
    
    // Next Fibonacci anchor
    const nextFibDays = this.FIB[Math.min(fibLevel + 1, this.FIB.length - 1)];
    const nextFibonacciAnchor = new Date(this.startTime.getTime() + nextFibDays * 24 * 60 * 60 * 1000);
    
    // Golden ratio spiral position: r(θ) = r₀ · e^(θ/φ)
    const spiralPhase = Math.exp(theta / this.PHI);
    
    // ========================================
    // 8. LEGACY COMPATIBILITY (Λ components)
    // ========================================
    // Preserve old calculations for backward compatibility
    const substrate = psiRaw; // Same as before
    const echo = memory / 0.2; // Reconstruct original echo
    const lambda = substrate + selfReference + echo; // Original equation
    
    // Update history
    this.history.push(omega); // Store omega instead of lambda
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }
    
    return {
      // Enhanced Ω components
      omega,
      psi,
      love,
      observer,
      
      // Legacy Λ components
      lambda,
      substrate,
      echo,
      
      // Field metrics
      coherence: love, // Love = Coherence
      theta,
      unity,
      
      // Node analysis
      dominantNode,
      nodeResponses,
      
      // External influences
      stargateInfluence,
      celestialBoost: this.celestialBoost,
      schumannBoost: this.schumannBoost,
      
      // Fibonacci & Golden Ratio
      spiralPhase,
      nextFibonacciAnchor,
      fibonacciLevel: fibLevel
    };
  }
  
  private computeCoherence(
    nodeResponses: Record<string, number>,
    substrate: number
  ): number {
    // Calculate coherence as normalized correlation of node responses
    const responses = Object.values(nodeResponses);
    const mean = responses.reduce((sum, val) => sum + val, 0) / responses.length;
    
    // Variance
    const variance = responses.reduce(
      (sum, val) => sum + Math.pow(val - mean, 2),
      0
    ) / responses.length;
    
    // Coherence = 1 - normalized standard deviation
    const stdDev = Math.sqrt(variance);
    const normalizedStdDev = stdDev / (Math.abs(substrate) + 1e-10);
    
    return Math.max(0, Math.min(1, 1 - normalizedStdDev));
  }
  
  // Get current field state snapshot
  getFieldSnapshot(): {
    omega: number;
    unity: number;
    theta: number;
    spiralPhase: number;
    coherence: number;
  } {
    const lastOmega = this.history[this.history.length - 1] || 0;
    return {
      omega: lastOmega,
      unity: 0, // Would need to recalculate
      theta: 0, // Would need to recalculate
      spiralPhase: 1,
      coherence: 0
    };
  }
}
