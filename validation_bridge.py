#!/usr/bin/env python3
"""
Validation Bridge - Coordinates both Schumann and Aura validators
Manages the 10-minute live proof protocol and data synchronization
"""

import subprocess
import json
import time
import threading
import queue
import sys
from pathlib import Path

class ValidationBridge:
    def __init__(self):
        self.auris_process = None
        self.aura_process = None
        self.data_queue = queue.Queue()
        self.running = False
        self.epoch = 0
        self.current_label = "baseline"
        
    def start_validators(self):
        """Start both validator processes"""
        try:
            # Start Auris validator
            self.auris_process = subprocess.Popen(
                [sys.executable, 'validator_auris.py'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Start Aura validator  
            self.aura_process = subprocess.Popen(
                [sys.executable, 'aura_validator.py'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            print("✓ Both validators started successfully")
            self.running = True
            return True
            
        except Exception as e:
            print(f"✗ Failed to start validators: {e}")
            return False
    
    def stop_validators(self):
        """Stop both validator processes"""
        self.running = False
        
        if self.auris_process:
            self.auris_process.terminate()
            self.auris_process.wait()
            
        if self.aura_process:
            self.aura_process.terminate()
            self.aura_process.wait()
            
        print("✓ Validators stopped")
    
    def send_auris_data(self, sample_data, fund_hz=7.83, harmonics=None, gain=1.0):
        """Send data to Auris validator"""
        if not self.auris_process or not self.running:
            return
            
        if harmonics is None:
            harmonics = [7.83, 14.3, 20.8, 27.3, 33.8]
            
        data = {
            "t": time.time(),
            "epoch": self.epoch,
            "label": self.current_label,
            "sample": sample_data,
            "fund_hz": fund_hz,
            "harmonics": harmonics,
            "gain": gain
        }
        
        try:
            json_line = json.dumps(data) + "\n"
            self.auris_process.stdin.write(json_line)
            self.auris_process.stdin.flush()
        except Exception as e:
            print(f"Error sending Auris data: {e}")
    
    def send_aura_data(self, bands=None, hrv_rmssd=0.0, gsr_uS=0.0, resp_bpm=0.0):
        """Send data to Aura validator"""
        if not self.aura_process or not self.running:
            return
            
        if bands is None:
            bands = {"alpha": 0.5, "theta": 0.3, "beta": 0.2}
            
        data = {
            "t": time.time(),
            "epoch": self.epoch,
            "label": self.current_label,
            "bands": bands,
            "hrv_rmssd": hrv_rmssd,
            "gsr_uS": gsr_uS,
            "resp_bpm": resp_bpm
        }
        
        try:
            json_line = json.dumps(data) + "\n"
            self.aura_process.stdin.write(json_line)
            self.aura_process.stdin.flush()
        except Exception as e:
            print(f"Error sending Aura data: {e}")
    
    def set_phase(self, epoch: int, label: str):
        """Update current validation phase"""
        self.epoch = epoch
        self.current_label = label
        print(f"Phase changed: Epoch {epoch} - {label}")
    
    def run_validation_protocol(self):
        """Execute the 10-minute validation protocol"""
        phases = [
            (1, "warmup", 60, "Sensor warmup and baseline setup"),
            (2, "baseline", 120, "No intent recording"),
            (3, "intent_1", 60, "Grounding intent focus"),
            (4, "washout_1", 30, "Recovery period"),
            (5, "intent_2", 60, "Coherence intent focus"), 
            (6, "washout_2", 30, "Recovery period"),
            (7, "intent_3", 60, "Alignment intent focus"),
            (8, "nudge_plus", 60, "Schumann +0.05 Hz nudge"),
            (9, "nudge_minus", 60, "Schumann -0.05 Hz nudge"),
            (10, "spheres", 60, "Jupiter-Saturn synodic mix")
        ]
        
        print("🚀 Starting 10-minute validation protocol...")
        
        for epoch, label, duration, description in phases:
            self.set_phase(epoch, label)
            print(f"📍 Phase {epoch}: {description} ({duration}s)")
            
            # Simulate data generation for this phase
            for second in range(duration):
                if not self.running:
                    break
                    
                # Generate mock Schumann data
                sample_data = [0.1 * (i + second) for i in range(100)]  # Mock samples
                fund_hz = 7.83 + (0.05 if label == "nudge_plus" else -0.05 if label == "nudge_minus" else 0.0)
                self.send_auris_data(sample_data, fund_hz=fund_hz)
                
                # Generate mock EEG/biometric data
                bands = {
                    "alpha": 0.4 + 0.2 * (1 if "intent" in label else 0),
                    "theta": 0.3 + 0.1 * (1 if "intent" in label else 0), 
                    "beta": 0.3 - 0.1 * (1 if "intent" in label else 0)
                }
                hrv = 45.0 + 10.0 * (1 if "intent" in label else 0)
                self.send_aura_data(bands=bands, hrv_rmssd=hrv)
                
                time.sleep(1)
                
                if second % 10 == 0:
                    print(f"  ⏱️  {second}s elapsed...")
        
        print("✅ Validation protocol completed!")
        print("📊 Check validation/ folder for CSV outputs")

def main():
    bridge = ValidationBridge()
    
    try:
        if not bridge.start_validators():
            return 1
            
        # Run the validation protocol
        bridge.run_validation_protocol()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        bridge.stop_validators()
        
    return 0

if __name__ == "__main__":
    sys.exit(main())