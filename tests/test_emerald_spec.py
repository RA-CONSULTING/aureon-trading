import importlib.util
import json
import math
import sys
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


em = load_module('test_emerald_spec_module', 'aureon/decoders/emerald_spec.py')


class TestTabletVerses(unittest.TestCase):
    """Verify the verse catalogue is well-formed and complete."""

    def test_verse_count_minimum(self):
        self.assertGreaterEqual(len(em._VERSE_CATALOG), 20)

    def test_verse_index_keys_match_catalog(self):
        for verse in em._VERSE_CATALOG:
            self.assertIn(verse.key, em.VERSE_INDEX)
            self.assertIs(em.VERSE_INDEX[verse.key], verse)

    def test_unique_keys(self):
        keys = [v.key for v in em._VERSE_CATALOG]
        self.assertEqual(len(keys), len(set(keys)))

    def test_all_verses_have_required_fields(self):
        for verse in em._VERSE_CATALOG:
            self.assertTrue(verse.key)
            self.assertTrue(verse.hermetic_text)
            self.assertTrue(verse.technical_translation)
            self.assertTrue(verse.aureon_implementation)


class TestSevenStages(unittest.TestCase):
    """Verify the 7 alchemical stages are well-formed."""

    def test_exactly_seven(self):
        self.assertEqual(len(em.SEVEN_STAGES), 7)

    def test_stages_numbered_1_to_7(self):
        numbers = [s.number for s in em.SEVEN_STAGES]
        self.assertEqual(numbers, [1, 2, 3, 4, 5, 6, 7])

    def test_stage_names_match_tradition(self):
        expected = [
            'Calcination', 'Dissolution', 'Separation',
            'Conjunction', 'Fermentation', 'Distillation', 'Coagulation',
        ]
        self.assertEqual([s.name for s in em.SEVEN_STAGES], expected)

    def test_final_stage_is_lt_score(self):
        final = em.SEVEN_STAGES[-1]
        self.assertEqual(final.name, 'Coagulation')
        self.assertEqual(final.units, 'L(t)')
        self.assertAlmostEqual(final.computed_value, 12.85, places=2)


class TestSacredConstants(unittest.TestCase):
    """Verify sacred constants match the seer module values."""

    def test_phi(self):
        self.assertAlmostEqual(em.PHI, (1 + math.sqrt(5)) / 2, places=12)

    def test_schumann(self):
        self.assertEqual(em.SCHUMANN_FUNDAMENTAL, 7.83)

    def test_love_frequency(self):
        self.assertEqual(em.LOVE_FREQUENCY, 528.0)

    def test_rf_carrier(self):
        self.assertEqual(em.RF_CARRIER_ISM, 13.56e6)

    def test_philosophical_threshold(self):
        self.assertEqual(em.PHILOSOPHERS_STONE_THRESHOLD, 2.8)


