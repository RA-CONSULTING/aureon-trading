#!/usr/bin/env python3
"""
GFZ INDEX PARSER
================

Parse geomagnetic indices from GFZ Potsdam data file:
- Kp (3-hour geomagnetic activity index)
- ap (3-hour equivalent amplitude)
- Ap (daily average)
- F10.7 (solar radio flux)

Source: https://www.gfz-potsdam.de/en/section/geomagnetism/data-products-services/geomagnetic-kp-index
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import warnings


def parse_gfz_kp_file(
    filepath: str = 'Kp_ap_Ap_SN_F107_since_1932.txt',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    output_file: str = 'kp_ap_f107.csv'
) -> pd.DataFrame:
    """
    Parse GFZ Kp/ap/F10.7 data file.
    
    File format (fixed-width):
    YYYY MM DD  days  days_m  Bsr  dB   Kp1...Kp8  ap1...ap8  Ap  SN  F107obs  F107adj  D
    
    Returns DataFrame with 3-hour resolution.
    """
    print(f"Parsing GFZ data: {filepath}")
    
    records = []
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip headers and comments
                if not line or line.startswith('#') or line.startswith('Y'):
                    continue
                
                parts = line.split()
                if len(parts) < 30:
                    continue
                
                try:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    
                    # Skip invalid dates
                    if year < 1932 or month < 1 or month > 12 or day < 1 or day > 31:
                        continue
                    
                    # Kp values (8 per day, 3-hour intervals)
                    # Format: Kp values are at indices 7-14
                    kp_values = []
                    for i in range(7, 15):
                        if i < len(parts):
                            try:
                                # Kp can be like "2o" "2+" "2-" - convert to numeric
                                kp_str = parts[i]
                                kp_val = float(kp_str.replace('o', '').replace('+', '.3').replace('-', '.0'))
                                kp_values.append(kp_val)
                            except:
                                kp_values.append(np.nan)
                        else:
                            kp_values.append(np.nan)
                    
                    # ap values (indices 15-22)
                    ap_values = []
                    for i in range(15, 23):
                        if i < len(parts):
                            try:
                                ap_values.append(float(parts[i]))
                            except:
                                ap_values.append(np.nan)
                        else:
                            ap_values.append(np.nan)
                    
                    # Daily Ap (index 23)
                    Ap = float(parts[23]) if len(parts) > 23 else np.nan
                    
                    # F10.7 observed (index 26)
                    F107 = float(parts[26]) if len(parts) > 26 else np.nan
                    
                    # Create 3-hour records
                    base_date = datetime(year, month, day)
                    for i, (kp, ap) in enumerate(zip(kp_values, ap_values)):
                        dt = base_date + timedelta(hours=i * 3)
                        records.append({
                            'datetime': dt,
                            'Kp': kp,
                            'ap': ap,
                            'Ap': Ap,
                            'F107': F107
                        })
                
                except Exception as e:
                    continue
    
    except FileNotFoundError:
        print(f"⚠ File not found: {filepath}")
        print("  Download from: https://www.gfz-potsdam.de/fileadmin/XXXX/Kp_ap_Ap_SN_F107_since_1932.txt")
        return pd.DataFrame()
    
    df = pd.DataFrame(records)
    
    if len(df) == 0:
        print("⚠ No data parsed!")
        return df
    
    # Filter date range
    if start_date:
        df = df[df['datetime'] >= start_date]
    if end_date:
        df = df[df['datetime'] <= end_date]
    
    # Forward-fill F107 (daily value applied to all 3-hour slots)
    df['F107'] = df['F107'].ffill()
    
    # Save
    df.to_csv(output_file, index=False)
    
    print(f"✓ Parsed {len(df)} records")
    print(f"  Date range: {df['datetime'].min()} → {df['datetime'].max()}")
    print(f"  Kp range: {df['Kp'].min():.1f} → {df['Kp'].max():.1f}")
    print(f"  F107 range: {df['F107'].min():.1f} → {df['F107'].max():.1f}")
    print(f"✓ Wrote {output_file}")
    
    return df


def resample_to_6h(
    input_file: str = 'kp_ap_f107.csv',
    output_file: str = 'kp_ap_f107_6h.csv'
) -> pd.DataFrame:
    """
    Resample 3-hour Kp data to 6-hour intervals.
    """
    df = pd.read_csv(input_file, parse_dates=['datetime'])
    df = df.set_index('datetime')
    
    # 6-hour mean
    resampled = df.resample('6H').agg({
        'Kp': 'mean',
        'ap': 'mean',
        'Ap': 'first',  # Daily value
        'F107': 'first'  # Daily value
    })
    
    resampled = resampled.reset_index()
    resampled.to_csv(output_file, index=False)
    
    print(f"✓ Resampled to 6H: {output_file} ({len(resampled)} rows)")
    
    return resampled


def download_gfz_file(output_path: str = 'Kp_ap_Ap_SN_F107_since_1932.txt') -> bool:
    """
    Download the GFZ Kp data file.
    """
    import urllib.request
    
    url = "https://www.gfz-potsdam.de/fileadmin/XXXX/Kp_ap_Ap_SN_F107_since_1932.txt"
    
    # Note: The actual URL varies. This is a placeholder.
    # Current URL (as of 2024):
    urls_to_try = [
        "https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F107_since_1932.txt",
        "https://www-app3.gfz-potsdam.de/kp_index/Kp_ap_Ap_SN_F107_since_1932.txt",
        "https://datapub.gfz-potsdam.de/download/10.5880.Kp.0001/Kp_definitive/Kp_ap_Ap_SN_F107_since_1932.txt"
    ]
    
    for url in urls_to_try:
        try:
            print(f"Trying: {url}")
            urllib.request.urlretrieve(url, output_path)
            print(f"✓ Downloaded to {output_path}")
            return True
        except Exception as e:
            print(f"  Failed: {e}")
            continue
    
    print("⚠ Could not download GFZ file. Please download manually from:")
    print("  https://kp.gfz-potsdam.de/")
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Parse GFZ Kp/ap/F10.7 data')
    parser.add_argument('--input', default='Kp_ap_Ap_SN_F107_since_1932.txt',
                        help='Input GFZ file')
    parser.add_argument('--output', default='kp_ap_f107.csv',
                        help='Output CSV file')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--download', action='store_true',
                        help='Try to download GFZ file first')
    parser.add_argument('--resample-6h', action='store_true',
                        help='Also create 6-hour resampled file')
    
    args = parser.parse_args()
    
    if args.download:
        download_gfz_file(args.input)
    
    df = parse_gfz_kp_file(
        filepath=args.input,
        start_date=args.start,
        end_date=args.end,
        output_file=args.output
    )
    
    if args.resample_6h and len(df) > 0:
        resample_to_6h(args.output)


if __name__ == '__main__':
    main()
