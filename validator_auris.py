# validator_auris.py
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, json, math, time, csv, collections
from typing import List, Deque
import numpy as np

# ---------- Config ----------
SCHUMANN = [7.83, 14.3, 20.8, 27.3, 33.8]
FUND_W = 0.40
SOFTCLIP_ALPHA = 1.2
WIN_SEC = 2.0
HOP_SEC = 0.5
FS = 200.0   # analysis sample rate of incoming 'sample' stream (Hz)
EPS = 1e-12

# ---------- Helpers ----------
def tanh_softclip(x): return math.tanh(SOFTCLIP_ALPHA * x)

def bandpass_env(x, fs, f0, bw=1.2):
    # simple analytic envelope via narrow IIR-like FIR (cheap) + Hilbert
    # For robustness in this minimal script, use FFT mask
    N = len(x)
    if N < 8: return 0.0
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(N, 1.0/fs)
    mask = np.logical_and(freqs >= max(0.01, f0 - bw/2), freqs <= f0 + bw/2)
    X_f = np.zeros_like(X); X_f[mask] = X[mask]
    x_f = np.fft.irfft(X_f, n=N)
    # Envelope via quadrature (Hilbert-ish with 90° shift through -i*sign)
    Y = X_f * (1j * np.sign(freqs))
    y_q = np.fft.irfft(Y, n=N)
    env = np.sqrt(x_f**2 + y_q**2) + EPS
    return float(np.mean(env))

def coh_score(envelopes: List[float]):
    # scalar 'coherence' proxy from per-band envelopes (normalized covariance)
    v = np.array(envelopes, dtype=float)
    if np.any(~np.isfinite(v)) or v.size < 2: return 0.0
    v = (v - v.mean()) / (v.std() + EPS)
    # pairwise corr mean
    c = 0.0; k = 0
    for i in range(len(v)):
      for j in range(i+1, len(v)):
        c += (v[i]*v[j])
        k += 1
    return float(max(0.0, min(1.0, 0.5 + 0.5 * (c / (k + EPS))))) if k else 0.0

def schumann_lock(envelopes: List[float]):
    if len(envelopes) < len(SCHUMANN): return 0.0
    env = np.array(envelopes[:len(SCHUMANN)], dtype=float)
    if not np.all(np.isfinite(env)): return 0.0
    env = np.maximum(env, 0.0)
    weights = np.array([FUND_W] + [ (1.0 - FUND_W)/(len(SCHUMANN)-1) ]*(len(SCHUMANN)-1))
    s = float(np.dot(env, weights) / (np.sum(env) + EPS))
    return max(0.0, min(1.0, s))

def prime_alignment(phases: List[float]):
    # phases already reduced to [0, 2π); compute vector strength
    if len(phases) < 2: return 0.0
    z = np.exp(1j*np.array(phases))
    R = np.abs(np.mean(z))
    return float(max(0.0, min(1.0, R)))

def ten_nine_one_concordance(unity, flow, anchor):
    v = np.array([unity, flow, anchor], dtype=float); v = v / (v.sum() + EPS)
    k = np.array([10.0, 9.0, 1.0], dtype=float); k = k / k.sum()
    return float(max(0.0, min(1.0, np.dot(v, k))))

# ---------- Main Processor ----------
class AurisValidator:
    def __init__(self):
        self.buffer: Deque[float] = collections.deque(maxlen=int(WIN_SEC * FS))
        self.last_hop = 0.0
        self.csv_writer = None
        self.csv_file = None
        self.epoch = 0
        
    def init_csv(self, filename="validation/auris_metrics.csv"):
        import os
        os.makedirs("validation", exist_ok=True)
        self.csv_file = open(filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'timestamp', 'epoch', 'label', 'rms', 'tsv_gain', 'coherence_score',
            'schumann_lock', 'prime_alignment', 'ten_nine_one_concordance',
            'fund_hz', 'harmonics_json', 'gain'
        ])
        
    def process_sample(self, data):
        t = data.get('t', time.time())
        sample = data.get('sample', 0.0)
        fund_hz = data.get('fund_hz', 7.83)
        harmonics = data.get('harmonics', SCHUMANN[1:])
        gain = data.get('gain', 1.0)
        label = data.get('label', 'unlabeled')
        
        self.buffer.append(sample)
        
        if t - self.last_hop >= HOP_SEC and len(self.buffer) >= int(WIN_SEC * FS):
            self.last_hop = t
            self.epoch += 1
            
            # Convert buffer to numpy array
            x = np.array(list(self.buffer))
            
            # Compute metrics
            rms = float(np.sqrt(np.mean(x**2)))
            tsv_gain = tanh_softclip(rms * gain)
            
            # Band envelopes
            freqs = [fund_hz] + harmonics[:4]  # limit to 5 bands
            envelopes = [bandpass_env(x, FS, f) for f in freqs]
            
            coherence_score = coh_score(envelopes)
            lock = schumann_lock(envelopes)
            
            # Mock phases for prime alignment (in real system, extract from complex envelope)
            phases = [2 * np.pi * np.random.random() for _ in freqs]
            alignment = prime_alignment(phases)
            
            # Mock 10-9-1 concordance (in real system, compute from energy ratios)
            unity, flow, anchor = np.random.random(3)
            concordance = ten_nine_one_concordance(unity, flow, anchor)
            
            # Write to CSV
            if self.csv_writer:
                self.csv_writer.writerow([
                    t, self.epoch, label, rms, tsv_gain, coherence_score,
                    lock, alignment, concordance, fund_hz,
                    json.dumps(harmonics), gain
                ])
                self.csv_file.flush()
                
            print(f"Epoch {self.epoch}: Lock={lock:.3f} Coh={coherence_score:.3f} TSV={tsv_gain:.3f}")
            
    def close(self):
        if self.csv_file:
            self.csv_file.close()

# ---------- Main ----------
if __name__ == "__main__":
    validator = AurisValidator()
    validator.init_csv()
    
    try:
        for line in sys.stdin:
            try:
                data = json.loads(line.strip())
                validator.process_sample(data)
            except json.JSONDecodeError:
                continue
    except KeyboardInterrupt:
        pass
    finally:
        validator.close()
        print("Validation complete. Check validation/auris_metrics.csv")