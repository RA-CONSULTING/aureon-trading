# aura_validator.py
import sys, json, time, csv, math, os
from collections import deque

EPS = 1e-12

# ---- EWMA normalizer (robust to live drift) ----
class EWMA:
    def __init__(self, alpha=0.02):
        self.alpha = alpha
        self.m = None
        self.v = None

    def update(self, x: float):
        x = 0.0 if (x is None or not math.isfinite(float(x))) else float(x)
        if self.m is None:
            self.m = x
            self.v = 1.0
        else:
            a = self.alpha
            diff = x - self.m
            self.m += a * diff
            self.v = (1 - a) * (self.v + a * diff * diff)
        # z-score like normalization
        return (x - self.m) / (math.sqrt(self.v) + EPS)

# ---- helpers ----
def fnum(x, d=6):
    try:
        x = float(x)
        if not math.isfinite(x): return 0.0
        return float(f"{x:.{d}f}")
    except: return 0.0

def clamp01(x): 
    try:
        return max(0.0, min(1.0, float(x)))
    except: 
        return 0.0

def hue_from_bands(alpha, theta, beta):
    # Map band dominance to hue (deg): theta→220°, alpha→60°, beta→0°
    # Weighted barycentric blend
    alpha = max(0.0, alpha); theta = max(0.0, theta); beta = max(0.0, beta)
    s = alpha + theta + beta + EPS
    wa, wt, wb = alpha/s, theta/s, beta/s
    hue = (wb*0.0 + wa*60.0 + wt*220.0) % 360.0
    return hue

def ten_nine_one_concordance(unity, flow, anchor):
    # normalize the triple then project onto 10:9:1
    u, f, a = max(0.0, unity), max(0.0, flow), max(0.0, anchor)
    s = u + f + a + EPS
    u, f, a = u/s, f/s, a/s
    k = (10.0, 9.0, 1.0)
    kn = math.sqrt(k[0]**2 + k[1]**2 + k[2]**2)
    proj = (u*k[0] + f*k[1] + a*k[2]) / (kn + EPS)
    # scale to 0..1 over a practical range
    return clamp01(0.5 + 0.5 * proj)

# ---- CSV setup ----
os.makedirs("validation", exist_ok=True)
csv_path = "validation/aura_features.csv"
write_header = not os.path.exists(csv_path) or os.stat(csv_path).st_size == 0
f = open(csv_path, "a", newline="")
w = csv.writer(f)
if write_header:
    w.writerow([
        "timestamp","epoch","label",
        "alpha_theta_ratio","hrv_norm","gsr_norm",
        "calm_index","prime_concordance_10_9_1","aura_hue_deg"
    ])
    f.flush()

# ---- normalizers ----
z_hrv = EWMA(alpha=0.02)  # slower, HRV drifts slowly
z_gsr = EWMA(alpha=0.05)  # skin response can drift faster

# ---- live ingest (stdin, JSON lines) ----
print("Aura validator listening on stdin…", file=sys.stderr)
epoch = 0
label = "live"

for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue

    if "epoch" in msg: 
        try: epoch = int(msg["epoch"])
        except: pass
    if "label" in msg:
        try: label = str(msg["label"])
        except: pass

    t = msg.get("t", time.time())
    bands = msg.get("bands", {}) or {}
    alpha = float(bands.get("alpha", 0.0) or 0.0)
    theta = float(bands.get("theta", 0.0) or 0.0)
    beta  = float(bands.get("beta",  0.0) or 0.0)

    # alpha/theta ratio
    atr = alpha / (theta + EPS)

    # HRV normalization (z-like)
    hrv = float(msg.get("hrv_rmssd", 0.0) or 0.0)
    hrv_norm = clamp01(0.5 + 0.2 * z_hrv.update(hrv))

    # GSR normalization (z-like)
    gsr = float(msg.get("gsr_uS", 0.0) or 0.0)
    gsr_norm = clamp01(0.5 + 0.2 * z_gsr.update(gsr))

    # Calm Index: blend of high alpha/theta and high HRV, moderated by low beta and gentle respiration
    resp_bpm = float(msg.get("resp_bpm", 0.0) or 0.0)
    resp_term = 1.0 - clamp01(abs(resp_bpm - 6.0) / 12.0)  # peak near ~6 bpm
    beta_term = 1.0 / (1.0 + beta)                          # lower beta → calmer
    # normalize ATR softly
    atr_norm = math.atan(atr) * (2.0 / math.pi)             # 0..1-ish
    calm_index = clamp01(0.35*atr_norm + 0.35*hrv_norm + 0.15*resp_term + 0.15*beta_term)

    # 10-9-1 concordance from (Unity, Flow, Anchor) proxies:
    # Unity ~ alpha dominance, Flow ~ HRV quality, Anchor ~ theta stability
    c1091 = ten_nine_one_concordance(unity=alpha, flow=hrv_norm, anchor=theta)

    # Aura hue from band dominance
    hue = hue_from_bands(alpha, theta, beta)

    w.writerow([
        fnum(t,3), epoch, label,
        fnum(atr), fnum(hrv_norm), fnum(gsr_norm),
        fnum(calm_index), fnum(c1091), fnum(hue)
    ])
    f.flush()

print("Aura validator finished.", file=sys.stderr)
f.close()