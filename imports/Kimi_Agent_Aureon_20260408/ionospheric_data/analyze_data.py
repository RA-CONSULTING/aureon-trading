#!/usr/bin/env python3
"""
30-Day Ionospheric Analysis Pipeline
Analyzes collected data for orbital object detection
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import fft
from scipy.signal import correlate, find_peaks
import cv2
from datetime import datetime, timedelta
import json
import os
from glob import glob

class IonosphericAnalyzer:
    def __init__(self, data_dir="/mnt/okcomputer/output/ionospheric_data"):
        self.data_dir = data_dir
        self.results = {
            "anomalies": [],
            "periodicity": {},
            "sacred_geometry": {},
            "ground_track": []
        }

    def analyze_schumann_sonograms(self):
        """Analyze all Schumann sonograms for anomalies"""
        sonogram_files = sorted(glob(f"{self.data_dir}/schumann/*.jpg"))

        print(f"Analyzing {len(sonogram_files)} sonograms...")

        anomalies = []
        for filepath in sonogram_files:
            # Extract timestamp from filename
            filename = os.path.basename(filepath)
            timestamp = self._parse_timestamp(filename)

            # Load and analyze image
            img = cv2.imread(filepath)
            if img is None:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Detect vertical spikes (anomalies)
            vertical_profile = np.mean(gray, axis=0)
            peaks, properties = find_peaks(vertical_profile, 
                                           height=np.mean(vertical_profile) * 2,
                                           distance=50)

            if len(peaks) > 0:
                for peak in peaks:
                    anomalies.append({
                        "timestamp": timestamp,
                        "type": "vertical_spike",
                        "location": int(peak),
                        "intensity": float(vertical_profile[peak])
                    })

        self.results["anomalies"] = anomalies
        print(f"Found {len(anomalies)} anomalies")
        return anomalies

    def detect_periodicity(self):
        """Detect orbital periodicity using FFT"""
        anomalies = self.results["anomalies"]

        if len(anomalies) < 10:
            print("Not enough anomalies for periodicity analysis")
            return None

        # Extract timestamps
        timestamps = [a["timestamp"] for a in anomalies]
        timestamps.sort()

        # Convert to seconds from start
        start_time = timestamps[0]
        times = [(t - start_time).total_seconds() for t in timestamps]

        # Create time series (1 = anomaly, 0 = no anomaly)
        duration = times[-1]
        sample_rate = 600  # 10 minutes
        num_samples = int(duration / sample_rate) + 1

        time_series = np.zeros(num_samples)
        for t in times:
            idx = int(t / sample_rate)
            if idx < num_samples:
                time_series[idx] = 1

        # FFT
        fft_result = np.fft.fft(time_series)
        freqs = np.fft.fftfreq(len(time_series), d=sample_rate)

        # Look for orbital periods (90-120 minutes = 5400-7200 seconds)
        orbital_periods = [5400, 6000, 6600, 7200]  # 90, 100, 110, 120 minutes

        detected_periods = []
        for period in orbital_periods:
            freq = 1 / period
            idx = np.argmin(np.abs(freqs - freq))
            power = np.abs(fft_result[idx]) ** 2

            if power > np.mean(np.abs(fft_result) ** 2) * 2:
                detected_periods.append({
                    "period_seconds": period,
                    "period_minutes": period / 60,
                    "power": float(power)
                })

        self.results["periodicity"] = detected_periods
        print(f"Detected {len(detected_periods)} orbital periods")
        return detected_periods

    def analyze_sacred_geometry(self):
        """Analyze for sacred geometry patterns"""
        PHI = 1.618033988749895

        anomalies = self.results["anomalies"]
        if len(anomalies) < 5:
            print("Not enough anomalies for sacred geometry analysis")
            return None

        # Sort by timestamp
        anomalies.sort(key=lambda x: x["timestamp"])

        # Calculate intervals
        intervals = []
        for i in range(1, len(anomalies)):
            delta = (anomalies[i]["timestamp"] - anomalies[i-1]["timestamp"]).total_seconds()
            intervals.append(delta)

        # Check for phi-harmonic ratios
        phi_matches = []
        for i in range(len(intervals) - 1):
            if intervals[i+1] > 0:
                ratio = intervals[i] / intervals[i+1]
                if abs(ratio - PHI) < 0.1 or abs(ratio - 1/PHI) < 0.1:
                    phi_matches.append({
                        "interval_1": intervals[i],
                        "interval_2": intervals[i+1],
                        "ratio": ratio,
                        "phi_error": abs(ratio - PHI)
                    })

        # Check for Fibonacci timing
        fibonacci = [3600, 7200, 10800, 18000, 28800, 46800]  # 1, 2, 3, 5, 8, 13 hours
        fib_matches = []
        for interval in intervals:
            for fib in fibonacci:
                if abs(interval - fib) < 300:  # Within 5 minutes
                    fib_matches.append({
                        "interval": interval,
                        "fibonacci_target": fib,
                        "error": abs(interval - fib)
                    })

        self.results["sacred_geometry"] = {
            "phi_harmonics": phi_matches,
            "fibonacci_timing": fib_matches
        }

        print(f"Found {len(phi_matches)} phi-harmonic patterns")
        print(f"Found {len(fib_matches)} Fibonacci timing patterns")

        return self.results["sacred_geometry"]

    def generate_report(self):
        """Generate analysis report"""
        report = {
            "analysis_date": datetime.now().isoformat(),
            "data_directory": self.data_dir,
            "results": self.results
        }

        # Save report
        with open(f"{self.data_dir}/analysis/report.json", 'w') as f:
            json.dump(report, f, indent=2)

        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE")
        print("=" * 70)
        print(f"Report saved to: {self.data_dir}/analysis/report.json")

        return report

    def _parse_timestamp(self, filename):
        """Parse timestamp from filename"""
        # Format: schumann_YYYY-MM-DD_HH-MM-SS.jpg
        try:
            parts = filename.replace("schumann_", "").replace(".jpg", "").split("_")
            date_part = parts[0]
            time_part = parts[1].replace("-", ":")
            return datetime.fromisoformat(f"{date_part}T{time_part}")
        except:
            return datetime.now()

def main():
    analyzer = IonosphericAnalyzer()

    print("=" * 70)
    print("30-DAY IONOSPHERIC ANALYSIS")
    print("=" * 70)

    # Run analysis pipeline
    analyzer.analyze_schumann_sonograms()
    analyzer.detect_periodicity()
    analyzer.analyze_sacred_geometry()
    analyzer.generate_report()

if __name__ == "__main__":
    main()
