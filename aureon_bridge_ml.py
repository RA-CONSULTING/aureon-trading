# aureon_bridge_ml.py
import json
import time
import os
import csv
from dataclasses import dataclass, asdict
from typing import List, Dict

# Configuration
SNAPSHOT_FILE = "bot_shape_snapshot.json"
TRAINING_DATA_FILE = "bot_shape_training_data.csv"

@dataclass
class BotShapeFeatureRow:
    timestamp: float
    symbol: str
    bot_class: str
    dominant_freq_1: float
    dominant_freq_2: float
    dominant_freq_3: float
    amplitude_1: float
    amplitude_2: float
    amplitude_3: float
    layering_score: float
    layering_depth_ratio: float
    
def flatten_shape(timestamp: float, shape: Dict) -> BotShapeFeatureRow:
    freqs = shape.get('dominant_freqs', [])
    amps = shape.get('amplitudes', [])
    
    # Pad with 0 if fewer than 3 frequencies found
    f1 = freqs[0] if len(freqs) > 0 else 0.0
    f2 = freqs[1] if len(freqs) > 1 else 0.0
    f3 = freqs[2] if len(freqs) > 2 else 0.0
    
    a1 = amps[0] if len(amps) > 0 else 0.0
    a2 = amps[1] if len(amps) > 1 else 0.0
    a3 = amps[2] if len(amps) > 2 else 0.0
    
    return BotShapeFeatureRow(
        timestamp=timestamp,
        symbol=shape['symbol'],
        bot_class=shape['bot_class'],
        dominant_freq_1=f1,
        dominant_freq_2=f2,
        dominant_freq_3=f3,
        amplitude_1=a1,
        amplitude_2=a2,
        amplitude_3=a3,
        layering_score=shape.get('layering_score', 0.0),
        layering_depth_ratio=shape.get('layering_depth_ratio', 0.0)
    )

def bridge_loop():
    print(f"🌉 AUREON ML BRIDGE: Monitoring {SNAPSHOT_FILE}...")
    
    last_processed_time = 0
    
    # Initialize CSV if not exists
    file_exists = os.path.exists(TRAINING_DATA_FILE)
    if not file_exists:
        with open(TRAINING_DATA_FILE, 'w', newline='') as csvfile:
            fieldnames = [field for field in BotShapeFeatureRow.__annotations__]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    while True:
        try:
            if os.path.exists(SNAPSHOT_FILE):
                # Check modification time
                mod_time = os.path.getmtime(SNAPSHOT_FILE)
                
                if mod_time > last_processed_time:
                    with open(SNAPSHOT_FILE, 'r') as f:
                        data = json.load(f)
                    
                    ts = data.get('timestamp', time.time())
                    shapes = data.get('shapes', [])
                    
                    if not shapes:
                        time.sleep(1)
                        continue

                    print(f"📥 Processing snapshot from {time.ctime(ts)} with {len(shapes)} shapes...")
                    
                    rows = []
                    for shape in shapes:
                        rows.append(asdict(flatten_shape(ts, shape)))
                    
                    # Append to CSV
                    with open(TRAINING_DATA_FILE, 'a', newline='') as csvfile:
                        fieldnames = [field for field in BotShapeFeatureRow.__annotations__]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writerows(rows)
                        
                    print(f"✅ Appended {len(rows)} rows to {TRAINING_DATA_FILE}")
                    last_processed_time = mod_time
                    
            time.sleep(5) # Check every 5 seconds
            
        except Exception as e:
            print(f"❌ Bridge Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    bridge_loop()