class TestEmeraldSeer(unittest.TestCase):
    """Test the EmeraldSeer decoder class."""

    def setUp(self):
        self.seer = em.EmeraldSeer()

    def test_decode_verse_known_key(self):
        verse = self.seer.decode_verse('verum')
        self.assertEqual(verse.key, 'verum')
        self.assertIn('Tier 1', verse.technical_translation)

    def test_decode_verse_unknown_key_raises(self):
        with self.assertRaises(KeyError):
            self.seer.decode_verse('nonexistent')

    def test_decode_by_text_found(self):
        verse = self.seer.decode_by_text('below is like')
        self.assertIsNotNone(verse)
        self.assertEqual(verse.key, 'as_below')

    def test_decode_by_text_not_found(self):
        result = self.seer.decode_by_text('completely unrelated string xyz')
        self.assertIsNone(result)

    def test_verify_philosophers_stone_true(self):
        self.assertTrue(self.seer.verify_philosophers_stone(12.85))

    def test_verify_philosophers_stone_false(self):
        self.assertFalse(self.seer.verify_philosophers_stone(1.0))

    def test_verify_golden_gate(self):
        self.assertTrue(self.seer.verify_golden_gate(12.85))
        self.assertFalse(self.seer.verify_golden_gate(3.0))

    def test_classify_score_extreme(self):
        self.assertEqual(self.seer.classify_score(12.85), 'PHILOSOPHERS_STONE')

    def test_classify_score_lead(self):
        self.assertEqual(self.seer.classify_score(0.5), 'LEAD')

    def test_classify_score_prima_materia(self):
        self.assertEqual(self.seer.classify_score(1.5), 'PRIMA_MATERIA')

    def test_haarp_epos_ratio_positive(self):
        ratio = self.seer.haarp_epos_ratio()
        self.assertGreater(ratio, 1000)

    def test_seed_frequencies(self):
        seeds = self.seer.seed_frequencies()
        self.assertEqual(seeds['carrier_hz'], 13.56e6)
        self.assertEqual(seeds['modulation_hz'], 7.83)
        self.assertAlmostEqual(seeds['phi'], em.PHI)

    def test_run_pipeline_returns_seven(self):
        stages = self.seer.run_pipeline()
        self.assertEqual(len(stages), 7)

    def test_get_egyptian_crosswalk_anubis(self):
        crosswalk = self.seer.get_egyptian_crosswalk('anubis')
        self.assertEqual(crosswalk.key, 'anubis')
        self.assertEqual(crosswalk.deity['name'], 'Anubis')
        self.assertIn('fear_greed < 20', crosswalk.runtime['trigger'])
        self.assertEqual(crosswalk.runtime['action'], 'OBSERVE')

    def test_decode_egyptian_ascent_anubis(self):
        payload = self.seer.decode_egyptian_ascent('anubis')
        verse_keys = [verse['key'] for verse in payload['emerald_verses']]
        stage_numbers = [stage['number'] for stage in payload['pipeline_stages']]

        self.assertEqual(payload['target'], 'anubis')
        self.assertIn('verum', verse_keys)
        self.assertIn('separate', verse_keys)
        self.assertIn(3, stage_numbers)
        self.assertIn(5, stage_numbers)
        self.assertEqual(payload['scripture']['book_of_dead_key'], 'spell_125')

    def test_decode_egyptian_ascent_all(self):
        payload = self.seer.decode_egyptian_ascent('all')
        targets = [node['target'] for node in payload['ascent']]

        self.assertEqual(len(payload['ascent']), 5)
        self.assertEqual(targets, ['anubis', 'maat', 'thoth', 'osiris', 'ra'])

    def test_resolve_wikipedia_topic_alias(self):
        self.assertEqual(self.seer._resolve_wikipedia_topic("ma'at"), 'Maat')
        self.assertEqual(self.seer._resolve_wikipedia_topic('spell_125'), 'Book of the Dead')

    def test_decode_wikipedia_meaning(self):
        def fake_fetch(url):
            if 'opensearch' in url:
                return ['Maat', ['Maat'], [], []]
            return {
                'type': 'standard',
                'title': 'Maat',
                'extract': 'Maat is the ancient Egyptian concept of truth and balance.',
                'description': 'ancient Egyptian concept and goddess',
                'pageid': 123,
                'content_urls': {
                    'desktop': {'page': 'https://en.wikipedia.org/wiki/Maat'}
                },
            }

        with patch.object(self.seer, '_fetch_wikipedia_json', side_effect=fake_fetch):
            payload = self.seer.decode_wikipedia_meaning("ma'at")

        self.assertEqual(payload['resolved_query'], 'Maat')
        self.assertEqual(payload['title'], 'Maat')
        self.assertIn('truth and balance', payload['summary'])
        self.assertEqual(payload['page_id'], 123)

    def test_decode_egyptian_ascent_with_wikipedia(self):
        with patch.object(
            self.seer,
            'decode_wikipedia_meaning',
            side_effect=lambda topic: {'query': topic, 'title': topic, 'summary': f'{topic} summary'},
        ):
            payload = self.seer.decode_egyptian_ascent('anubis', include_wikipedia=True)

        topics = [topic['query'] for topic in payload['wikipedia_grounding']['topics']]
        self.assertEqual(topics, ['Emerald Tablet', 'Anubis', 'Book of the Dead', 'Maat'])

    def test_full_decode_json_serialisable(self):
        decoded = self.seer.full_decode()
        # Must be JSON-serialisable without error
        payload = json.dumps(decoded, indent=2)
        self.assertIn('Emerald Tablet', payload)
        self.assertIn('verses', decoded)
        self.assertIn('seven_stages', decoded)
        self.assertIn('egyptian_ascent', decoded)
        self.assertEqual(len(decoded['verses']), len(em._VERSE_CATALOG))
        self.assertEqual(len(decoded['seven_stages']), 7)
        self.assertEqual(len(decoded['egyptian_ascent']), 5)


