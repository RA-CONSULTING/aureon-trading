// PAW API Driver Methods - Extended functionality

import { Element, Voxel, PlaceReply, Telemetry, SafetyViolation } from '../types/paw-types';
import { PAWAPIDriver } from './paw-api-driver';

export class PAWAPIDriverExtended extends PAWAPIDriver {
  
  Inject(elem: Element, flux_ips: number): [boolean, string] {
    if (!this.armed) {
      return [false, "Not armed"];
    }
    this.flux_ips = Math.min(flux_ips, this.caps.flux_max);
    return [true, `Injecting ${elem.symbol} at ${this.flux_ips.toExponential(2)} ips`];
  }

  Place(voxel: Voxel, elem: Element, energy_eV: number, complexity: number): PlaceReply {
    if (!this.armed || this.paused || this.aborted) {
      return { ok: false, placement_error_pm: this.error_pm, msg: "Not ready" };
    }

    // Base error trend: harder for higher complexity, better for higher B
    const base_err = 80 + 10 * complexity;
    const B = Math.max(0.0, this.balance_B);
    const scale = Math.max(0.35, 1.4 - 0.6 * Math.min(B, 2.0));
    const noise = this.gauss(0.0, 8.0 + 2.0 * complexity);
    const drift = 3.0 * Math.sin(Date.now() * 0.0009);
    
    this.error_pm = Math.max(0.0, base_err * scale + noise + drift);
    
    // Energy-per-atom model
    this.epa_eV = Math.max(0.1, 10 + 1.5 * complexity - 3.0 * Math.min(B, 2.0));
    
    // Temperature dynamics
    this.temp_K = Math.max(1.6, Math.min(4.0, 
      this.temp_K + 0.002 * this.flux_ips / 1e6 - 0.01));

    // Safety violations
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