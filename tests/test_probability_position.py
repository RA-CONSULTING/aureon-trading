#!/usr/bin/env python3
"""
Unit tests for probability matrix position adjustment logic.
Tests win-rate boosts, P&L adjustments, and feed/close flows.
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import time
from unittest.mock import patch, MagicMock

# Import the module under test
from hnc_probability_matrix import (
    HNCProbabilityIntegration, 
    PositionData,
    ProbabilityMatrix,
    HourlyProbabilityWindow,
    ProbabilityState,
)


class TestPositionDataFeed:
    """Test position data feeding to probability matrix."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Patch file loading to avoid disk dependencies
        with patch.object(HNCProbabilityIntegration, '_load_persisted_outcomes'):
            self.integration = HNCProbabilityIntegration()
    
    def test_feed_position_data_creates_entry(self):
        """Test that feeding position data creates a PositionData entry."""
        self.integration.feed_position_data(
            symbol='BTCUSDC',
            exchange='binance',
            entry_price=50000.0,
            entry_time=time.time() - 3600,  # 1 hour ago
            quantity=0.1,
            entry_value=5000.0,
            current_price=51000.0,
            is_historical=False,
            momentum=2.0,
            coherence=0.85,
        )
        
        assert 'BTCUSDC' in self.integration.position_data
        pos = self.integration.position_data['BTCUSDC']
        assert pos.symbol == 'BTCUSDC'
        assert pos.exchange == 'binance'
        assert pos.entry_price == 50000.0
        assert pos.current_price == 51000.0
        assert pos.unrealized_pnl > 0  # Price went up
        assert pos.hold_duration_mins > 0
    
    def test_feed_position_data_calculates_pnl(self):
        """Test that P&L is calculated correctly."""
        self.integration.feed_position_data(
            symbol='ETHUSDC',
            exchange='binance',
            entry_price=2000.0,
            entry_time=time.time() - 1800,  # 30 mins ago
            quantity=1.0,
            entry_value=2000.0,
            current_price=2100.0,  # 5% up
        )
        
        pos = self.integration.position_data['ETHUSDC']
        assert pos.current_value == 2100.0
        assert pos.unrealized_pnl == 100.0
        assert abs(pos.unrealized_pnl_pct - 5.0) < 0.01


class TestPositionClose:
    """Test position close recording."""
    
    def setup_method(self):
        with patch.object(HNCProbabilityIntegration, '_load_persisted_outcomes'):
            with patch.object(HNCProbabilityIntegration, '_persist_outcomes'):
                self.integration = HNCProbabilityIntegration()
    
    def test_feed_position_close_records_outcome(self):
        """Test that closing a position records the outcome."""
        # First, feed the position
        self.integration.feed_position_data(
            symbol='SOLUSDC',
            exchange='binance',
            entry_price=100.0,
            entry_time=time.time() - 600,
            quantity=10.0,
            entry_value=1000.0,
            current_price=110.0,
        )
        
        # Now close it
        with patch.object(self.integration, '_persist_outcomes'):
            self.integration.feed_position_close(
                symbol='SOLUSDC',
                exit_price=110.0,
                realized_pnl=95.0,  # After fees
                exit_reason='TP_HIT',
            )
        
        assert 'SOLUSDC' in self.integration.position_outcomes
        outcomes = self.integration.position_outcomes['SOLUSDC']
        assert len(outcomes) == 1
        assert outcomes[0]['win'] == True
        assert outcomes[0]['exit_reason'] == 'TP_HIT'
        assert outcomes[0]['realized_pnl'] == 95.0
    
    def test_feed_position_close_removes_active_position(self):
        """Test that closing removes from active positions."""
        self.integration.feed_position_data(
            symbol='ADAUSDC',
            exchange='binance',
            entry_price=0.5,
            entry_time=time.time() - 300,
            quantity=1000.0,
            entry_value=500.0,
            current_price=0.48,
        )
        
        assert 'ADAUSDC' in self.integration.position_data
        
        with patch.object(self.integration, '_persist_outcomes'):
            self.integration.feed_position_close(
                symbol='ADAUSDC',
                exit_price=0.48,
                realized_pnl=-25.0,  # Loss
                exit_reason='SL_HIT',
            )
        
        assert 'ADAUSDC' not in self.integration.position_data

    def test_feed_position_close_requires_penny_target(self):
        """Positive P&L below target_net should not count as a win."""
        self.integration.feed_position_data(
            symbol='XRPUSDC',
            exchange='binance',
            entry_price=0.5,
            entry_time=time.time() - 120,
            quantity=1000.0,
            entry_value=500.0,
            current_price=0.5001,
        )

        with patch.object(self.integration, '_persist_outcomes'):
            self.integration.feed_position_close(
                symbol='XRPUSDC',
                exit_price=0.5001,
                realized_pnl=0.005,  # Positive but below $0.01
                exit_reason='MANUAL',
            )

        outcomes = self.integration.position_outcomes['XRPUSDC']
        assert outcomes[0]['win'] is False
        assert outcomes[0]['penny_hit'] is False