class TestScalingLaw(unittest.TestCase):
    """Verify HAARP-to-EPOS scaling constants."""

    def test_chamber_volume_approximately_14_liters(self):
        vol_liters = em.EPOS_CHAMBER_VOLUME_M3 * 1000
        self.assertAlmostEqual(vol_liters, 14.14, places=1)

    def test_concentration_factor_order_of_magnitude(self):
        # Volumetric ratio is extremely large (ionosphere vs 30 cm chamber)
        self.assertGreater(em.VOLUMETRIC_CONCENTRATION_FACTOR, 1e9)

    def test_power_ratio_very_small(self):
        ratio = em.EPOS_RF_POWER_W / em.HAARP_POWER_W
        self.assertLess(ratio, 1e-4)
        self.assertGreater(ratio, 1e-6)


class TestCLI(unittest.TestCase):
    """Test CLI entry point."""

    def test_main_returns_zero(self):
        rc = em.main([])
        self.assertEqual(rc, 0)

    def test_main_json_mode(self):
        rc = em.main(['--json'])
        self.assertEqual(rc, 0)

    def test_main_verse_mode(self):
        rc = em.main(['--verse', 'verum'])
        self.assertEqual(rc, 0)

    def test_main_stage_mode(self):
        rc = em.main(['--stage', '7'])
        self.assertEqual(rc, 0)

    def test_main_verse_json_mode(self):
        rc = em.main(['--verse', 'as_below', '--json'])
        self.assertEqual(rc, 0)

    def test_main_ascent_mode(self):
        rc = em.main(['--ascent', 'anubis'])
        self.assertEqual(rc, 0)

    def test_main_ascent_json_mode(self):
        rc = em.main(['--ascent', 'all', '--json'])
        self.assertEqual(rc, 0)

    def test_main_wiki_mode(self):
        with patch.object(
            em.EmeraldSeer,
            'decode_wikipedia_meaning',
            return_value={
                'query': 'Emerald Tablet',
                'resolved_query': 'Emerald Tablet',
                'title': 'Emerald Tablet',
                'summary': 'A compact and cryptic text attributed to Hermes Trismegistus.',
                'description': 'ancient text',
                'page_id': 1,
                'url': 'https://en.wikipedia.org/wiki/Emerald_Tablet',
                'source': 'wikipedia_rest_summary',
            },
        ):
            rc = em.main(['--wiki', 'Emerald Tablet', '--json'])
        self.assertEqual(rc, 0)

    def test_main_ancient_mode(self):
        rc = em.main(['--ancient', 'mogollon'])
        self.assertEqual(rc, 0)

    def test_main_ancient_json_mode(self):
        rc = em.main(['--ancient', 'all', '--json'])
        self.assertEqual(rc, 0)

    def test_main_unified_mode(self):
        rc = em.main(['--unified', '--json'])
        self.assertEqual(rc, 0)


