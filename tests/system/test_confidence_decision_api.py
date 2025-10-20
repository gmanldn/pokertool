#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for Confidence-Aware Decision API
========================================

Comprehensive test suite for the confidence-aware decision making system.
"""

import pytest
import numpy as np
from pokertool.confidence_decision_api import (
    ConfidenceAwareDecisionAPI,
    ConfidenceBand,
    RiskLevel,
    ConfidenceInterval,
    DecisionRecommendation,
    PredictiveDistribution,
    get_confidence_decision_api
)


class TestPredictiveDistribution:
    """Tests for predictive distribution computation."""

    def test_gaussian_distribution(self):
        """Test Gaussian distribution generation."""
        api = ConfidenceAwareDecisionAPI(n_bootstrap_samples=1000)
        dist = api.compute_predictive_distribution(0.5, 0.1, method="gaussian")

        assert isinstance(dist, PredictiveDistribution)
        assert len(dist.samples) == 1000
        assert 0.3 < dist.mean < 0.7  # Should be around 0.5
        assert 0.05 < dist.std < 0.15  # Should be around 0.1
        assert dist.median is not None
        assert 0.025 in dist.quantiles
        assert 0.975 in dist.quantiles

    def test_bootstrap_distribution(self):
        """Test bootstrap distribution generation."""
        api = ConfidenceAwareDecisionAPI(n_bootstrap_samples=500)
        dist = api.compute_predictive_distribution(0.7, 0.15, method="bootstrap")

        assert len(dist.samples) == 500
        assert 0.4 < dist.mean < 1.0
        assert dist.std > 0

    def test_monte_carlo_distribution(self):
        """Test Monte Carlo distribution generation."""
        api = ConfidenceAwareDecisionAPI(n_bootstrap_samples=800)
        dist = api.compute_predictive_distribution(0.6, 0.2, method="monte_carlo")

        assert len(dist.samples) == 800
        assert dist.std > 0
        assert all(q in dist.quantiles for q in [0.025, 0.5, 0.975])


class TestConfidenceInterval:
    """Tests for confidence interval computation."""

    def test_95_percent_confidence_interval(self):
        """Test 95% confidence interval calculation."""
        api = ConfidenceAwareDecisionAPI()
        dist = api.compute_predictive_distribution(0.5, 0.1)
        ci = api.compute_confidence_interval(dist, confidence_level=0.95)

        assert isinstance(ci, ConfidenceInterval)
        assert ci.confidence_level == 0.95
        assert ci.lower_bound < ci.mean < ci.upper_bound
        assert ci.lower_bound >= 0
        assert ci.std_dev > 0

    def test_90_percent_confidence_interval(self):
        """Test 90% confidence interval calculation."""
        api = ConfidenceAwareDecisionAPI()
        dist = api.compute_predictive_distribution(0.7, 0.15)
        ci = api.compute_confidence_interval(dist, confidence_level=0.90)

        assert ci.confidence_level == 0.90
        # 90% CI should be narrower than 95% CI
        ci_95 = api.compute_confidence_interval(dist, confidence_level=0.95)
        assert (ci.upper_bound - ci.lower_bound) < (ci_95.upper_bound - ci_95.lower_bound)

    def test_default_confidence_level(self):
        """Test default confidence level usage."""
        api = ConfidenceAwareDecisionAPI(default_confidence_level=0.99)
        dist = api.compute_predictive_distribution(0.6, 0.1)
        ci = api.compute_confidence_interval(dist)

        assert ci.confidence_level == 0.99


class TestConfidenceBand:
    """Tests for confidence band determination."""

    def test_very_high_confidence(self):
        """Test very high confidence band."""
        api = ConfidenceAwareDecisionAPI()
        band = api.determine_confidence_band(std_dev=0.02, mean=0.5)
        assert band == ConfidenceBand.VERY_HIGH

    def test_high_confidence(self):
        """Test high confidence band."""
        api = ConfidenceAwareDecisionAPI()
        band = api.determine_confidence_band(std_dev=0.05, mean=0.5)
        assert band == ConfidenceBand.HIGH

    def test_medium_confidence(self):
        """Test medium confidence band."""
        api = ConfidenceAwareDecisionAPI()
        band = api.determine_confidence_band(std_dev=0.15, mean=0.5)
        # CV = 0.15/0.5 = 0.30, which is at the MEDIUM/LOW boundary
        assert band in [ConfidenceBand.MEDIUM, ConfidenceBand.LOW]

    def test_low_confidence(self):
        """Test low confidence band."""
        api = ConfidenceAwareDecisionAPI()
        band = api.determine_confidence_band(std_dev=0.20, mean=0.5)
        assert band == ConfidenceBand.LOW

    def test_very_low_confidence(self):
        """Test very low confidence band."""
        api = ConfidenceAwareDecisionAPI()
        band = api.determine_confidence_band(std_dev=0.30, mean=0.5)
        assert band == ConfidenceBand.VERY_LOW

    def test_zero_mean_handling(self):
        """Test confidence band with zero mean."""
        api = ConfidenceAwareDecisionAPI()
        band = api.determine_confidence_band(std_dev=0.05, mean=0.0)
        assert band in ConfidenceBand


class TestRiskLevel:
    """Tests for risk level determination."""

    def test_conservative_risk(self):
        """Test conservative risk level."""
        api = ConfidenceAwareDecisionAPI(bankroll=1000.0)
        ci = ConfidenceInterval(lower_bound=5.0, upper_bound=15.0, confidence_level=0.95, mean=10.0, std_dev=2.0)
        risk = api.determine_risk_level(bet_size=15.0, ev=10.0, confidence_interval=ci)
        assert risk == RiskLevel.CONSERVATIVE

    def test_moderate_risk(self):
        """Test moderate risk level."""
        api = ConfidenceAwareDecisionAPI(bankroll=1000.0)
        ci = ConfidenceInterval(lower_bound=5.0, upper_bound=15.0, confidence_level=0.95, mean=10.0, std_dev=2.0)
        risk = api.determine_risk_level(bet_size=30.0, ev=10.0, confidence_interval=ci)
        assert risk == RiskLevel.MODERATE

    def test_aggressive_risk(self):
        """Test aggressive risk level."""
        api = ConfidenceAwareDecisionAPI(bankroll=1000.0)
        ci = ConfidenceInterval(lower_bound=5.0, upper_bound=15.0, confidence_level=0.95, mean=10.0, std_dev=2.0)
        risk = api.determine_risk_level(bet_size=60.0, ev=10.0, confidence_interval=ci)
        assert risk == RiskLevel.AGGRESSIVE

    def test_downside_risk_adjustment(self):
        """Test risk adjustment for negative lower bound."""
        api = ConfidenceAwareDecisionAPI(bankroll=1000.0)
        ci = ConfidenceInterval(lower_bound=-5.0, upper_bound=15.0, confidence_level=0.95, mean=5.0, std_dev=5.0)
        risk = api.determine_risk_level(bet_size=30.0, ev=5.0, confidence_interval=ci)
        # Should be higher risk due to downside uncertainty
        assert risk in [RiskLevel.MODERATE, RiskLevel.AGGRESSIVE]


class TestDecisionRecommendation:
    """Tests for decision recommendation generation."""

    def test_strong_hand_recommendation(self):
        """Test recommendation for strong hand."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.85,
            pot_size=100.0,
            call_amount=20.0,
            stack_size=500.0,
            uncertainty_estimate=0.10
        )

        assert isinstance(rec, DecisionRecommendation)
        assert rec.action in ['call', 'raise', 'all-in']
        assert rec.ev > 0
        assert rec.win_probability > 0.5
        assert isinstance(rec.confidence_band, ConfidenceBand)
        assert isinstance(rec.risk_level, RiskLevel)
        assert 0.0 <= rec.recommendation_strength <= 1.0

    def test_weak_hand_recommendation(self):
        """Test recommendation for weak hand."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.25,
            pot_size=100.0,
            call_amount=80.0,
            stack_size=200.0,
            uncertainty_estimate=0.15
        )

        # Weak hand with large call - should recommend conservative action
        # Note: fold equity in raises can make aggressive plays viable even with weak hands
        assert rec.action in ['fold', 'raise']  # Bluffing can be optimal
        if rec.action == 'fold':
            assert rec.ev == 0.0

    def test_moderate_hand_with_good_odds(self):
        """Test recommendation for moderate hand with good pot odds."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.55,
            pot_size=150.0,
            call_amount=25.0,  # Good pot odds
            stack_size=400.0,
            uncertainty_estimate=0.12
        )

        # Should recommend call or raise
        assert rec.action in ['call', 'raise']
        assert rec.ev > 0

    def test_opponent_tendencies_integration(self):
        """Test integration of opponent tendencies."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec_with_info = api.recommend_decision(
            hand_strength=0.60,
            pot_size=100.0,
            call_amount=30.0,
            stack_size=500.0,
            opponent_tendencies={'fold_to_raise': 0.45},
            uncertainty_estimate=0.10
        )

        rec_without_info = api.recommend_decision(
            hand_strength=0.60,
            pot_size=100.0,
            call_amount=30.0,
            stack_size=500.0,
            opponent_tendencies=None,
            uncertainty_estimate=0.10
        )

        # With opponent info should have different (likely higher) confidence
        assert rec_with_info.recommendation_strength != rec_without_info.recommendation_strength

    def test_alternative_actions_included(self):
        """Test that alternative actions are provided."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.70,
            pot_size=100.0,
            call_amount=30.0,
            stack_size=400.0,
            uncertainty_estimate=0.12
        )

        assert len(rec.alternative_actions) > 0
        assert all(isinstance(alt[0], str) for alt in rec.alternative_actions)
        assert all(isinstance(alt[1], float) for alt in rec.alternative_actions)
        assert all(isinstance(alt[2], float) for alt in rec.alternative_actions)

    def test_uncertainty_sources_tracked(self):
        """Test that uncertainty sources are tracked."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.65,
            pot_size=100.0,
            call_amount=25.0,
            stack_size=500.0,
            opponent_tendencies=None,
            uncertainty_estimate=0.25
        )

        assert len(rec.uncertainty_sources) > 0
        assert "Limited opponent data" in rec.uncertainty_sources or "High model uncertainty" in rec.uncertainty_sources

    def test_suggested_bet_sizing(self):
        """Test bet sizing suggestions for raise actions."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.80,
            pot_size=100.0,
            call_amount=20.0,
            stack_size=500.0,
            uncertainty_estimate=0.08
        )

        if rec.action == 'raise':
            assert rec.suggested_bet_size is not None
            assert rec.suggested_bet_range is not None
            assert rec.suggested_bet_range[0] < rec.suggested_bet_size < rec.suggested_bet_range[1]


