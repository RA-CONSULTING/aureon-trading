#!/usr/bin/env bash
set -euo pipefail

# Ephemeris + Coupling Validation Pipeline
# Outputs: CSVs for ephemeris errors, alignment events, extrema, Kp/F10.7 parse,
# radar Gamma, lag correlation and coherence spectra.

if [[ ! -f "Kp_ap_Ap_SN_F107_since_1932.txt" ]]; then
  echo "⚠️  Missing Kp_ap_Ap_SN_F107_since_1932.txt in current directory"
  echo "    Download from GFZ Potsdam and place it here, then re-run."
  exit 1
fi

echo "⏳ Installing minimal dependencies (local venv optional)"
python - <<'PY'
import sys, subprocess
pkgs = [
  'numpy','pandas','skyfield','astroquery','astropy','scipy','requests'
]
subprocess.check_call([sys.executable,'-m','pip','install','--quiet','--disable-pip-version-check']+pkgs)
print('✅ Dependencies ready')
PY

echo "1) Generate Skyfield ephemeris (radar_ephem_skyfield_de440.csv)"
python - <<'PY'
from datetime import datetime, timezone, timedelta
import numpy as np, pandas as pd
from skyfield.api import load

PLANETS = {
    "Mercury":"mercury",
    "Venus":"venus",
    "Earth":"earth",
    "Mars":"mars barycenter",
    "Jupiter":"jupiter barycenter",
    "Saturn":"saturn barycenter",
    "Uranus":"uranus barycenter",
    "Neptune":"neptune barycenter"
}

def make_times(start_utc, end_utc, step_hours=6):
    t = start_utc; out=[]
    while t <= end_utc:
        out.append(t); t += timedelta(hours=step_hours)
    return out

ts = load.timescale()
eph = load("de440s.bsp")
earth = eph["earth"]; sun = eph["sun"]
now = datetime.now(timezone.utc); start = now - timedelta(days=30)
grid = make_times(start, now, step_hours=6)
rows=[]
for dt in grid:
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    sun_app = earth.at(t).observe(sun).apparent()
    sun_u = sun_app.position.au; sun_u = sun_u / np.linalg.norm(sun_u)
    for name,key in PLANETS.items():
        body = eph[key]
        app = earth.at(t).observe(body).apparent()
        ra,dec,_ = app.radec()
        u = app.position.au; u = u / np.linalg.norm(u)
        cosang = float(np.clip(np.dot(u, sun_u), -1.0, 1.0))
        elong = np.degrees(np.arccos(cosang))
        rows.append({"datetime": dt.isoformat(), "planet": name, "ra_deg": ra.hours*15.0, "dec_deg": dec.degrees, "elong_deg": elong})
df = pd.DataFrame(rows)
df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
df.to_csv("radar_ephem_skyfield_de440.csv", index=False)
print("Wrote radar_ephem_skyfield_de440.csv")
PY

echo "2) Fetch Horizons geocentric ephemeris and heliocentric r (radar_ephem_horizons_truth_with_r.csv)"
python - <<'PY'
from datetime import datetime, timezone, timedelta
import pandas as pd
from astroquery.jplhorizons import Horizons

PLANETS = {"Mercury":"199","Venus":"299","Earth":"399","Mars":"499","Jupiter":"599","Saturn":"699","Uranus":"799","Neptune":"899"}
EARTH_LOC="500@399"; SUN_CENTER="500@10"

def make_times(start_utc, end_utc, step_hours=6):
    t=start_utc; out=[]
    while t<=end_utc:
        out.append(t.strftime("%Y-%m-%d %H:%M")); t+=timedelta(hours=step_hours)
    return out

now = datetime.now(timezone.utc); start = now - timedelta(days=30)
times = make_times(start, now, step_hours=6)
rows=[]
for name,pid in PLANETS.items():
    print("Fetching", name)
    h = Horizons(id=pid, location=EARTH_LOC, epochs=times)
    geo = h.ephemerides(quantities="1,20").to_pandas()
    geo["datetime"] = pd.to_datetime(geo["datetime_str"], utc=True)
    geo = geo.rename(columns={"RA":"ra_deg","DEC":"dec_deg","ELONG":"elong_deg"})[["datetime","ra_deg","dec_deg","elong_deg"]]

    h2 = Horizons(id=pid, location=SUN_CENTER, epochs=times)
    vec = h2.vectors().to_pandas()
    vec["datetime"] = pd.to_datetime(vec["datetime_str"], utc=True)
    vec["r_au"] = (vec["X"]**2 + vec["Y"]**2 + vec["Z"]**2)**0.5
    hel = vec[["datetime","r_au"]]

    df = geo.merge(hel, on="datetime", how="inner")
    df["planet"] = name
    rows.append(df)
