/**
 * Light Path Tracer
 * Captures complete data flow for each decision cycle
 * Traces: Input Frequency → Prism Levels → Matrix Weights → Telescope Refractions → Final Action
 */

export interface LightPathNode {
  component: string;
  inputValue: number;
  outputValue: number;
  transformation: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

export interface LightPathTrace {
  traceId: string;
  startTime: number;
  endTime: number;
  nodes: LightPathNode[];
  inputFrequency: number;
  outputAction: 'BUY' | 'SELL' | 'HOLD';
  outputConfidence: number;
  alignmentScore: number;
  isValid: boolean;
  validationErrors: string[];
}

export interface LightPathStats {
  totalTraces: number;
  avgAlignmentScore: number;
  avgProcessingTime: number;
  successRate: number;
  componentHealth: Record<string, { successRate: number; avgLatency: number }>;
}

class LightPathTracerClass {
  private traces: LightPathTrace[] = [];
  private currentTrace: Partial<LightPathTrace> | null = null;
  private maxTraces = 50;
  private listeners: Set<(traces: LightPathTrace[]) => void> = new Set();

  startTrace(inputFrequency: number): string {
    const traceId = `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    this.currentTrace = {
      traceId,
      startTime: Date.now(),
      nodes: [],
      inputFrequency,
      isValid: true,
      validationErrors: []
    };

    return traceId;
  }

  addNode(
    component: string,
    inputValue: number,
    outputValue: number,
    transformation: string,
    metadata?: Record<string, any>
  ): void {
    if (!this.currentTrace) return;

    this.currentTrace.nodes = this.currentTrace.nodes || [];
    this.currentTrace.nodes.push({
      component,
      inputValue,
      outputValue,
      transformation,
      timestamp: Date.now(),
      metadata
    });
  }

  addValidationError(error: string): void {
    if (!this.currentTrace) return;
    this.currentTrace.isValid = false;
    this.currentTrace.validationErrors = this.currentTrace.validationErrors || [];
    this.currentTrace.validationErrors.push(error);
  }

  completeTrace(action: 'BUY' | 'SELL' | 'HOLD', confidence: number): LightPathTrace | null {
    if (!this.currentTrace) return null;

    const nodes = this.currentTrace.nodes || [];
    
    // Calculate alignment score based on how well components agree
    const alignmentScore = this.calculateAlignmentScore(nodes);

    const completedTrace: LightPathTrace = {
      traceId: this.currentTrace.traceId!,
      startTime: this.currentTrace.startTime!,
      endTime: Date.now(),
      nodes,
      inputFrequency: this.currentTrace.inputFrequency!,
      outputAction: action,
      outputConfidence: confidence,
      alignmentScore,
      isValid: this.currentTrace.isValid!,
      validationErrors: this.currentTrace.validationErrors || []
    };

    this.traces.push(completedTrace);
    
    // Keep only last N traces
    if (this.traces.length > this.maxTraces) {
      this.traces = this.traces.slice(-this.maxTraces);
    }

    this.currentTrace = null;
    this.notifyListeners();

    return completedTrace;
  }

  private calculateAlignmentScore(nodes: LightPathNode[]): number {
    if (nodes.length < 2) return 1;

    // Calculate how consistent the transformations are
    let totalAlignment = 0;
    let comparisons = 0;

    for (let i = 1; i < nodes.length; i++) {
      const prev = nodes[i - 1];
      const curr = nodes[i];
      
      // Check if output of previous matches input of current (with tolerance)
      const continuity = 1 - Math.min(1, Math.abs(prev.outputValue - curr.inputValue));
      
      // Check if transformation direction is consistent
      const prevDirection = Math.sign(prev.outputValue - prev.inputValue);
      const currDirection = Math.sign(curr.outputValue - curr.inputValue);
      const directionAlign = prevDirection === currDirection ? 1 : prevDirection === 0 || currDirection === 0 ? 0.5 : 0;

      totalAlignment += (continuity * 0.6 + directionAlign * 0.4);
      comparisons++;
    }

    return comparisons > 0 ? totalAlignment / comparisons : 1;
  }

  getTraces(): LightPathTrace[] {
    return [...this.traces];
  }

  getRecentTraces(count: number = 10): LightPathTrace[] {
    return this.traces.slice(-count);
  }

  getStats(): LightPathStats {
    if (this.traces.length === 0) {
      return {
        totalTraces: 0,
        avgAlignmentScore: 0,
        avgProcessingTime: 0,
        successRate: 0,
        componentHealth: {}
      };
    }

    const validTraces = this.traces.filter(t => t.isValid);
    const avgAlignmentScore = this.traces.reduce((sum, t) => sum + t.alignmentScore, 0) / this.traces.length;
    const avgProcessingTime = this.traces.reduce((sum, t) => sum + (t.endTime - t.startTime), 0) / this.traces.length;
    const successRate = validTraces.length / this.traces.length;

    // Component health stats
    const componentHealth: Record<string, { successRate: number; avgLatency: number }> = {};
    const componentStats: Record<string, { successes: number; total: number; totalLatency: number }> = {};

    for (const trace of this.traces) {
      let prevTime = trace.startTime;
      for (const node of trace.nodes) {
        if (!componentStats[node.component]) {
          componentStats[node.component] = { successes: 0, total: 0, totalLatency: 0 };
        }
        componentStats[node.component].total++;
        componentStats[node.component].totalLatency += (node.timestamp - prevTime);
        if (trace.isValid) {
          componentStats[node.component].successes++;
        }
        prevTime = node.timestamp;
      }
    }

    for (const [component, stats] of Object.entries(componentStats)) {
      componentHealth[component] = {
        successRate: stats.successes / stats.total,
        avgLatency: stats.totalLatency / stats.total
      };
    }

    return {
      totalTraces: this.traces.length,
      avgAlignmentScore,
      avgProcessingTime,
      successRate,
      componentHealth
    };
  }

  subscribe(listener: (traces: LightPathTrace[]) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.traces));
  }

  clear(): void {
    this.traces = [];
    this.currentTrace = null;
    this.notifyListeners();
  }
}

export const lightPathTracer = new LightPathTracerClass();
