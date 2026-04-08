#!/usr/bin/env python3
"""
Ionospheric Object Detection Analysis Script
Searches for anomalous objects in LEO using open-source ionospheric data
"""

import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class IonosphericObjectDetector:
    """
    Detects anomalous objects in low Earth orbit via ionospheric signatures
    """

    def __init__(self):
        self.data_sources = {
            'schumann_tomsk': 'https://schumannresonancedata.com/',
            'haarp': 'https://haarp.gi.alaska.edu/diagnostic-suite',
            'mirrion': 'https://www.ncei.noaa.gov/products/space-weather/legacy-data/mirrion-2-real-time-ionosonde',
            'giro': 'https://giro.uml.edu/GAMBIT',
            'waldo': 'https://waldo.world'
        }

        # Known VLF transmitters for reference
        self.vlf_transmitters = {
            'NWC': {'freq': 19.8, 'location': (-21.82, 114.17), 'power': 1000},
            'NPM': {'freq': 21.4, 'location': (21.42, -157.92), 'power': 566},
            'NLK': {'freq': 24.8, 'location': (48.2, -121.92), 'power': 250},
            'NAA': {'freq': 24.0, 'location': (44.65, -67.28), 'power': 1000},
            'GBZ': {'freq': 19.6, 'location': (54.9, -3.3), 'power': 16},
            'JXN': {'freq': 16.4, 'location': (66.98, 13.87), 'power': 50},
            'ICV': {'freq': 20.27, 'location': (40.92, 9.73), 'power': 20}
        }

        # Schumann resonance baseline
        self.schumann_baseline = {
            'fundamental': 7.83,
            'harmonics': [14.3, 20.8, 26.4, 33.0]
        }

    def analyze_schumann_anomaly(self, frequency_data, amplitude_data, timestamps):
        """
        Analyze Schumann resonance data for anomalies

        Parameters:
        -----------
        frequency_data : array-like
            Frequency measurements (Hz)
        amplitude_data : array-like
            Amplitude measurements (relative)
        timestamps : array-like
            Measurement timestamps

        Returns:
        --------
        dict : Anomaly detection results
        """
        results = {
            'baseline_deviation': [],
            'amplitude_spikes': [],
            'anomaly_score': 0,
            'periodic_components': []
        }

        # Check fundamental frequency deviation
        fundamental_mask = (frequency_data >= 7.0) & (frequency_data <= 8.5)
        if np.any(fundamental_mask):
            fundamental_mean = np.mean(frequency_data[fundamental_mask])
            baseline_deviation = abs(fundamental_mean - self.schumann_baseline['fundamental'])
            results['baseline_deviation'].append({
                'frequency': 'fundamental',
                'deviation_hz': baseline_deviation,
                'significant': baseline_deviation > 0.3
            })

        # Detect amplitude spikes (>3x background)
        background = np.percentile(amplitude_data, 50)
        spike_threshold = background * 3
        spikes = amplitude_data > spike_threshold

        if np.any(spikes):
            spike_times = [timestamps[i] for i in np.where(spikes)[0]]
            results['amplitude_spikes'].extend(spike_times)

        # FFT for periodic components (orbital frequencies)
        if len(amplitude_data) > 100:
            fft = np.fft.fft(amplitude_data)
            freqs = np.fft.fftfreq(len(amplitude_data), d=3600)  # 1-hour sampling assumed

            # Look for orbital periods (90-120 min = 0.011-0.015 Hz)
            orbital_mask = (freqs >= 0.0001) & (freqs <= 0.001)
            if np.any(orbital_mask):
                orbital_power = np.abs(fft[orbital_mask])
                if np.max(orbital_power) > np.mean(orbital_power) * 2:
                    peak_idx = np.where(orbital_mask)[0][np.argmax(orbital_power)]
                    period_minutes = 1 / (freqs[peak_idx] * 60)
                    results['periodic_components'].append({
                        'period_minutes': period_minutes,
                        'power': np.max(orbital_power)
                    })

        # Overall anomaly score
        results['anomaly_score'] = (
            len([d for d in results['baseline_deviation'] if d['significant']]) * 0.3 +
            len(results['amplitude_spikes']) * 0.1 +
            len(results['periodic_components']) * 0.4
        )

        return results

    def analyze_ionosonde_anomaly(self, foF2_data, hmF2_data, timestamps, station_id):
        """
        Analyze ionosonde data for anomalous signatures

        Parameters:
        -----------
        foF2_data : array-like
            Critical frequency of F2 layer (MHz)
        hmF2_data : array-like
            Height of maximum electron density (km)
        timestamps : array-like
            Measurement timestamps
        station_id : str
            Ionosonde station identifier

        Returns:
        --------
        dict : Anomaly detection results
        """
        results = {
            'foF2_depletions': [],
            'hmF2_anomalies': [],
            'diurnal_deviation': [],
            'station': station_id
        }

        # Detect foF2 depletions (>20% drop)
        foF2_smooth = pd.Series(foF2_data).rolling(window=5, center=True).mean()
        for i in range(1, len(foF2_data)-1):
            if foF2_data[i] < foF2_smooth.iloc[i] * 0.8:  # 20% depletion
                results['foF2_depletions'].append({
                    'timestamp': timestamps[i],
                    'foF2': foF2_data[i],
                    'baseline': foF2_smooth.iloc[i],
                    'depletion_percent': (1 - foF2_data[i]/foF2_smooth.iloc[i]) * 100
                })

        # Detect hmF2 anomalies (sudden height changes)
        hmF2_diff = np.diff(hmF2_data)
        anomalous_changes = np.where(np.abs(hmF2_diff) > 50)[0]  # >50 km change
        for idx in anomalous_changes:
            results['hmF2_anomalies'].append({
                'timestamp': timestamps[idx],
                'height_change_km': hmF2_diff[idx],
                'height_before': hmF2_data[idx],
                'height_after': hmF2_data[idx+1]
            })

        return results

    def analyze_vlf_anomaly(self, amplitude_data, phase_data, transmitter, timestamps):
        """
        Analyze VLF data for anomalous signatures

        Parameters:
        -----------
        amplitude_data : array-like
            Signal amplitude (dB or relative)
        phase_data : array-like
            Signal phase (degrees)
        transmitter : str
            Transmitter identifier (e.g., 'NWC')
        timestamps : array-like
            Measurement timestamps

        Returns:
        --------
        dict : Anomaly detection results
        """
        results = {
            'transmitter': transmitter,
            'amplitude_variations': [],
            'phase_perturbations': [],
            'terminator_anomalies': []
        }

        if transmitter not in self.vlf_transmitters:
            return results

        tx_info = self.vlf_transmitters[transmitter]

        # Detect amplitude variations >3σ
        mean_amp = np.mean(amplitude_data)
        std_amp = np.std(amplitude_data)
        threshold = mean_amp + 3 * std_amp

        anomalies = np.where(np.abs(amplitude_data - mean_amp) > 3 * std_amp)[0]
        for idx in anomalies:
            results['amplitude_variations'].append({
                'timestamp': timestamps[idx],
                'amplitude': amplitude_data[idx],
                'deviation_sigma': (amplitude_data[idx] - mean_amp) / std_amp
            })

        # Detect phase perturbations
        phase_diff = np.diff(phase_data)
        phase_anomalies = np.where(np.abs(phase_diff) > 10)[0]  # >10° change
        for idx in phase_anomalies:
            results['phase_perturbations'].append({
                'timestamp': timestamps[idx],
                'phase_change': phase_diff[idx]
            })

        return results

    def correlate_multi_sensor(self, schumann_results, ionosonde_results, vlf_results):
        """
        Correlate anomalies across multiple sensor types

        Returns:
        --------
        dict : Correlated events
        """
        correlated_events = []

        # Extract timestamps from each sensor
        schumann_times = set(schumann_results.get('amplitude_spikes', []))
        ionosonde_times = set([d['timestamp'] for d in ionosonde_results.get('foF2_depletions', [])])
        vlf_times = set([v['timestamp'] for v in vlf_results.get('amplitude_variations', [])])

        # Find overlapping time windows (±15 minutes)
        all_times = schumann_times.union(ionosonde_times).union(vlf_times)

        for t in all_times:
            window_start = t - timedelta(minutes=15)
            window_end = t + timedelta(minutes=15)

            sensors_triggered = []
            if any(window_start <= ts <= window_end for ts in schumann_times):
                sensors_triggered.append('schumann')
            if any(window_start <= ts <= window_end for ts in ionosonde_times):
                sensors_triggered.append('ionosonde')
            if any(window_start <= ts <= window_end for ts in vlf_times):
                sensors_triggered.append('vlf')

            if len(sensors_triggered) >= 2:
                correlated_events.append({
                    'timestamp': t,
                    'sensors': sensors_triggered,
                    'confidence': len(sensors_triggered) / 3
                })

        return correlated_events

    def generate_report(self, detection_results):
        """
        Generate a formatted detection report
        """
        report = []
        report.append("=" * 70)
        report.append("IONOSPHERIC OBJECT DETECTION REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 70)
        report.append("")

        # Summary statistics
        report.append("SUMMARY STATISTICS")
        report.append("-" * 40)
        report.append(f"Total anomalies detected: {detection_results.get('total_anomalies', 0)}")
        report.append(f"Multi-sensor correlations: {detection_results.get('correlated_events', 0)}")
        report.append(f"Overall confidence: {detection_results.get('confidence', 0):.2f}")
        report.append("")

        # Detailed findings
        if 'correlated_events' in detection_results:
            report.append("CORRELATED EVENTS (2+ sensors)")
            report.append("-" * 40)
            for event in detection_results['correlated_events'][:10]:  # Top 10
                report.append(f"  Time: {event['timestamp']}")
                report.append(f"  Sensors: {', '.join(event['sensors'])}")
                report.append(f"  Confidence: {event['confidence']:.2f}")
                report.append("")

        report.append("=" * 70)
        report.append("END OF REPORT")
        report.append("=" * 70)

        return '\n'.join(report)


def main():
    """
    Main analysis routine
    """
    detector = IonosphericObjectDetector()

    print("Ionospheric Object Detection System")
    print("=" * 50)
    print()
    print("Available data sources:")
    for name, url in detector.data_sources.items():
        print(f"  - {name}: {url}")
    print()
    print("Known VLF transmitters:")
    for tx, info in detector.vlf_transmitters.items():
        print(f"  - {tx}: {info['freq']} kHz, {info['power']} kW")
    print()
    print("Schumann resonance baseline:")
    print(f"  Fundamental: {detector.schumann_baseline['fundamental']} Hz")
    print(f"  Harmonics: {detector.schumann_baseline['harmonics']}")
    print()
    print("=" * 50)
    print("System ready for data ingestion and analysis")
    print()
    print("To use this system:")
    print("1. Download data from WALDO, GIRO, or other sources")
    print("2. Load data into pandas DataFrame")
    print("3. Call appropriate analysis method:")
    print("   - analyze_schumann_anomaly()")
    print("   - analyze_ionosonde_anomaly()")
    print("   - analyze_vlf_anomaly()")
    print("4. Use correlate_multi_sensor() for cross-validation")
    print("5. Generate report with generate_report()")


if __name__ == "__main__":
    main()