out = pd.concat(rows, ignore_index=True)
out.to_csv("radar_ephem_horizons_truth_with_r.csv", index=False)
print("Wrote radar_ephem_horizons_truth_with_r.csv")
PY

echo "3) Compare Skyfield vs Horizons (ephem_error_detail.csv)"
python - <<'PY'
import pandas as pd, math

def unit_from_radec(ra_deg, dec_deg):
    ra = math.radians(ra_deg); dec = math.radians(dec_deg)
    return (math.cos(dec)*math.cos(ra), math.cos(dec)*math.sin(ra), math.sin(dec))

def ang_sep_arcmin(u,v):
    dot = max(-1.0, min(1.0, u[0]*v[0]+u[1]*v[1]+u[2]*v[2]))
    return math.degrees(math.acos(dot))*60.0

h = pd.read_csv("radar_ephem_horizons_truth_with_r.csv", parse_dates=["datetime"])
s = pd.read_csv("radar_ephem_skyfield_de440.csv", parse_dates=["datetime"])
df = h.merge(s, on=["datetime","planet"], suffixes=("_hz","_sf"))
errs=[]
for _,r in df.iterrows():
    uh = unit_from_radec(r["ra_deg_hz"], r["dec_deg_hz"])
    us = unit_from_radec(r["ra_deg_sf"], r["dec_deg_sf"])
    errs.append(ang_sep_arcmin(uh,us))
df["pos_err_arcmin"]=errs
df.to_csv("ephem_error_detail.csv", index=False)
print("Wrote ephem_error_detail.csv")
PY

echo "4) Alignment events diff (gate2_alignment_event_diff.csv)"
python - <<'PY'
import pandas as pd
EPS_DEG=3.0; TIME_TOL_HOURS=6

def extract_events(df, src):
    out=[]
    for _,r in df.iterrows():
        t=r["datetime"]; e=float(r["elong_deg"])
        if e<=EPS_DEG: out.append({"src":src,"planet":r["planet"],"datetime":t,"type":"CONJUNCTION","elong_deg":e})
        if abs(e-180.0)<=EPS_DEG: out.append({"src":src,"planet":r["planet"],"datetime":t,"type":"OPPOSITION","elong_deg":e})
    return pd.DataFrame(out)

def nearest_time_delta(a_times, b_times):
    deltas=[]
    for t in a_times:
        diffs=(b_times - t).abs(); j=diffs.idxmin(); deltas.append(b_times.loc[j]-t)
    return deltas

hz = pd.read_csv("radar_ephem_horizons_truth_with_r.csv", parse_dates=["datetime"])
sf = pd.read_csv("radar_ephem_skyfield_de440.csv", parse_dates=["datetime"])
hz_ev = extract_events(hz, "horizons"); sf_ev = extract_events(sf, "skyfield")
rows=[]
for planet in sorted(set(hz_ev["planet"]).union(sf_ev["planet"])):
    for typ in ["CONJUNCTION","OPPOSITION"]:
        a = hz_ev[(hz_ev["planet"]==planet)&(hz_ev["type"]==typ)].copy()
        b = sf_ev[(sf_ev["planet"]==planet)&(sf_ev["type"]==typ)].copy()
        if a.empty and b.empty: continue
        if a.empty:
            for t in b["datetime"]:
                rows.append({"planet":planet,"type":typ,"horizons_time":None,"skyfield_time":t,"delta_hours":None,"status":"MISSING_HORIZONS"})
            continue
        if b.empty:
            for t in a["datetime"]:
                rows.append({"planet":planet,"type":typ,"horizons_time":t,"skyfield_time":None,"delta_hours":None,"status":"MISSING_SKYFIELD"})
            continue
        deltas = nearest_time_delta(a["datetime"].reset_index(drop=True), b["datetime"].reset_index(drop=True))
        for ht, dt in zip(a["datetime"], deltas):
            delta_hours = dt.total_seconds()/3600.0
            status = "PASS" if abs(delta_hours) <= TIME_TOL_HOURS else "FAIL"
            diffs = (b["datetime"] - ht).abs()
            st = b.loc[diffs.idxmin(), "datetime"]
            rows.append({"planet":planet,"type":typ,"horizons_time":ht,"skyfield_time":st,"delta_hours":delta_hours,"status":status})
