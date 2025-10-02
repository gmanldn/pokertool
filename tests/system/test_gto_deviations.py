#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for GTO Deviations Module
================================

Comprehensive tests for profitable GTO deviation calculations.

Author: PokerTool Development Team
Version: 1.0.0
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from pokertool.gto_deviations import (
    ActionType,
    PopulationTendency,
    OpponentModel,
    Deviation,
    MaximumExploitationFinder,
    NodeLocker,
    StrategySimplifier,
    GTODeviationCalculator,
    create_opponent_model,
    find_deviations
)


class TestPopulationTendency:
    """Test PopulationTendency dataclass."""
    
    def test_is_significant_with_good_data(self):
        """Test significance with sufficient confidence and samples."""
        tendency = PopulationTendency(
            action=ActionType.FOLD,
            frequency=0.75,
            sample_size=50,
            confidence=0.85
        )
        assert tendency.is_significant()
    
    def test_is_not_significant_low_confidence(self):
        """Test not significant with low confidence."""
        tendency = PopulationTendency(
            action=ActionType.FOLD,
            frequency=0.75,
            sample_size=50,
            confidence=0.60
        )
        assert not tendency.is_significant()
    
    def test_is_not_significant_small_sample(self):
        """Test not significant with small sample."""
        tendency = PopulationTendency(
            action=ActionType.FOLD,
            frequency=0.75,
            sample_size=20,
            confidence=0.85
        )
        assert not tendency.is_significant()


class TestOpponentModel:
    """Test OpponentModel functionality."""
    
    def test_create_opponent_model(self):
        """Test creating opponent model."""
        opponent = create_opponent_model("test_player", vpip=0.30, pfr=0.20, aggression=1.5)
        assert opponent.player_id == "test_player"
        assert opponent.overall_vpip == 0.30
        assert opponent.overall_pfr == 0.20
        assert opponent.aggression_factor == 1.5
    
    def test_add_and_get_tendency(self):
        """Test adding and retrieving tendencies."""
        opponent = OpponentModel(player_id="test")
        tendency = PopulationTendency(
            action=ActionType.FOLD,
            frequency=0.80,
            sample_size=40,
            confidence=0.90
        )
        opponent.add_tendency("3bet_situation", tendency)
        
        retrieved = opponent.get_tendency("3bet_situation")
        assert retrieved == tendency
    
    def test_is_tight(self):
        """Test tight player identification."""
        tight_opponent = OpponentModel(player_id="tight", overall_vpip=0.15)
        loose_opponent = OpponentModel(player_id="loose", overall_vpip=0.40)
        
        assert tight_opponent.is_tight()
        assert not loose_opponent.is_tight()
    
    def test_is_aggressive(self):
        """Test aggressive player identification."""
        aggressive = OpponentModel(player_id="agg", aggression_factor=2.5)
        passive = OpponentModel(player_id="pass", aggression_factor=0.8)
        
        assert aggressive.is_aggressive()
        assert not passive.is_aggressive()
    
    def test_get_style_tag(self):
        """Test TAG style identification."""
        tag = OpponentModel(player_id="tag", overall_vpip=0.18, aggression_factor=2.5)
        assert tag.get_style() == "TAG"
    
    def test_get_style_lag(self):
        """Test LAG style identification."""
        lag = OpponentModel(player_id="lag", overall_vpip=0.35, aggression_factor=2.5)
        assert lag.get_style() == "LAG"
    
    def test_get_style_tight_passive(self):
        """Test tight-passive style."""
        tp = OpponentModel(player_id="tp", overall_vpip=0.15, aggression_factor=1.0)
        assert tp.get_style() == "Tight-Passive"
    
    def test_get_style_loose_passive(self):
        """Test loose-passive style."""
        lp = OpponentModel(player_id="lp", overall_vpip=0.40, aggression_factor=1.0)
        assert lp.get_style() == "Loose-Passive"


class TestMaximumExploitationFinder:
    """Test exploitation finding logic."""
    
    def test_find_exploits_over_folding(self):
        """Test finding exploits against over-folding."""
        finder = MaximumExploitationFinder()
        
        opponent = OpponentModel(player_id="folder")
        opponent.add_tendency(
            "test_spot",
            PopulationTendency(
                action=ActionType.FOLD,
                frequency=0.75,
                sample_size=50,
                confidence=0.85
            )
        )
        
        gto_strategy = {
            ActionType.FOLD: 0.3,
            ActionType.CALL: 0.4,
            ActionType.BET: 0.3
        }
        
        deviations = finder.find_exploits(opponent, "test_spot", gto_strategy)
        
        assert len(deviations) > 0
        assert deviations[0].ev_gain > 0
    
    def test_find_exploits_no_significant_tendency(self):
        """Test no exploits when no significant tendencies."""
        finder = MaximumExploitationFinder()
        
        opponent = OpponentModel(player_id="balanced")
        # No tendencies added
        
        gto_strategy = {ActionType.FOLD: 0.3, ActionType.CALL: 0.4, ActionType.BET: 0.3}
        
        deviations = finder.find_exploits(opponent, "test_spot", gto_strategy)
        
        assert len(deviations) == 0


