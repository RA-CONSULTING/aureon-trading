// PAW API Driver - Software mock of Phased Atomic Weaver API
// Implements: Init, Arm, Inject, Place, Pause, Abort, GetTelemetry

import { Element, Voxel, PlaceReply, Telemetry, PAWCapabilities, SafetyViolation } from '../types/paw-types';

export class PAWAPIDriver {
  private inited = false;
  private armed = false;
  private interlocks_ok = true;
  private temp_K = 2.4;
  private flux_ips = 0.0;
  private balance_B = 0.0;
  private error_pm = 0.0;
  private epa_eV = 0.0;
  private fault_bias = 0.0;
  private paused = false;
  private aborted = false;
  private last_place_t = 0.0;
  private rng_seed = 42;

  public caps: PAWCapabilities = {
    B_min: 0.6,
    error_goal_pm: 50.0,
    error_hard_pm: 200.0,
    flux_max: 2.0e6,
  };

  private random(): number {
    // Simple seeded random number generator
    this.rng_seed = (this.rng_seed * 9301 + 49297) % 233280;
    return this.rng_seed / 233280;
  }

  private gauss(mean: number, stddev: number): number {
    // Box-Muller transform for Gaussian distribution
    const u1 = this.random();
    const u2 = this.random();
    const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mean + stddev * z0;
  }

  Init(profile: string): [boolean, string] {
    this.inited = true;
    this.aborted = false;
    this.paused = false;
    this.temp_K = 2.0 + (this.random() - 0.5) * 0.3;
    return [true, `Profile '${profile}' loaded`];
  }

  Arm(balance_B: number, interlocks_ok: boolean): [boolean, string] {
    this.balance_B = balance_B;
    this.interlocks_ok = interlocks_ok;
    
    if (!this.inited) {
      return [false, "Weaver not initialized"];
    }
    if (!interlocks_ok) {
      return [false, "Interlocks not OK"];
    }
    if (balance_B < this.caps.B_min) {
      return [false, `Balance ${balance_B.toFixed(2)} below minimum ${this.caps.B_min}`];
    }
    
    this.armed = true;
    // Lower fault bias when balance is high
    this.fault_bias = Math.max(0.0, 1.0 - Math.min(balance_B, 2.0) / 2.0);
    return [true, "Armed"];
  }