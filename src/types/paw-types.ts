// PAW (Phased Atomic Weaver) Type Definitions
// Based on MGB-KTM-GUI-02 Technical Specification

export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface Voxel {
  i: number;
  j: number;
  k: number;
}

export interface Element {
  symbol: string;
  Z: number;
  A: number; // isotope mass number
}

export interface Blueprint {
  name: string;
  mass_kg: number;
  complexity: number; // 1..10 (affects fault chance)
  elements: Array<[string, number]>; // [symbol, proportion]
}

export interface PlaceReply {
  ok: boolean;
  placement_error_pm: number;
  msg: string;
}

export interface Telemetry {
  error_pm: number;
  epa_eV: number;
  temp_K: number;
  flux_ips: number;
  balance_B: number;
  interlocks_ok: boolean;
  class2: boolean;
  class3: boolean;
}

export interface PAWCapabilities {
  B_min: number;
  error_goal_pm: number;
  error_hard_pm: number;
  flux_max: number;
}

export class SafetyViolation extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SafetyViolation';
  }
}