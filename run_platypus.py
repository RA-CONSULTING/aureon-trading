#!/usr/bin/env python3
"""
PLATYPUS PIPELINE ORCHESTRATOR
==============================

Master script to run the full Song of the Sphaerae pipeline:

1. Generate ephemeris (Skyfield DE440)
2. Fetch truth data (JPL Horizons)
3. Gate 1: Compare positions
4. Gate 2A: Detect alignment events
5. Gate 2B: Detect distance extrema
6. Parse GFZ indices (Kp, ap, F10.7)
7. Compute Platypus coherence (Q, H, E, O, Λ, Γ)
8. Gate 3: Validate coupling

Usage:
    python run_platypus.py --start 2020-01-01 --end 2024-12-31
    python run_platypus.py --preset geometric --start 2023-01-01 --end 2024-01-01
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """Check if required packages are installed."""
    missing = []
    
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    
    try:
        import pandas
    except ImportError:
        missing.append('pandas')
    
    try:
        import scipy
    except ImportError:
        missing.append('scipy')
    
    try:
        import skyfield
    except ImportError:
        missing.append('skyfield')
    
    try:
        import astroquery
    except ImportError:
        missing.append('astroquery')
    
    if missing:
        print("Missing required packages:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def run_pipeline(
    start_date: str,
    end_date: str,
    preset: str = 'default',
    dt_hours: int = 6,
    skip_horizons: bool = False,
    skip_gfz_download: bool = False,
    output_dir: str = '.'
):
    """Run full Platypus pipeline."""
    
    print("=" * 70)
    print("PLATYPUS / SONG OF THE SPHAERAE PIPELINE")
    print("=" * 70)
    print(f"Date range: {start_date} → {end_date}")
    print(f"Preset: {preset}")
    print(f"Time step: {dt_hours}h")
    print("=" * 70)
    
    # Change to output directory
    os.makedirs(output_dir, exist_ok=True)
    original_dir = os.getcwd()
    os.chdir(output_dir)
    
    try:
        # ═══════════════════════════════════════════════════════════════════
        # STEP 1: Generate Skyfield Ephemeris
        # ═══════════════════════════════════════════════════════════════════
        print("\n" + "─" * 70)
        print("STEP 1: Generate Skyfield Ephemeris (DE440)")
        print("─" * 70)
        
        from ephemeris_generator import generate_skyfield_ephemeris
        
        sf_file = 'radar_ephem_skyfield_de440.csv'
        generate_skyfield_ephemeris(start_date, end_date, dt_hours, sf_file)
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 2: Fetch JPL Horizons Truth (Optional)
        # ═══════════════════════════════════════════════════════════════════
        hz_file = 'radar_ephem_horizons_truth.csv'
        
        if not skip_horizons:
            print("\n" + "─" * 70)
            print("STEP 2: Fetch JPL Horizons Truth Data")
            print("─" * 70)
            
            from ephemeris_generator import fetch_horizons_truth
            fetch_horizons_truth(start_date, end_date, dt_hours, hz_file)
        else:
            print("\n⚠ Skipping Horizons fetch (--skip-horizons)")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 3: Gate 1 - Compare Positions
        # ═══════════════════════════════════════════════════════════════════
        if not skip_horizons and os.path.exists(hz_file):
            print("\n" + "─" * 70)
            print("STEP 3: Gate 1 - Positional Accuracy Check")
            print("─" * 70)
            
            from ephemeris_generator import compare_ephemerides
            compare_ephemerides(sf_file, hz_file, 'gate1_errors.csv')
        else:
            print("\n⚠ Skipping Gate 1 (no Horizons data)")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 4: Gate 2A - Alignment Events
        # ═══════════════════════════════════════════════════════════════════
        print("\n" + "─" * 70)
        print("STEP 4: Gate 2A - Alignment Event Detection")
        print("─" * 70)
        
        from ephemeris_generator import detect_alignment_events
        detect_alignment_events(sf_file, 'alignment_events.csv')
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 5: Gate 2B - Distance Extrema
        # ═══════════════════════════════════════════════════════════════════
        print("\n" + "─" * 70)
        print("STEP 5: Gate 2B - Distance Extrema Detection")
        print("─" * 70)
        
        from ephemeris_generator import detect_distance_extrema
        detect_distance_extrema(sf_file, 'distance_extrema.csv')
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 6: Parse GFZ Indices
        # ═══════════════════════════════════════════════════════════════════
        print("\n" + "─" * 70)
        print("STEP 6: Parse GFZ Kp/ap/F10.7 Indices")
        print("─" * 70)
        
        from gfz_parser import parse_gfz_kp_file, download_gfz_file
        
        gfz_file = 'Kp_ap_Ap_SN_F107_since_1932.txt'
        kp_file = 'kp_ap_f107.csv'
        
        if not os.path.exists(gfz_file):
            if not skip_gfz_download:
                print("GFZ file not found, attempting download...")
                download_gfz_file(gfz_file)
            else:
                print(f"⚠ GFZ file not found: {gfz_file}")
                print("  Please download manually from https://kp.gfz-potsdam.de/")
        
        if os.path.exists(gfz_file):
            parse_gfz_kp_file(
                filepath=gfz_file,
                start_date=start_date,
                end_date=end_date,
                output_file=kp_file
            )
        else:
            print("⚠ Skipping GFZ parsing (file not found)")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 7: Compute Platypus Coherence
        # ═══════════════════════════════════════════════════════════════════
        print("\n" + "─" * 70)
        print("STEP 7: Compute Platypus Coherence (Q, H, E, O, Λ, Γ)")
        print("─" * 70)
        
        from platypus import Platypus
        from platypus_presets import get_preset
        
        config = get_preset(preset)
        config.dt_hours = dt_hours
        
        print(f"Using preset: {preset}")
        print(f"  Weights: S={config.w_S:.2f} Q={config.w_Q:.2f} H={config.w_H:.2f} E={config.w_E:.2f} O={config.w_O:.2f}")
        print(f"  Memory α={config.alpha}, Observer β={config.beta}")
        
        engine = Platypus(config)
        engine.load_ephemeris(sf_file)
        
        if os.path.exists(hz_file):
            engine.load_horizons_r(hz_file)
        
        engine.compute_coherence()
        engine.save_timeseries('radar_timeseries.csv')
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 8: Gate 3 - Validate Coupling
        # ═══════════════════════════════════════════════════════════════════
        if os.path.exists(kp_file):
            print("\n" + "─" * 70)
            print("STEP 8: Gate 3 - Validate Kp Coupling")
            print("─" * 70)
            
            import pandas as pd
            kp_df = pd.read_csv(kp_file, parse_dates=['datetime'])
            
            engine.validate_against_index(kp_df, 'Kp')
            engine.save_validation_artifacts('gate3')
            
            print("\n" + engine.summary())
        else:
            print("\n⚠ Skipping Gate 3 (no Kp data)")
        
        # ═══════════════════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("PIPELINE COMPLETE")
        print("=" * 70)
        print("\nGenerated files:")
        for f in sorted(Path('.').glob('*.csv')):
            size = f.stat().st_size
            print(f"  {f.name:<40} {size:>10} bytes")
        
        print("\nNext steps:")
        print("  1. Review radar_timeseries.csv for coherence patterns")
        print("  2. Check gate3_lag_corr.csv for coupling evidence")
        print("  3. Plot Gamma vs Kp to visualize relationships")
        print("=" * 70)
        
    finally:
        os.chdir(original_dir)


def main():
    parser = argparse.ArgumentParser(
        description='Run Platypus/Song of the Sphaerae Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Presets:
  default     - Balanced weights for general analysis
  high_memory - Strong temporal persistence (α=0.4)
  low_latency - Fast response, minimal memory (α=0.05)
  geometric   - Emphasizes alignment patterns (wQ=0.40)
  forcing     - Emphasizes distance-based forcing (wH=0.40)
  observer    - Strong self-reference (β=0.25)
  moving_avg  - W-step moving average instead of exponential
  strict      - More stringent permutation testing (n=5000)

Examples:
  python run_platypus.py --start 2020-01-01 --end 2024-12-31
  python run_platypus.py --preset geometric --start 2023-01-01 --end 2024-01-01
  python run_platypus.py --skip-horizons --skip-gfz-download  # Offline mode
        """
    )
    
    parser.add_argument('--start', default='2020-01-01',
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2024-12-31',
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--preset', default='default',
                        choices=['default', 'high_memory', 'low_latency', 
                                 'geometric', 'forcing', 'observer', 
                                 'moving_avg', 'strict'],
                        help='Configuration preset')
    parser.add_argument('--step', type=int, default=6,
                        help='Time step in hours (default: 6)')
    parser.add_argument('--skip-horizons', action='store_true',
                        help='Skip JPL Horizons fetch')
    parser.add_argument('--skip-gfz-download', action='store_true',
                        help='Skip GFZ file download attempt')
    parser.add_argument('--output-dir', default='.',
                        help='Output directory for CSV files')
    parser.add_argument('--list-presets', action='store_true',
                        help='List available presets and exit')
    
    args = parser.parse_args()
    
    if args.list_presets:
        from platypus_presets import list_presets
        list_presets()
        return
    
    if not check_dependencies():
        print("\n⚠ Please install missing dependencies first.")
        sys.exit(1)
    
    run_pipeline(
        start_date=args.start,
        end_date=args.end,
        preset=args.preset,
        dt_hours=args.step,
        skip_horizons=args.skip_horizons,
        skip_gfz_download=args.skip_gfz_download,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