class TestAncientWisdomCatalog(unittest.TestCase):
    """Verify the Mogollon / Maya / Celtic crosswalk nodes."""

    def setUp(self):
        self.seer = em.EmeraldSeer()

    def test_catalog_has_three_nodes(self):
        self.assertEqual(len(em.ANCIENT_WISDOM_CATALOG), 3)
        keys = [n.key for n in em.ANCIENT_WISDOM_CATALOG]
        self.assertEqual(keys, ['mogollon', 'maya', 'celt'])

    def test_get_ancient_wisdom_crosswalk_mogollon(self):
        node = self.seer.get_ancient_wisdom_crosswalk('mogollon')
        self.assertEqual(node.key, 'mogollon')
        self.assertIn('spiral', node.deity['trading'].lower())
        self.assertIn('spiral', node.title.lower())
        self.assertIn((1, 7), [node.stage_numbers])

    def test_get_ancient_wisdom_crosswalk_maya(self):
        node = self.seer.get_ancient_wisdom_crosswalk('maya')
        self.assertEqual(node.key, 'maya')
        self.assertIn('Long Count', node.title)
        self.assertIn('7day_planner', ''.join(node.repo_surfaces))

    def test_get_ancient_wisdom_crosswalk_celt(self):
        node = self.seer.get_ancient_wisdom_crosswalk('celt')
        self.assertEqual(node.key, 'celt')
        self.assertIn('Ogham', node.title)
        self.assertEqual(node.runtime['action'], 'CROSS_THE_THRESHOLD')

    def test_get_ancient_wisdom_unknown_key_raises(self):
        with self.assertRaises(KeyError):
            self.seer.get_ancient_wisdom_crosswalk('atlantis')

    def test_decode_ancient_wisdom_maya_structure(self):
        payload = self.seer.decode_ancient_wisdom('maya')
        self.assertEqual(payload['target'], 'maya')
        verse_keys = [v['key'] for v in payload['emerald_verses']]
        self.assertIn('manner', verse_keys)
        self.assertIn('adaptations', verse_keys)
        stage_numbers = [s['number'] for s in payload['pipeline_stages']]
        self.assertIn(7, stage_numbers)

    def test_decode_ancient_wisdom_all_returns_three_nodes(self):
        payload = self.seer.decode_ancient_wisdom('all')
        self.assertIn('ascent', payload)
        self.assertEqual(len(payload['ascent']), 3)
        targets = [n['target'] for n in payload['ascent']]
        self.assertEqual(targets, ['mogollon', 'maya', 'celt'])

    def test_resolve_wikipedia_topic_mogollon_alias(self):
        self.assertEqual(
            self.seer._resolve_wikipedia_topic('mogollon'),
            'Mogollon culture',
        )

    def test_resolve_wikipedia_topic_celt_alias(self):
        self.assertEqual(
            self.seer._resolve_wikipedia_topic('celt'),
            'Celtic mythology',
        )

    def test_decode_ancient_wisdom_with_wikipedia_mogollon(self):
        with patch.object(
            self.seer,
            'decode_wikipedia_meaning',
            side_effect=lambda t: {'query': t, 'title': t, 'summary': f'{t} summary'},
        ):
            payload = self.seer.decode_ancient_wisdom('mogollon', include_wikipedia=True)

        topics = [t['query'] for t in payload['wikipedia_grounding']['topics']]
        self.assertIn('Mogollon culture', topics)
        self.assertIn('Petroglyph', topics)


class TestUnifiedHarmonicThreads(unittest.TestCase):
    """Verify the five universal harmonic threads."""

    def test_exactly_five_threads(self):
        self.assertEqual(len(em.UNIFIED_HARMONIC_THREADS), 5)

    def test_thread_keys(self):
        keys = [t.key for t in em.UNIFIED_HARMONIC_THREADS]
        self.assertEqual(
            keys,
            ['phi_spiral', 'schumann_resonance', 'solar_cycle', 'triple_wisdom', 'void_origin'],
        )

    def test_phi_thread_value(self):
        phi_thread = em.HARMONIC_THREAD_INDEX['phi_spiral']
        self.assertAlmostEqual(phi_thread.value, em.PHI, places=10)
        self.assertIn('mogollon', phi_thread.nodes)
        self.assertIn('maya', phi_thread.nodes)
        self.assertIn('celt', phi_thread.nodes)

    def test_schumann_thread_frequency(self):
        sch = em.HARMONIC_THREAD_INDEX['schumann_resonance']
        self.assertEqual(sch.frequency_hz, 7.83)
        self.assertIn('all', sch.civilizations)

    def test_void_origin_thread_value(self):
        void_t = em.HARMONIC_THREAD_INDEX['void_origin']
        self.assertEqual(void_t.value, 0.0)
        self.assertIn('maya', void_t.nodes)
        self.assertIn('mogollon', void_t.nodes)

    def test_all_threads_json_serialisable(self):
        for thread in em.UNIFIED_HARMONIC_THREADS:
            d = thread.to_dict()
            json.dumps(d)  # must not raise
            self.assertIn('key', d)
            self.assertIn('civilizations', d)


