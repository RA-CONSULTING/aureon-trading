# emit_test_stream.py  (lattice)
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import json, sys, math, time, random
t0 = time.time()
fund = 7.83
harms = [14.3,20.8,27.3,33.8]
gain = 1.0
fs = 200.0
dt = 1.0/fs

def push_label(label, epoch=None):
    pkt = {"label":label}
    if epoch is not None: pkt["epoch"]=epoch
    print(json.dumps(pkt)); sys.stdout.flush()

# Baseline 10s
push_label("baseline",0)
t=t0
for i in range(int(10*fs)):
    x = 0.15*math.sin(2*math.pi*fund*(t-t0)) \
        + 0.05*math.sin(2*math.pi*harms[0]*(t-t0)) \
        + 0.02*random.uniform(-1,1)
    pkt = {"t":t, "sample":x, "fund_hz":fund, "harmonics":harms, "gain":gain}
    print(json.dumps(pkt)); sys.stdout.flush()
    t += dt

# Intent 1 (grounding) 10s – add coherent envelopes
push_label("intent_grounding",1)
for i in range(int(10*fs)):
    env = 0.25 + 0.1*math.sin(2*math.pi*0.2*(t-t0))  # slow envelope
    x = (0.18+env)*math.sin(2*math.pi*fund*(t-t0)) \
        + 0.10*math.sin(2*math.pi*harms[0]*(t-t0)) \
        + 0.05*math.sin(2*math.pi*harms[1]*(t-t0)) \
        + 0.02*random.uniform(-1,1)
    print(json.dumps({"t":t,"sample":x,"fund_hz":fund,"harmonics":harms,"gain":1.2})); sys.stdout.flush()
    t += dt

# Nudge fundamental +0.05 Hz for lock 10s
push_label("nudge_plus_0p05",2)
fund2 = fund + 0.05
for i in range(int(10*fs)):
    x = 0.22*math.sin(2*math.pi*fund2*(t-t0)) \
        + 0.10*math.sin(2*math.pi*harms[0]*(t-t0)) \
        + 0.05*math.sin(2*math.pi*harms[1]*(t-t0)) \
        + 0.02*random.uniform(-1,1)
    print(json.dumps({"t":t,"sample":x,"fund_hz":fund2,"harmonics":harms,"gain":1.2})); sys.stdout.flush()
    t += dt