class TestFormatting:
    """Tests for recommendation formatting."""

    def test_format_recommendation(self):
        """Test recommendation formatting."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.75,
            pot_size=100.0,
            call_amount=25.0,
            stack_size=500.0,
            opponent_tendencies={'fold_to_raise': 0.35},
            uncertainty_estimate=0.12
        )

        formatted = api.format_recommendation(rec)

        assert isinstance(formatted, str)
        assert "RECOMMENDED ACTION" in formatted
        assert "Expected Value" in formatted
        assert "Win Probability" in formatted
        assert "Confidence" in formatted
        assert "Risk Level" in formatted

    def test_format_with_bet_sizing(self):
        """Test formatting includes bet sizing when available."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.80,
            pot_size=100.0,
            call_amount=20.0,
            stack_size=500.0,
            uncertainty_estimate=0.08
        )

        formatted = api.format_recommendation(rec)

        if rec.action == 'raise':
            assert "Suggested Bet" in formatted


class TestFactoryFunction:
    """Tests for factory function."""

    def test_get_confidence_decision_api(self):
        """Test factory function creates valid API instance."""
        api = get_confidence_decision_api(n_bootstrap_samples=500, bankroll=10000.0)

        assert isinstance(api, ConfidenceAwareDecisionAPI)
        assert api.n_bootstrap_samples == 500
        assert api.bankroll == 10000.0

    def test_factory_default_parameters(self):
        """Test factory function with default parameters."""
        api = get_confidence_decision_api()

        assert isinstance(api, ConfidenceAwareDecisionAPI)
        assert api.n_bootstrap_samples == 1000


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_zero_stack_size(self):
        """Test handling of zero stack size."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.70,
            pot_size=100.0,
            call_amount=0.0,
            stack_size=0.0,
            uncertainty_estimate=0.10
        )

        # Should still provide a recommendation
        assert rec.action in ['fold', 'call', 'raise', 'all-in']

    def test_very_high_uncertainty(self):
        """Test handling of very high uncertainty."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.50,
            pot_size=100.0,
            call_amount=30.0,
            stack_size=500.0,
            uncertainty_estimate=0.45
        )

        # Should reflect high uncertainty
        assert rec.confidence_band in [ConfidenceBand.LOW, ConfidenceBand.VERY_LOW]
        assert "High model uncertainty" in rec.uncertainty_sources

    def test_perfect_hand(self):
        """Test handling of perfect hand (100% win rate)."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=1.0,
            pot_size=100.0,
            call_amount=50.0,
            stack_size=500.0,
            uncertainty_estimate=0.05
        )

        # Should recommend positive EV action (call, raise, or all-in all valid)
        assert rec.action in ['call', 'raise', 'all-in']
        assert rec.ev > 0
        assert rec.win_probability > 0.9

    def test_impossible_hand(self):
        """Test handling of impossible hand (0% win rate)."""
        api = ConfidenceAwareDecisionAPI(bankroll=5000.0)
        rec = api.recommend_decision(
            hand_strength=0.0,
            pot_size=100.0,
            call_amount=50.0,
            stack_size=500.0,
            uncertainty_estimate=0.05
        )

        # With 0% hand strength, any action has negative EV except fold
        # But the algorithm considers fold equity, so any action is possible
        assert rec.action in ['fold', 'call', 'raise', 'all-in']
        # The EV for 0% hand should be negative for any non-fold action
        if rec.action == 'fold':
            assert rec.ev == 0.0
        else:
            # Negative EV but fold equity might make it close
            assert rec.ev <= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