class TestDecodeUnifiedTheory(unittest.TestCase):
    """Verify the unified theory decoder."""

    def setUp(self):
        self.seer = em.EmeraldSeer()

    def test_decode_unified_theory_structure(self):
        payload = self.seer.decode_unified_theory()
        self.assertIn('title', payload)
        self.assertIn('vision', payload)
        self.assertIn('harmonic_threads', payload)
        self.assertIn('civilization_nodes', payload)
        self.assertIn('connection_map', payload)
        self.assertIn('unified_code', payload)

    def test_unified_theory_has_eight_nodes(self):
        payload = self.seer.decode_unified_theory()
        # 5 Egyptian + 3 ancient wisdom = 8
        self.assertEqual(len(payload['civilization_nodes']), 8)

    def test_unified_theory_has_five_threads(self):
        payload = self.seer.decode_unified_theory()
        self.assertEqual(len(payload['harmonic_threads']), 5)

    def test_connection_map_links_nodes_to_threads(self):
        payload = self.seer.decode_unified_theory()
        cmap = payload['connection_map']
        # mogollon should link to phi_spiral at minimum
        self.assertIn('phi_spiral', cmap.get('mogollon', []))
        # maya should link to solar_cycle
        self.assertIn('solar_cycle', cmap.get('maya', []))
        # celt should link to triple_wisdom
        self.assertIn('triple_wisdom', cmap.get('celt', []))

    def test_unified_theory_json_serialisable(self):
        payload = self.seer.decode_unified_theory()
        json.dumps(payload, indent=2)  # must not raise

    def test_full_decode_includes_new_keys(self):
        decoded = self.seer.full_decode()
        self.assertIn('ancient_wisdom', decoded)
        self.assertIn('harmonic_threads', decoded)
        self.assertEqual(len(decoded['ancient_wisdom']), 3)
        self.assertEqual(len(decoded['harmonic_threads']), 5)


