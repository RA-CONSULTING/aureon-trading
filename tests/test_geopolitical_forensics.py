import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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


geo = load_module('test_geopolitical_forensics_module', 'aureon/geopolitical_forensics.py')


class TestGeopoliticalForensics(unittest.TestCase):
    def test_default_scores_match_expected_thresholds(self):
        engine = geo.GeopoliticalForensicsEngine(output_root=ROOT)
        findings = engine.analyze('both')

        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0].case.cluster_id, 'MAGAMYMAN-001')
        self.assertAlmostEqual(findings[0].lt_score, 12.85, places=2)
        self.assertEqual(findings[0].case.severity, 'EXTREME')
        self.assertEqual(findings[1].case.cluster_id, 'BUBBLEMAPS-6')
        self.assertAlmostEqual(findings[1].lt_score, 13.03, places=2)
        self.assertEqual(findings[1].case.severity, 'EXTREME')

    def test_cli_artifacts_are_written_with_expected_names(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            exit_code = geo.main([
                '--cluster',
                'both',
                '--output-root',
                tmp_dir,
                '--report-stamp',
                '20260306_000000',
            ])
            self.assertEqual(exit_code, 0)

            evidence_mag = Path(tmp_dir) / 'evidence' / 'evidence_MAGAMYMAN-001_L12.85.json'
            evidence_bubble = Path(tmp_dir) / 'evidence' / 'evidence_BUBBLEMAPS-6_L13.03.json'
            report_path = Path(tmp_dir) / 'reports' / 'findings_report_20260306_000000.tex'

            self.assertTrue(evidence_mag.exists())
            self.assertTrue(evidence_bubble.exists())
            self.assertTrue(report_path.exists())

            mag_payload = json.loads(evidence_mag.read_text(encoding='utf-8'))
            bubble_payload = json.loads(evidence_bubble.read_text(encoding='utf-8'))
            report_text = report_path.read_text(encoding='utf-8')

            self.assertEqual(mag_payload['cluster_id'], 'MAGAMYMAN-001')
            self.assertAlmostEqual(mag_payload['lt_score'], 12.85, places=2)
            self.assertEqual(bubble_payload['cluster_id'], 'BUBBLEMAPS-6')
            self.assertAlmostEqual(bubble_payload['lt_score'], 13.03, places=2)
            self.assertIn('public-record, pseudonymous activity only', report_text)


class TestStakeConcentration(unittest.TestCase):
    def test_gini_uniform_distribution_is_zero(self):
        gini = geo._compute_gini([100.0, 100.0, 100.0, 100.0])
        self.assertAlmostEqual(gini, 0.0, places=4)

    def test_gini_concentrated_distribution_is_high(self):
        gini = geo._compute_gini([0.0, 0.0, 0.0, 1000.0])
        self.assertGreater(gini, 0.7)

    def test_herfindahl_monopoly(self):
        hhi = geo._compute_herfindahl([1.0])
        self.assertAlmostEqual(hhi, 1.0, places=4)

    def test_herfindahl_equal_split(self):
        hhi = geo._compute_herfindahl([0.25, 0.25, 0.25, 0.25])
        self.assertAlmostEqual(hhi, 0.0625 * 4, places=4)

    def test_stake_result_to_dict_round_trip(self):
        result = geo.StakeConcentrationResult(
            contract_address='0xABC',
            chain='polygon',
            top_n=10,
            total_supply_sampled=1000.0,
            top_n_share=0.85,
            gini_coefficient=0.65,
            herfindahl_index=0.12,
            source='polygonscan',
            fetched_at='2026-03-06T00:00:00+00:00',
        )
        d = result.to_dict()
        self.assertEqual(d['chain'], 'polygon')
        self.assertAlmostEqual(d['gini_coefficient'], 0.65, places=4)


class TestBuildPdf(unittest.TestCase):
    def test_build_pdf_raises_on_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            geo.build_pdf('/nonexistent/report.tex')

    def test_build_pdf_raises_when_pdflatex_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tex = Path(tmp_dir) / 'report.tex'
            tex.write_text(r'\documentclass{article}\begin{document}Hi\end{document}')
            with patch.object(shutil, 'which', return_value=None):
                with self.assertRaises(RuntimeError) as ctx:
                    geo.build_pdf(tex)
                self.assertIn('pdflatex is not installed', str(ctx.exception))

    def test_cli_pdf_flag_reports_error_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(shutil, 'which', return_value=None):
                exit_code = geo.main([
                    '--cluster', 'magamyman',
                    '--output-root', tmp_dir,
                    '--report-stamp', 'test',
                    '--pdf', '--json',
                ])
            self.assertEqual(exit_code, 0)


if __name__ == '__main__':
    unittest.main()