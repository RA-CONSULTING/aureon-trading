# emit_test_stream_aura.py  (aura)
import json, sys, math, time, random
t0 = time.time()
def out(**kw): print(json.dumps(kw)); sys.stdout.flush()

# Baseline 10s
out(label="baseline", epoch=0)
for k in range(10):
    t = t0 + k
    alpha, theta, beta = 2.0, 1.8, 1.0
    out(t=t, bands={"alpha":alpha,"theta":theta,"beta":beta},
        hrv_rmssd=35+2*random.random(), gsr_uS=4.0+0.2*random.random(), resp_bpm=12)
    time.sleep(1)  # 1 second intervals

# Intent 10s (calm ↑: alpha↑, beta↓, HRV↑, resp→6 bpm)
out(label="intent_grounding", epoch=1)
for k in range(10):
    t = t0 + 10 + k
    alpha = 2.8 + 0.2*math.sin(2*math.pi*0.1*k)
    theta = 1.6 + 0.1*math.sin(2*math.pi*0.07*k)
    beta  = 0.7 + 0.05*math.sin(2*math.pi*0.13*k)
    out(t=t, bands={"alpha":alpha,"theta":theta,"beta":beta},
        hrv_rmssd=52+3*random.random(), gsr_uS=3.8+0.2*random.random(), resp_bpm=6)
    time.sleep(1)

# Nudge 10s (hold calm)
out(label="nudge_plus_0p05", epoch=2)
for k in range(10):
    t = t0 + 20 + k
    alpha, theta, beta = 3.0, 1.5, 0.65
    out(t=t, bands={"alpha":alpha,"theta":theta,"beta":beta},
        hrv_rmssd=55+2*random.random(), gsr_uS=3.7+0.2*random.random(), resp_bpm=6)
    time.sleep(1)