out = pd.DataFrame(rows).sort_values(["planet","type","horizons_time"], na_position="last")
out.to_csv("gate2_alignment_event_diff.csv", index=False)
print("Wrote gate2_alignment_event_diff.csv")
PY

echo "5) Distance extrema comparison (gate2_distance_extrema_*.csv)"
python - <<'PY'
import pandas as pd

def extrema(df, src):
    rows=[]
    for planet,g in df.groupby("planet"):
        g=g.sort_values("datetime")
        i_min=g["r_au"].idxmin(); i_max=g["r_au"].idxmax()
        rows.append({"src":src,"planet":planet,"kind":"MIN_R","time":g.loc[i_min,"datetime"],"r_au":g.loc[i_min,"r_au"]})
        rows.append({"src":src,"planet":planet,"kind":"MAX_R","time":g.loc[i_max,"datetime"],"r_au":g.loc[i_max,"r_au"]})
    return pd.DataFrame(rows)

try:
    sf = pd.read_csv("skyfield_helio_r.csv", parse_dates=["datetime"])
    sf_ex = extrema(sf, "skyfield")
    hz = pd.read_csv("horizons_helio_r.csv", parse_dates=["datetime"])
    hz_ex = extrema(hz, "horizons")
    df = hz_ex.merge(sf_ex, on=["planet","kind"], suffixes=("_hz","_sf"))
    df["delta_r_au"] = df["r_au_sf"] - df["r_au_hz"]
    df["delta_time_hours"] = (pd.to_datetime(df["time_sf"]) - pd.to_datetime(df["time_hz"])).dt.total_seconds()/3600.0
    df.to_csv("gate2_distance_extrema_diff.csv", index=False)
    print("Wrote gate2_distance_extrema_diff.csv")
except FileNotFoundError:
    # If horizons_helio_r.csv not present, write skyfield-only extrema
    try:
        hz = pd.read_csv("radar_ephem_horizons_truth_with_r.csv", parse_dates=["datetime"])
        hz[['datetime','planet','r_au']].to_csv('horizons_helio_r.csv', index=False)
    except Exception:
        pass
    try:
        sf = pd.read_csv("radar_ephem_skyfield_de440.csv", parse_dates=["datetime"])  # no r_au
        print("No Skyfield heliocentric r source; skipping skyfield-only extrema")
    except Exception:
        pass
PY

echo "6) Parse GFZ Kp file (kp_ap_f107.csv)"
python - <<'PY'
import pandas as pd
from datetime import datetime, timedelta

