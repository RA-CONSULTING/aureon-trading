// PAW API Driver - Complete implementation
import { Element, Voxel, PlaceReply, Telemetry, PAWCapabilities } from '../types/paw-types';

export class PAWAPIDriver {
  protected inited = false;
  protected armed = false;
  protected interlocks_ok = true;
  protected temp_K = 2.4;
  protected flux_ips = 0.0;
  protected balance_B = 0.0;
  protected error_pm = 0.0;
  protected epa_eV = 0.0;
  protected fault_bias = 0.0;
  protected paused = false;
  protected aborted = false;
  protected last_place_t = 0.0;
  protected rng_seed = 42;

  public caps: PAWCapabilities = {
    B_min: 0.6,
    error_goal_pm: 50.0,
    error_hard_pm: 200.0,
    flux_max: 2.0e6,
  };

  protected random(): number {
    this.rng_seed = (this.rng_seed * 9301 + 49297) % 233280;
    return this.rng_seed / 233280;
  }

  protected gauss(mean: number, stddev: number): number {
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
    
    if (!this.inited) return [false, "Weaver not initialized"];
    if (!interlocks_ok) return [false, "Interlocks not OK"];
    if (balance_B < this.caps.B_min) {
      return [false, `Balance ${balance_B.toFixed(2)} below minimum ${this.caps.B_min}`];
    }
    
    this.armed = true;
    this.fault_bias = Math.max(0.0, 1.0 - Math.min(balance_B, 2.0) / 2.0);
    return [true, "Armed"];
  }

  Inject(elem: Element, flux_ips: number): [boolean, string] {
    if (!this.armed) return [false, "Not armed"];
    this.flux_ips = Math.min(flux_ips, this.caps.flux_max);
    return [true, `Injecting ${elem.symbol} at ${this.flux_ips.toExponential(2)} ips`];
  }

  Place(voxel: Voxel, elem: Element, energy_eV: number, complexity: number): PlaceReply {
    if (!this.armed || this.paused || this.aborted) {
      return { ok: false, placement_error_pm: this.error_pm, msg: "Not ready" };
    }

    const base_err = 80 + 10 * complexity;
    const B = Math.max(0.0, this.balance_B);
    const scale = Math.max(0.35, 1.4 - 0.6 * Math.min(B, 2.0));
    const noise = this.gauss(0.0, 8.0 + 2.0 * complexity);
    const drift = 3.0 * Math.sin(Date.now() * 0.0009);
    
    this.error_pm = Math.max(0.0, base_err * scale + noise + drift);
    this.epa_eV = Math.max(0.1, 10 + 1.5 * complexity - 3.0 * Math.min(B, 2.0));
    this.temp_K = Math.max(1.6, Math.min(4.0, 
      this.temp_K + 0.002 * this.flux_ips / 1e6 - 0.01));

    let class2 = false;
    let class3 = false;
    
    if (this.error_pm > this.caps.error_hard_pm || this.temp_K > 3.8) {
      class3 = true;
    } else if (this.error_pm > this.caps.error_goal_pm * 1.5 || this.temp_K > 3.2) {
      class2 = true;
    }

    this.last_place_t = Date.now();
    
    return {
      ok: !class3,
      placement_error_pm: this.error_pm,
      msg: class3 ? "Class 3 violation" : class2 ? "Class 2 warning" : "OK"
    };
  }

  Pause(): [boolean, string] {
    this.paused = true;
    return [true, "Paused"];
  }

  Abort(): [boolean, string] {
    this.aborted = true;
    this.armed = false;
    return [true, "Aborted"];
  }

  GetTelemetry(): Telemetry {
    const class2 = this.error_pm > this.caps.error_goal_pm * 1.5 || this.temp_K > 3.2;
    const class3 = this.error_pm > this.caps.error_hard_pm || this.temp_K > 3.8;
    
    return {
      error_pm: this.error_pm,
      epa_eV: this.epa_eV,
      temp_K: this.temp_K,
      flux_ips: this.flux_ips,
      balance_B: this.balance_B,
      interlocks_ok: this.interlocks_ok,
      class2,
      class3
    };
  }
}