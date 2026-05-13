import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f'Unable to load {module_name} from {module_path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


bridge_module = load_module('test_harmonic_nexus_bridge_module', 'aureon/harmonic_nexus_bridge.py')


class TestHarmonicNexusBridge(unittest.TestCase):
    def test_demo_analysis_matches_expected_temporal_clustering(self):
        bridge = bridge_module.HarmonicNexusBridge()
        report = bridge.run_demo()

        self.assertEqual(report.status, 'Analyzed')
        self.assertEqual(report.geo_count, 1)
        self.assertEqual(report.plasma_count, 1)
        self.assertEqual(report.avg_temporal_proximity_sec, 1560)
        self.assertAlmostEqual(report.clustering_score, 2.77, places=2)
        self.assertEqual(report.interpretation, 'CORRELATED')

    def test_console_output_contains_summary_lines(self):
        bridge = bridge_module.HarmonicNexusBridge()
        report = bridge.run_demo()
        console_output = bridge_module._format_console_output(bridge, report)

        self.assertIn('HARMONIC NEXUS BRIDGE - Cross-Domain Anomaly Fusion', console_output)
        self.assertIn('Temporal proximity: 1560 seconds (26 minutes)', console_output)
        self.assertIn('Clustering score: 2.77x expected', console_output)


class TestPlanetaryNetworkInjection(unittest.TestCase):
    def test_inject_creates_fresh_network_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            net_path = Path(tmp_dir) / 'planetary_harmonic_network.json'
            bridge = bridge_module.HarmonicNexusBridge()
            bridge.run_demo()
            result_path = bridge.inject_into_planetary_network(net_path)

            self.assertTrue(net_path.exists())
            self.assertEqual(result_path, net_path)

            data = json.loads(net_path.read_text(encoding='utf-8'))
            sigs = data['harmonic_signatures']
            # Only the geopolitical anomaly should be injected (not the plasma one)
            geo_sigs = [s for s in sigs if s.get('entity_type') == 'Geopolitical L(t)']
            self.assertEqual(len(geo_sigs), 1)
            self.assertEqual(geo_sigs[0]['entity_name'], 'MAGAMYMAN-001')
            self.assertAlmostEqual(geo_sigs[0]['lt_score'], 12.85, places=2)
            self.assertEqual(geo_sigs[0]['severity'], 'EXTREME')

    def test_inject_merges_into_existing_network(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            net_path = Path(tmp_dir) / 'planetary_harmonic_network.json'
            # Seed with one existing signature
            existing = {
                'metadata': {
                    'sweep_timestamp': 0,
                    'sweep_date': '2026-01-01T00:00:00+00:00',
                    'total_entities': 1,
                    'total_signatures': 1,
                    'total_coordination_links': 0,
                    'total_counter_measures': 0,
                },
                'harmonic_signatures': [{
                    'entity_name': 'MICROSTRATEGY',
                    'entity_type': 'Corporate Treasury',
                    'symbol': 'BTCUSDT',
                    'dominant_cycle_hours': 24.0,
                    'frequency_hz': 0.042,
                    'phase_angle_degrees': 7.5,
                    'amplitude': 50000,
                    'sacred_match': 'DAILY_SOLAR',
                    'sacred_alignment_pct': 99.0,
                    'timestamp': 0,
                }],
                'coordination_network': [],
                'counter_measures': [],
                'threat_analysis': {'critical_links': [], 'high_links': []},
            }
            net_path.write_text(json.dumps(existing, indent=2), encoding='utf-8')

            bridge = bridge_module.HarmonicNexusBridge()
            bridge.run_demo()
            bridge.inject_into_planetary_network(net_path)

            data = json.loads(net_path.read_text(encoding='utf-8'))
            self.assertEqual(data['metadata']['total_signatures'], 2)
            names = {s['entity_name'] for s in data['harmonic_signatures']}
            self.assertIn('MICROSTRATEGY', names)
            self.assertIn('MAGAMYMAN-001', names)

    def test_inject_deduplicates_on_repeat(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            net_path = Path(tmp_dir) / 'planetary_harmonic_network.json'
            bridge = bridge_module.HarmonicNexusBridge()
            bridge.run_demo()
            bridge.inject_into_planetary_network(net_path)
            # Inject again — should not duplicate
            bridge2 = bridge_module.HarmonicNexusBridge()
            bridge2.run_demo()
            bridge2.inject_into_planetary_network(net_path)

            data = json.loads(net_path.read_text(encoding='utf-8'))
            geo_sigs = [s for s in data['harmonic_signatures']
                        if s.get('entity_type') == 'Geopolitical L(t)']
            self.assertEqual(len(geo_sigs), 1)


if __name__ == '__main__':
    unittest.main()