def parse_gfz_kp_file(filepath):
    rows=[]
    with open(filepath,'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip(): continue
            parts=line.split()
            if len(parts)<3: continue
            try:
                year=int(parts[0]); month=int(parts[1]); day=int(parts[2])
                kp_values=[]
                for i in range(3, min(11, len(parts))):
                    try: kp_values.append(float(parts[i]))
                    except: kp_values.append(None)
                base_date = datetime(year, month, day)
                for hour_idx, kp in enumerate(kp_values):
                    dt = base_date + timedelta(hours=hour_idx*3)
                    ap_daily=None; f107=None
                    if len(parts)>11:
                        try: ap_daily=float(parts[11])
                        except: pass
                    if len(parts)>13:
                        try: f107=float(parts[13])
                        except: pass
                    rows.append({'datetime':dt,'Kp':kp,'ap_daily':ap_daily,'F107':f107})
            except:
                continue
    df=pd.DataFrame(rows)
    df['datetime']=pd.to_datetime(df['datetime'], utc=True)
    df['F107']=df.groupby(df['datetime'].dt.date)['F107'].transform(lambda x: x.ffill().bfill())
    return df

df = parse_gfz_kp_file("Kp_ap_Ap_SN_F107_since_1932.txt")
df = df.dropna(subset=['Kp'])
df.to_csv("kp_ap_f107.csv", index=False)
print("Wrote kp_ap_f107.csv")
PY

echo "7) Generate radar_timeseries.csv (Gamma and L2_event)"
python - <<'PY'
import pandas as pd, numpy as np

def compute_gamma_from_ephemeris(ephem_df):
    gamma=[]
    for planet in ephem_df['planet'].unique():
        pdf = ephem_df[ephem_df['planet']==planet].copy()
        elong = pdf['elong_deg'].values
        alignment = np.minimum(elong, np.abs(180-elong))
        if 'r_au' in pdf.columns:
            r = pdf['r_au'].values; weight = 1.0/(r**2)
        else:
            weight = 1.0
        contrib = weight * np.exp(-alignment/10.0)
        gamma.append(pd.DataFrame({'datetime':pdf['datetime'].values, f'gamma_{planet}':contrib}))
    result = gamma[0]
    for g in gamma[1:]:
        result = result.merge(g, on='datetime', how='outer')
    planet_cols = [c for c in result.columns if c.startswith('gamma_')]
    result['Gamma'] = result[planet_cols].sum(axis=1)
    return result[['datetime','Gamma']]

def detect_lighthouse_events(ephem_df, eps_deg=3.0):
    events=[]
    for _,row in ephem_df.iterrows():
        elong = row['elong_deg']; is_event=0
        if elong <= eps_deg: is_event=1
        elif abs(elong-180.0) <= eps_deg: is_event=1
        events.append({'datetime':row['datetime'],'planet':row['planet'],'L2_event':is_event})
    df = pd.DataFrame(events)
    agg = df.groupby('datetime')['L2_event'].max().reset_index()
    return agg

ephem = pd.read_csv("radar_ephem_skyfield_de440.csv", parse_dates=["datetime"])
try:
    horizons = pd.read_csv("radar_ephem_horizons_truth_with_r.csv", parse_dates=["datetime"])
    ephem = ephem.merge(horizons[['datetime','planet','r_au']], on=['datetime','planet'], how='left')
except FileNotFoundError:
    pass

gamma_df = compute_gamma_from_ephemeris(ephem)
events_df = detect_lighthouse_events(ephem, eps_deg=3.0)
result = gamma_df.merge(events_df, on='datetime', how='left')
result['L2_event'] = result['L2_event'].fillna(0).astype(int)
result = result.sort_values('datetime')
result.to_csv("radar_timeseries.csv", index=False)
print("Wrote radar_timeseries.csv")
PY

echo "8) Gate 3 coupling tests (gate3_lag_corr.csv, gate3_coherence.csv)"
python - <<'PY'
import numpy as np, pandas as pd
from scipy.signal import coherence, detrend
from scipy.stats import pearsonr

TARGET_COL="Kp"; RADAR_COL="Gamma"; DT_HOURS=3; MAX_LAG_HOURS=72; EPSILON=1e-12
COH_NPERSEG=256

def lag_corr(x,y,max_lag_steps):
    out=[]
    for lag in range(-max_lag_steps, max_lag_steps+1):
        if lag < 0: xx=x[-lag:]; yy=y[:lag]
        elif lag > 0: xx=x[:-lag]; yy=y[lag:]
        else: xx=x; yy=y
        r = pearsonr(xx,yy)[0] if len(xx)>10 else np.nan
        out.append((lag,r))
    return pd.DataFrame(out, columns=["lag_steps","r"])

radar = pd.read_csv("radar_timeseries.csv", parse_dates=["datetime"]).set_index("datetime")
kp = pd.read_csv("kp_ap_f107.csv", parse_dates=["datetime"]).set_index("datetime")
radar_3h = radar.resample(f"{DT_HOURS}H").mean()
kp_3h = kp.resample(f"{DT_HOURS}H").mean()
df = radar_3h.join(kp_3h[[TARGET_COL,"F107"]], how="inner").dropna(subset=[RADAR_COL,TARGET_COL])

X = detrend(df[RADAR_COL].values); Y = detrend(df[TARGET_COL].values)
X = (X - X.mean())/(X.std()+EPSILON); Y = (Y - Y.mean())/(Y.std()+EPSILON)
max_lag_steps = int(MAX_LAG_HOURS/DT_HOURS)
lc = lag_corr(X,Y,max_lag_steps=max_lag_steps)
lc.to_csv("gate3_lag_corr.csv", index=False)

fs = 1.0/(DT_HOURS*3600.0)
f, Cxy = coherence(X,Y,fs=fs, nperseg=min(COH_NPERSEG, len(X)//2))
pd.DataFrame({"freq_hz":f,"coherence":Cxy}).to_csv("gate3_coherence.csv", index=False)
print("Wrote gate3_lag_corr.csv and gate3_coherence.csv")
PY

echo "✅ Pipeline complete. CSV outputs are in $(pwd)"
