from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import json
import os
import tempfile
import unittest

from learned_analytics_reset import reset_learned_analytics_if_needed


class TestLearnedAutoResetSmoke(unittest.TestCase):
    def test_reset_when_regime_tag_changes(self):
        with tempfile.TemporaryDirectory() as td:
            history_path = os.path.join(td, 'adaptive_learning_history.json')

            original = {
                'trades': [{'pnl': -0.01, 'entry_time': 1}],
                'thresholds': {'min_score': 999},
                'regime_tag': 'old_regime',
            }
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(original, f)

            result = reset_learned_analytics_if_needed(
                history_path=history_path,
                reason='startup auto reset',
                regime_tag='penny_profit_v1',
                force=False,
                archive=True,
            )

            self.assertTrue(result.did_reset)
            self.assertIsNotNone(result.backup_path)
            self.assertTrue(os.path.exists(result.backup_path))

            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.assertEqual(data.get('trades'), [])
            self.assertEqual(data.get('thresholds'), {})
            self.assertEqual(data.get('regime_tag'), 'penny_profit_v1')

    def test_no_reset_when_same_regime_and_has_trades(self):
        with tempfile.TemporaryDirectory() as td:
            history_path = os.path.join(td, 'adaptive_learning_history.json')

            original = {
                'trades': [{'pnl': 0.02, 'entry_time': 1}],
                'thresholds': {'min_score': 55},
                'regime_tag': 'penny_profit_v1',
            }
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(original, f)

            result = reset_learned_analytics_if_needed(
                history_path=history_path,
                reason='startup auto reset',
                regime_tag='penny_profit_v1',
                force=False,
                archive=True,
            )

            self.assertFalse(result.did_reset)
            self.assertIsNone(result.backup_path)

            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.assertEqual(data.get('trades'), original['trades'])
            self.assertEqual(data.get('thresholds'), original['thresholds'])
            self.assertEqual(data.get('regime_tag'), 'penny_profit_v1')

    def test_force_reset_even_when_same_regime(self):
        with tempfile.TemporaryDirectory() as td:
            history_path = os.path.join(td, 'adaptive_learning_history.json')

            original = {
                'trades': [{'pnl': 0.02, 'entry_time': 1}],
                'thresholds': {'min_score': 55},
                'regime_tag': 'penny_profit_v1',
            }
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(original, f)

            result = reset_learned_analytics_if_needed(
                history_path=history_path,
                reason='forced',
                regime_tag='penny_profit_v1',
                force=True,
                archive=True,
            )

            self.assertTrue(result.did_reset)
            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.assertEqual(data.get('trades'), [])
            self.assertEqual(data.get('thresholds'), {})
            self.assertEqual(data.get('regime_tag'), 'penny_profit_v1')


class TestAutoResetIntegrationWithEngine(unittest.TestCase):
    def test_engine_startup_resets_target_file_only(self):
        # Ensure import-time global ADAPTIVE_LEARNER doesn't wipe real history.
        os.environ.pop('AUREON_AUTO_RESET_LEARNED_ANALYTICS', None)

        import aureon_unified_ecosystem  # noqa: F401
        from aureon_unified_ecosystem import AdaptiveLearningEngine

        with tempfile.TemporaryDirectory() as td:
            history_path = os.path.join(td, 'adaptive_learning_history.json')
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump({'trades': [{'pnl': -1}], 'thresholds': {}, 'regime_tag': 'old'}, f)

            os.environ['AUREON_AUTO_RESET_LEARNED_ANALYTICS'] = '1'
            os.environ['AUREON_LEARNED_ANALYTICS_REGIME_TAG'] = 'penny_profit_v1'
            os.environ['AUREON_AUTO_RESET_LEARNED_ANALYTICS_REASON'] = 'test'

            _engine = AdaptiveLearningEngine(history_file=history_path)

            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.assertEqual(data.get('trades'), [])
            self.assertEqual(data.get('regime_tag'), 'penny_profit_v1')

            rec = _engine.get_entry_recommendation(
                symbol='TEST',
                frequency=256,
                coherence=0.55,
                score=70,
                probability=0.55,
            )
            self.assertTrue(rec.get('should_trade'), rec)


if __name__ == '__main__':
    unittest.main()