class TestNodeLocker:
    """Test node locking functionality."""
    
    def test_lock_and_unlock_node(self):
        """Test basic lock/unlock operations."""
        locker = NodeLocker()
        
        locker.lock_node("test_node", ActionType.BET, "test reason")
        assert locker.is_locked("test_node")
        assert locker.get_action("test_node") == ActionType.BET
        
        locker.unlock_node("test_node")
        assert not locker.is_locked("test_node")
    
    def test_apply_locking_strategy(self):
        """Test automatic locking strategy generation."""
        locker = NodeLocker()
        
        opponent = OpponentModel(player_id="test")
        opponent.add_tendency(
            "spot1",
            PopulationTendency(
                action=ActionType.FOLD,
                frequency=0.10,  # Rarely folds
                sample_size=40,
                confidence=0.85
            )
        )
        
        locks = locker.apply_locking_strategy(opponent)
        
        assert len(locks) > 0


class TestStrategySimplifier:
    """Test strategy simplification."""
    
    def test_simplify_removes_low_frequency(self):
        """Test that simplification removes low-frequency actions."""
        simplifier = StrategySimplifier()
        
        strategy = {
            ActionType.FOLD: 0.05,  # Should be removed
            ActionType.CALL: 0.45,
            ActionType.BET: 0.50
        }
        
        simplified = simplifier.simplify(strategy, min_frequency=0.10)
        
        assert ActionType.FOLD not in simplified
        assert ActionType.CALL in simplified
        assert ActionType.BET in simplified
    
    def test_simplify_renormalizes(self):
        """Test that simplification renormalizes frequencies."""
        simplifier = StrategySimplifier()
        
        strategy = {
            ActionType.CALL: 0.45,
            ActionType.BET: 0.50,
            ActionType.RAISE: 0.05
        }
        
        simplified = simplifier.simplify(strategy, min_frequency=0.10)
        
        # Should sum to 1.0
        assert abs(sum(simplified.values()) - 1.0) < 0.01
    
    def test_merge_similar_actions(self):
        """Test merging similar actions."""
        simplifier = StrategySimplifier()
        
        strategy = {
            ActionType.BET: 0.30,
            ActionType.RAISE: 0.20,
            ActionType.CALL: 0.50
        }
        
        merged = simplifier.merge_similar_actions(strategy)
        
        # Should merge BET and RAISE
        assert not (ActionType.BET in merged and ActionType.RAISE in merged)


class TestGTODeviationCalculator:
    """Test main GTO deviation calculator."""
    
    def test_calculate_deviations(self):
        """Test full deviation calculation."""
        calculator = GTODeviationCalculator()
        
        opponent = OpponentModel(player_id="fish")
        opponent.add_tendency(
            "test_spot",
            PopulationTendency(
                action=ActionType.FOLD,
                frequency=0.80,
                sample_size=50,
                confidence=0.90
            )
        )
        
        gto_strategy = {
            ActionType.FOLD: 0.3,
            ActionType.CALL: 0.4,
            ActionType.BET: 0.3
        }
        
        exploit_strategy, deviations = calculator.calculate_deviations(
            opponent, "test_spot", gto_strategy
        )
        
        assert len(deviations) > 0
        assert len(exploit_strategy) > 0
        assert abs(sum(exploit_strategy.values()) - 1.0) < 0.01
    
    def test_calculate_exploitability(self):
        """Test exploitability calculation."""
        calculator = GTODeviationCalculator()
        
        balanced_strategy = {
            ActionType.FOLD: 0.3,
            ActionType.CALL: 0.3,
            ActionType.BET: 0.4
        }
        
        unbalanced_strategy = {
            ActionType.FOLD: 0.8,
            ActionType.CALL: 0.1,
            ActionType.BET: 0.1
        }
        
        opponent = OpponentModel(player_id="test")
        
        balanced_exploit = calculator.calculate_exploitability(balanced_strategy, opponent)
        unbalanced_exploit = calculator.calculate_exploitability(unbalanced_strategy, opponent)
        
        # Unbalanced should be more exploitable
        assert unbalanced_exploit > balanced_exploit
    
    def test_generate_report(self):
        """Test deviation report generation."""
        calculator = GTODeviationCalculator()
        
        opponent = OpponentModel(
            player_id="test",
            overall_vpip=0.30,
            overall_pfr=0.20,
            aggression_factor=1.5,
            sample_hands=100
        )
        
        deviations = [
            Deviation(
                situation="test",
                gto_action=ActionType.CALL,
                gto_frequency=0.5,
                exploitative_action=ActionType.BET,
                exploitative_frequency=0.6,
                ev_gain=0.5,
                confidence=0.85,
                reasoning="Test"
            )
        ]
        
        report = calculator.generate_report(opponent, deviations)
        
        assert 'opponent_style' in report
        assert 'deviation_count' in report
        assert report['deviation_count'] == 1
        assert 'total_ev_gain' in report


class TestConvenienceFunctions:
    """Test convenience helper functions."""
    
    def test_find_deviations_convenience(self):
        """Test find_deviations convenience function."""
        opponent = create_opponent_model("test", vpip=0.40, pfr=0.10, aggression=0.5)
        opponent.add_tendency(
            "test_spot",
            PopulationTendency(
                action=ActionType.FOLD,
                frequency=0.75,
                sample_size=50,
                confidence=0.85
            )
        )
        
        gto_strategy = {
            'fold': 0.3,
            'call': 0.4,
            'bet': 0.3
        }
        
        deviations = find_deviations(opponent, "test_spot", gto_strategy)
        
        assert isinstance(deviations, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