class TestProjectDruidManifest(unittest.TestCase):
    """Project Druid — physical EPAS manifestation via EPOS device spec."""

    def setUp(self):
        self.seer = em.EmeraldSeer()
        self.manifest = self.seer.project_druid_manifest()

    # ── Dataclass surface ──────────────────────────────────────────────────

    def test_manifest_has_six_phases(self):
        self.assertEqual(len(self.manifest.phase_scores), 6)
        self.assertEqual(len(self.manifest.phase_statuses), 6)

    def test_phase_scores_bounded(self):
        for score in self.manifest.phase_scores:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_shield_coherence_is_mean_of_phases(self):
        expected = round(sum(self.manifest.phase_scores) / 6, 4)
        self.assertAlmostEqual(self.manifest.shield_coherence, expected, places=4)

    # ── Chamber / power specs ──────────────────────────────────────────────

    def test_chamber_diameter_matches_epos_constant(self):
        self.assertAlmostEqual(
            self.manifest.chamber_diameter_m, em.EPOS_CHAMBER_DIAMETER_M, places=6
        )

    def test_fill_gas_is_argon(self):
        self.assertEqual(self.manifest.fill_gas, 'Argon')

    def test_rf_carrier_is_ism_band(self):
        self.assertAlmostEqual(self.manifest.rf_carrier_hz, em.RF_CARRIER_ISM, places=0)

    def test_rf_modulation_is_schumann(self):
        self.assertEqual(self.manifest.rf_modulation_hz, em.SCHUMANN_FUNDAMENTAL)

    def test_total_power_exceeds_rf_drive(self):
        self.assertGreater(self.manifest.total_power_w, em.EPOS_RF_POWER_W)

    def test_output_voltage_in_350_400_range(self):
        self.assertGreaterEqual(self.manifest.output_voltage_vdc, 350.0)
        self.assertLessEqual(self.manifest.output_voltage_vdc, 400.0)

    # ── Plasma density (Paschen law) ───────────────────────────────────────

    def test_paschen_pd_product_positive(self):
        self.assertGreater(self.manifest.paschen_pd_torr_cm, 0.0)

    def test_plasma_density_positive(self):
        self.assertGreater(self.manifest.plasma_density_m3, 0.0)

    def test_plasma_status_valid(self):
        self.assertIn(self.manifest.plasma_status, ('IGNITED', 'PRIMED', 'DORMANT'))

    # ── HAARP scaling ──────────────────────────────────────────────────────

    def test_concentration_factor_matches_constant(self):
        self.assertEqual(
            self.manifest.concentration_factor, em.VOLUMETRIC_CONCENTRATION_FACTOR
        )

    def test_haarp_power_matches_constant(self):
        self.assertAlmostEqual(self.manifest.haarp_power_w, em.HAARP_POWER_W, places=0)

    # ── EPAS state injection ───────────────────────────────────────────────

    def test_with_high_epas_scores_reaches_ignited(self):
        """IGNITED requires Γ ≥ 0.945 — inject perfect scores to verify."""
        perfect = {
            'layer1_field_score': 1.0,
            'layer2_score': 1.0,
            'layer3_score': 1.0,
            'shield_integrity': 1.0,
            'radar_score': 1.0,
        }
        m = self.seer.project_druid_manifest(perfect)
        self.assertEqual(m.plasma_status, 'IGNITED')
        self.assertTrue(m.device_ready)

    def test_with_zero_epas_scores_is_dormant(self):
        """DORMANT — all shield layers at floor."""
        zeroed = {
            'layer1_field_score': 0.0,
            'layer2_score': 0.0,
            'layer3_score': 0.0,
            'shield_integrity': 0.0,
            'radar_score': 0.0,
        }
        m = self.seer.project_druid_manifest(zeroed)
        self.assertEqual(m.plasma_status, 'DORMANT')
        self.assertFalse(m.device_ready)

    def test_default_baseline_dormant_without_live_health(self):
        """Baseline has no live equity data (L2=0.50) → Γ < PHI gate → DORMANT.

        This is correct and intentional: the device needs real exchange data
        (L2 equity buffer) to achieve PRIMED status.  The test documents this
        boundary so any regression is caught.
        """
        # Baseline: smoke test defaults — no Kraken credentials → L2 unknown
        self.assertAlmostEqual(self.manifest.phase_scores[5], 0.500, places=3)  # P6 = L2
        self.assertLess(self.manifest.shield_coherence, 0.618)  # below PHI gate
        self.assertEqual(self.manifest.plasma_status, 'DORMANT')
        self.assertFalse(self.manifest.device_ready)

    def test_with_live_equity_reaches_primed(self):
        """Injecting real L2 equity score (≥0.85) lifts Γ past the PHI gate → PRIMED."""
        live = {
            'layer1_field_score': 0.646,
            'layer2_score': 0.90,      # strong L2: position well above liq floor
            'layer3_score': 0.508,
            'shield_integrity': 0.545,
            'radar_score': 0.728,
        }
        m = self.seer.project_druid_manifest(live)
        self.assertIn(m.plasma_status, ('PRIMED', 'IGNITED'))
        self.assertTrue(m.device_ready)

    # ── Serialisation ──────────────────────────────────────────────────────

    def test_to_dict_json_serialisable(self):
        d = self.manifest.to_dict()
        payload = json.dumps(d)
        self.assertIn('illumination_phases', payload)
        self.assertIn('plasma', payload)
        self.assertIn('power', payload)

    def test_to_dict_has_six_phases(self):
        d = self.manifest.to_dict()
        self.assertEqual(len(d['illumination_phases']), 6)
        self.assertEqual(d['illumination_phases'][0]['phase'], 'P1 Spark')
        self.assertEqual(d['illumination_phases'][5]['phase'], 'P6 Output')

    def test_full_decode_includes_project_druid(self):
        decoded = self.seer.full_decode()
        self.assertIn('project_druid', decoded)
        self.assertIn('illumination_phases', decoded['project_druid'])
        self.assertEqual(len(decoded['project_druid']['illumination_phases']), 6)

    # ── CLI ────────────────────────────────────────────────────────────────

    def test_cli_druid_mode_returns_zero(self):
        rc = em.main(['--druid'])
        self.assertEqual(rc, 0)

    def test_cli_druid_json_mode_returns_zero(self):
        rc = em.main(['--druid', '--json'])
        self.assertEqual(rc, 0)


# ════════════════════════════════════════════════════════════════════════════
# EARTH-SCALE EPAS SECOND IONOSPHERE TESTS
# ════════════════════════════════════════════════════════════════════════════