class TestWinRateCalculation:
    """Test win rate statistics."""
    
    def setup_method(self):
        with patch.object(HNCProbabilityIntegration, '_load_persisted_outcomes'):
            self.integration = HNCProbabilityIntegration()
        
        # Pre-populate some outcomes
        self.integration.position_outcomes = {
            'BTCUSDC': [
                {'win': True, 'realized_pnl': 50, 'hold_duration_mins': 30},
                {'win': True, 'realized_pnl': 30, 'hold_duration_mins': 45},
                {'win': False, 'realized_pnl': -20, 'hold_duration_mins': 15},
            ],
            'ETHUSDC': [
                {'win': False, 'realized_pnl': -10, 'hold_duration_mins': 10},
                {'win': False, 'realized_pnl': -15, 'hold_duration_mins': 20},
            ],
        }
    
    def test_win_rate_per_symbol(self):
        """Test win rate calculation for a specific symbol."""
        stats = self.integration.get_position_win_rate('BTCUSDC')
        
        assert stats['symbol'] == 'BTCUSDC'
        assert stats['trades'] == 3
        assert stats['wins'] == 2
        assert stats['losses'] == 1
        assert abs(stats['win_rate'] - 0.6667) < 0.01
    
    def test_win_rate_overall(self):
        """Test overall win rate across all symbols."""
        stats = self.integration.get_position_win_rate()
        
        assert stats['trades'] == 5
        assert stats['wins'] == 2
        assert stats['losses'] == 3
        assert abs(stats['win_rate'] - 0.4) < 0.01
    
    def test_win_rate_no_trades(self):
        """Test win rate for symbol with no trades."""
        stats = self.integration.get_position_win_rate('XRPUSDC')
        
        assert stats['trades'] == 0
        assert stats['win_rate'] == 0.5  # Default neutral


class TestPositionAdjustment:
    """Test probability adjustment based on position data."""
    
    def setup_method(self):
        with patch.object(HNCProbabilityIntegration, '_load_persisted_outcomes'):
            self.integration = HNCProbabilityIntegration()
    
    def test_high_winrate_boosts_probability(self):
        """Test that high win rate gives positive adjustment."""
        # Set up high win rate history
        self.integration.position_outcomes = {
            'BTCUSDC': [
                {'win': True, 'hold_duration_mins': 30},
                {'win': True, 'hold_duration_mins': 45},
                {'win': True, 'hold_duration_mins': 20},
                {'win': False, 'hold_duration_mins': 15},
            ],
        }
        
        adj, reason = self.integration._compute_position_adjustment('BTCUSDC')
        
        assert adj > 0, "High win rate should give positive adjustment"
        assert 'winrate' in reason.lower()
    
    def test_low_winrate_reduces_probability(self):
        """Test that low win rate gives negative adjustment."""
        self.integration.position_outcomes = {
            'ETHUSDC': [
                {'win': False, 'hold_duration_mins': 10},
                {'win': False, 'hold_duration_mins': 20},
                {'win': False, 'hold_duration_mins': 15},
                {'win': True, 'hold_duration_mins': 30},
            ],
        }
        
        adj, reason = self.integration._compute_position_adjustment('ETHUSDC')
        
        assert adj < 0, "Low win rate should give negative adjustment"
    
    def test_profitable_position_boosts(self):
        """Test that an active profitable position gives a boost."""
        # Add an active profitable position
        self.integration.feed_position_data(
            symbol='SOLUSDC',
            exchange='binance',
            entry_price=100.0,
            entry_time=time.time() - 1800,
            quantity=10.0,
            entry_value=1000.0,
            current_price=115.0,  # 15% profit
        )
        
        adj, reason = self.integration._compute_position_adjustment('SOLUSDC')
        
        assert adj > 0, "Profitable position should give positive adjustment"
        assert 'pos' in reason.lower()
    
    def test_losing_position_reduces(self):
        """Test that an active losing position reduces probability."""
        self.integration.feed_position_data(
            symbol='ADAUSDC',
            exchange='binance',
            entry_price=0.5,
            entry_time=time.time() - 1800,
            quantity=1000.0,
            entry_value=500.0,
            current_price=0.47,  # -6% loss
        )
        
        adj, reason = self.integration._compute_position_adjustment('ADAUSDC')
        
        assert adj < 0, "Losing position should give negative adjustment"

    def test_gross_green_but_net_red_reduces(self):
        """If costs make net P&L negative, adjustment should be negative."""
        self.integration.feed_position_data(
            symbol='DOTUSDC',
            exchange='binance',
            entry_price=10.0,
            entry_time=time.time() - 600,
            quantity=100.0,
            entry_value=1000.0,
            current_price=10.01,  # +$1 gross
            # Provide cost context: 0.3% per leg => ~$6 costs total => net negative
            target_net=0.0001,
            total_rate=0.003,
        )

        adj, reason = self.integration._compute_position_adjustment('DOTUSDC')
        assert adj < 0, "Net-negative position should reduce probability"
        assert 'net' in reason.lower()
    
    def test_no_data_neutral_adjustment(self):
        """Test that no position data gives neutral adjustment."""
        adj, reason = self.integration._compute_position_adjustment('UNKNOWNUSDC')
        
        assert adj == 0, "No data should give zero adjustment"
        assert 'no pos data' in reason.lower()


class TestActivePosistionsSummary:
    """Test active positions summary."""
    
    def setup_method(self):
        with patch.object(HNCProbabilityIntegration, '_load_persisted_outcomes'):
            self.integration = HNCProbabilityIntegration()
    
    def test_empty_summary(self):
        """Test summary with no positions."""
        summary = self.integration.get_active_positions_summary()
        
        assert summary['count'] == 0
        assert summary['positions'] == []
    
    def test_summary_with_positions(self):
        """Test summary with active positions."""
        self.integration.feed_position_data(
            symbol='BTCUSDC',
            exchange='binance',
            entry_price=50000.0,
            entry_time=time.time() - 3600,
            quantity=0.1,
            entry_value=5000.0,
            current_price=51000.0,
        )
        self.integration.feed_position_data(
            symbol='ETHUSDC',
            exchange='kraken',
            entry_price=2000.0,
            entry_time=time.time() - 1800,
            quantity=2.0,
            entry_value=4000.0,
            current_price=1950.0,
        )
        
        summary = self.integration.get_active_positions_summary()
        
        assert summary['count'] == 2
        assert summary['total_value'] > 0
        assert len(summary['positions']) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
