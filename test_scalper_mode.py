import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import asyncio
import warnings

# Add current directory to path
sys.path.append(os.getcwd())

# Some ecosystem init paths create an event loop and don't close it.
# Keep unit test output clean (this does not affect trading runtime).
warnings.simplefilter("ignore", ResourceWarning)

from aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG

class TestScalperMode(unittest.TestCase):
    def setUp(self):
        # Configure global CONFIG for testing
        self.original_config = CONFIG.copy()
        CONFIG['MIN_TRADE_USD'] = 10.0
        CONFIG['PORTFOLIO_RISK_BUDGET'] = 0.9
        CONFIG['ENABLE_REBALANCING'] = False
        CONFIG['USE_SERVER_SIDE_ORDERS'] = False
        
        # Create a list of patches
        self.patches = [
            patch('aureon_unified_ecosystem.UnifiedExchangeClient'),
            patch('aureon_unified_ecosystem.MultiExchangeClient'),
            patch('aureon_unified_ecosystem.MyceliumNetwork'),
            patch('aureon_unified_ecosystem.ProbabilityLoader'),
            patch('aureon_unified_ecosystem.UnifiedSniperBrain'),
            patch('aureon_unified_ecosystem.MinerStateConnector'),
            patch('aureon_unified_ecosystem.UnifiedStateAggregator'),
            patch('aureon_unified_ecosystem.AdaptiveLearningEngine'),
            patch('aureon_unified_ecosystem.PredictionValidator'),
            patch('aureon_unified_ecosystem.AureonWisdomScanner'),
            patch('aureon_unified_ecosystem.NewsFeed'),
            patch('aureon_unified_ecosystem.KnowledgeBase'),
            patch('aureon_unified_ecosystem.GlobalHarmonicField'),
            patch('aureon_unified_ecosystem.QuantumTelescope'),
            patch('aureon_unified_ecosystem.CostBasisTracker'),
            patch('aureon_unified_ecosystem.IraCelticSniper'),
            patch('aureon_unified_ecosystem.get_platform_fee', return_value=0.001),
            patch('aureon_unified_ecosystem.has_one_minute_profit_consensus', return_value=(True, "OK", {'prob_quick': 0.9, 'confidence': 0.9, 'estimated_seconds': 60}))
        ]
        
        # Start all patches
        for p in self.patches:
            p.start()
            
        self.ecosystem = AureonKrakenEcosystem()
        self.ecosystem.dry_run = False
        
        # Clear restored positions
        self.ecosystem.positions = {}
        
        self.ecosystem.exchange = MagicMock()
        self.ecosystem.mycelium = MagicMock()
        self.ecosystem.client = MagicMock()
        self.ecosystem.tracker = MagicMock()
        self.ecosystem.capital_pool = MagicMock()
        self.ecosystem.lattice = MagicMock()
        self.ecosystem.auris = MagicMock()
        self.ecosystem.prime_sizer = MagicMock()
        
        # Mock Kraken client specifically for volume check
        kraken_client = MagicMock()
        kraken_client.get_symbol_filters.return_value = {'min_qty': 0.0}
        self.ecosystem.client.clients = {'kraken': kraken_client}
        
        # Mock internal methods
        self.ecosystem.should_enter_trade = MagicMock(return_value=True)
        self.ecosystem.ensure_quote_liquidity = MagicMock(return_value=(True, 1000.0, None))
        self.ecosystem._detect_exchange_for_symbol = MagicMock(return_value='kraken')
        self.ecosystem._get_quote_asset = MagicMock(return_value='USD')
        self.ecosystem._is_duplicate_across_exchanges = MagicMock(return_value=False)
        
        # Setup basic mocks
        self.ecosystem.tracker.balance = 1000.0
        self.ecosystem.tracker.trading_halted = False
        self.ecosystem.tracker.calculate_position_size.return_value = 0.1
        self.ecosystem.capital_pool.get_recommended_position_size.return_value = 100.0
        self.ecosystem.lattice.get_state.return_value = {'risk_mod': 1.0}
        self.ecosystem.auris.should_trade_imperial.return_value = (True, "OK")
        self.ecosystem.auris.should_trade_earth.return_value = (True, "OK")
        self.ecosystem.auris.update_hnc_state.return_value = {'hnc_frequency': 256.0}
        self.ecosystem.auris.get_hnc_position_modifier.return_value = 1.0
        self.ecosystem.prime_sizer.get_next_size.return_value = 10.0
        
        # Mock client methods
        self.ecosystem.client.get_all_balances.return_value = {'kraken': {'USD': 1000.0}}
        self.ecosystem.client.convert_to_quote.return_value = 100.0
        self.ecosystem.client.place_market_order.return_value = {
            'id': '123', 
            'status': 'closed', 
            'filled': 0.01, 
            'price': 50000.0,
            'fills': [{'qty': 0.01, 'price': 50000.0, 'commission': 0.1}]
        }

    def tearDown(self):
        CONFIG.update(self.original_config)
        for p in reversed(self.patches):
            p.stop()

        # Ensure no lingering loop is set as current for subsequent tests.
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass

    def test_scalper_mode_activation(self):
        """Test that Scalper Mode activates when Queen Signal > 0.8"""
        
        opp = {
            'symbol': 'BTC/USD',
            'price': 50000.0,
            'queen_signal': 0.85,
            'source': 'test',
            'exchange': 'kraken',
            'coherence': 0.9,
            'score': 90,
            'change24h': 1.5,
            'dominant_node': 'Queen',
            'learned_recommendation': {}
        }
        
        self.ecosystem.exchange.get_balance.return_value = 1000.0
        self.ecosystem.cash_balance_gbp = 1000.0
        self.ecosystem.total_equity_gbp = 1000.0
        
        self.ecosystem.open_position(opp)
        
        self.assertIn('BTC/USD', self.ecosystem.positions)
        position = self.ecosystem.positions['BTC/USD']
        
        self.assertEqual(position.learned_tp_pct, 0.005, "Scalper Mode TP should be 0.5%")