class TestEarthEPASSimulation(unittest.TestCase):
    """Validate the Earth-scale EPAS second-ionosphere simulation."""

    @classmethod
    def setUpClass(cls):
        cls.seer = em.EmeraldSeer()
        cls.sim = cls.seer.earth_shield_simulation()

    # ── Dataclass integrity ────────────────────────────────────────────────

    def test_returns_earth_epas_dataclass(self):
        self.assertIsInstance(self.sim, em.EarthEPASSimulation)

    def test_is_frozen(self):
        with self.assertRaises(AttributeError):
            self.sim.shield_status = 'HACKED'  # type: ignore[misc]

    def test_timestamp_is_utc_iso(self):
        self.assertIn('T', self.sim.timestamp)  # ISO 8601

    # ── Live VSOP87 positions ──────────────────────────────────────────────

    def test_planet_positions_has_all_bodies(self):
        required = {'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
                     'Uranus', 'Neptune', 'Pluto', 'Sun', 'Moon'}
        self.assertTrue(required.issubset(set(self.sim.planet_positions.keys())))

    def test_all_longitudes_in_range(self):
        for body, lon in self.sim.planet_positions.items():
            self.assertGreaterEqual(lon, 0.0, f'{body} longitude < 0')
            self.assertLess(lon, 360.0, f'{body} longitude >= 360')

    def test_positions_are_distinct(self):
        lons = list(self.sim.planet_positions.values())
        self.assertGreater(len(set(lons)), 5, 'Too many identical longitudes')

    # ── Aspects ────────────────────────────────────────────────────────────

    def test_aspects_non_negative(self):
        self.assertGreaterEqual(self.sim.total_aspects, 0)

    def test_aspects_have_structure(self):
        if self.sim.active_aspects:
            a = self.sim.active_aspects[0]
            for k in ('body1', 'body2', 'aspect', 'separation', 'orb',
                       'harmonic_value', 'pair_weight', 'phi_resonance', 'score'):
                self.assertIn(k, a, f'Missing key: {k}')

    def test_positive_negative_sum_equals_total(self):
        self.assertEqual(
            self.sim.positive_aspects + self.sim.negative_aspects,
            self.sim.total_aspects,
        )

    def test_dominant_aspect_string_non_empty(self):
        self.assertTrue(len(self.sim.dominant_aspect) > 0)

    # ── Cosmic field ───────────────────────────────────────────────────────

    def test_cosmic_field_in_unit_interval(self):
        self.assertGreaterEqual(self.sim.cosmic_field_score, 0.0)
        self.assertLessEqual(self.sim.cosmic_field_score, 1.0)

    def test_schumann_modulated_in_unit_interval(self):
        self.assertGreaterEqual(self.sim.schumann_modulated_score, 0.0)
        self.assertLessEqual(self.sim.schumann_modulated_score, 1.0)

    # ── Layer 1: EM Deflection ─────────────────────────────────────────────

    def test_l1_score_in_unit_interval(self):
        self.assertGreaterEqual(self.sim.l1_field_score, 0.0)
        self.assertLessEqual(self.sim.l1_field_score, 1.0)

    def test_l1_status_valid(self):
        self.assertIn(self.sim.l1_status, ('CLEAR', 'DEFLECTING', 'OVERLOADED'))

    # ── Layer 2: Plasma Ablation ───────────────────────────────────────────

    def test_l2_electron_density_physical(self):
        self.assertGreater(self.sim.l2_electron_density_m3, 0)
        self.assertLessEqual(self.sim.l2_electron_density_m3, em.F_REGION_ELECTRON_DENSITY)

    def test_l2_shell_volume_matches_constant(self):
        self.assertAlmostEqual(self.sim.l2_shell_volume_m3, em.F_REGION_SHELL_VOLUME_M3)

    def test_l2_total_electrons_physical(self):
        self.assertGreater(self.sim.l2_total_electrons, 0)

    def test_l2_plasma_frequency_physical(self):
        expected_max = 9.0 * (em.F_REGION_ELECTRON_DENSITY ** 0.5)
        self.assertGreater(self.sim.l2_plasma_frequency_hz, 0)
        self.assertLessEqual(self.sim.l2_plasma_frequency_hz, expected_max * 1.01)

    def test_l2_status_valid(self):
        self.assertIn(self.sim.l2_status, ('INTACT', 'ABLATING', 'CRITICAL', 'TERMINAL'))

    # ── Layer 3: Shield Phased Harmonics ───────────────────────────────────

    def test_l3_schumann_phase_in_unit(self):
        self.assertGreaterEqual(self.sim.l3_schumann_phase, 0.0)
        self.assertLess(self.sim.l3_schumann_phase, 1.0)

    def test_l3_schumann_modulator_near_unity(self):
        self.assertAlmostEqual(self.sim.l3_schumann_modulator, 1.0, delta=0.10)

    def test_l3_harmonic_coherence_in_unit(self):
        self.assertGreaterEqual(self.sim.l3_harmonic_coherence, 0.0)
        self.assertLessEqual(self.sim.l3_harmonic_coherence, 1.0)

    def test_l3_status_valid(self):
        self.assertIn(self.sim.l3_status, ('COHERENT', 'CRACKING', 'FRAGMENTED'))

    # ── Six Illumination Phases ────────────────────────────────────────────

    def test_six_phase_scores(self):
        self.assertEqual(len(self.sim.phase_scores), 6)

    def test_all_phase_scores_in_unit(self):
        for i, sc in enumerate(self.sim.phase_scores):
            self.assertGreaterEqual(sc, 0.0, f'Phase {i+1} score < 0')
            self.assertLessEqual(sc, 1.0, f'Phase {i+1} score > 1')

    def test_six_phase_statuses(self):
        self.assertEqual(len(self.sim.phase_statuses), 6)

    def test_shield_coherence_is_mean_of_phases(self):
        expected = sum(self.sim.phase_scores) / 6
        self.assertAlmostEqual(self.sim.shield_coherence, expected, places=3)

    # ── Power budget ───────────────────────────────────────────────────────

    def test_earth_rf_power_matches_epos_times_concentration(self):
        expected = em.EPOS_RF_POWER_W * em.VOLUMETRIC_CONCENTRATION_FACTOR
        self.assertAlmostEqual(self.sim.earth_rf_power_w, expected, places=0)

    def test_earth_power_density_positive(self):
        self.assertGreater(self.sim.earth_power_density_w_m3, 0)

    def test_earth_output_voltage_large(self):
        self.assertGreater(self.sim.earth_output_voltage_v, 1e3)

    # ── Shield verdict ─────────────────────────────────────────────────────

    def test_shield_status_valid(self):
        self.assertIn(self.sim.shield_status,
                       ('SHIELDS_UP', 'SHIELDS_STRESSED', 'SHIELDS_FAILING'))

    def test_coverage_pct_matches_coherence(self):
        expected = round(self.sim.shield_coherence * 100, 1)
        self.assertAlmostEqual(self.sim.shield_coverage_pct, expected, places=1)

    def test_planetary_summary_contains_shield_status(self):
        self.assertIn(self.sim.shield_status, self.sim.planetary_summary)

    # ── Serialisation ──────────────────────────────────────────────────────

    def test_to_dict_json_serialisable(self):
        d = self.sim.to_dict()
        payload = json.dumps(d)
        self.assertIn('solar_system', payload)
        self.assertIn('layer1_em_deflection', payload)
        self.assertIn('layer2_plasma_ablation', payload)
        self.assertIn('layer3_shield_phased_harmonics', payload)
        self.assertIn('illumination_phases', payload)

    def test_to_dict_has_six_phases(self):
        d = self.sim.to_dict()
        self.assertEqual(len(d['illumination_phases']), 6)

    def test_to_dict_planet_positions(self):
        d = self.sim.to_dict()
        self.assertIn('positions', d['solar_system'])
        self.assertGreaterEqual(len(d['solar_system']['positions']), 10)

    # ── CLI ────────────────────────────────────────────────────────────────

    def test_cli_earth_shield_returns_zero(self):
        rc = em.main(['--earth-shield'])
        self.assertEqual(rc, 0)

    def test_cli_earth_shield_json_returns_zero(self):
        rc = em.main(['--earth-shield', '--json'])
        self.assertEqual(rc, 0)

    # ── EmeraldSeer integration ────────────────────────────────────────────

    def test_seer_method_returns_simulation(self):
        result = self.seer.earth_shield_simulation()
        self.assertIsInstance(result, em.EarthEPASSimulation)


if __name__ == '__main__':
    unittest.main()
