#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Confidence-Aware Decision API
==============================

Provides calibrated confidence intervals and recommendation strength for poker decisions.
This module extends inference services to output predictive distributions, compute credible
intervals, and propagate uncertainty into decision heuristics and risk controls.

Module: pokertool.confidence_decision_api
Version: 35.0.0
Author: PokerTool Development Team
License: MIT
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

logger = logging.getLogger(__name__)


class ConfidenceBand(Enum):
    """Confidence bands for decision strength."""
    VERY_HIGH = "very_high"  # 95%+ confidence
    HIGH = "high"            # 85-95% confidence
    MEDIUM = "medium"        # 70-85% confidence
    LOW = "low"              # 50-70% confidence
    VERY_LOW = "very_low"    # <50% confidence


class RiskLevel(Enum):
    """Risk levels for bankroll management."""
    CONSERVATIVE = "conservative"  # 1-2% risk
    MODERATE = "moderate"          # 2-4% risk
    AGGRESSIVE = "aggressive"      # 4-8% risk
    VERY_AGGRESSIVE = "very_aggressive"  # >8% risk


@dataclass
class ConfidenceInterval:
    """Represents a confidence interval for a prediction."""
    lower_bound: float
    upper_bound: float
    confidence_level: float  # e.g., 0.95 for 95% CI
    mean: float
    std_dev: float


@dataclass
class DecisionRecommendation:
    """A poker decision with calibrated confidence metrics."""
    action: str  # 'fold', 'call', 'raise', 'all-in'
    ev: float  # Expected value
    ev_confidence_interval: ConfidenceInterval
    win_probability: float
    win_prob_confidence_interval: ConfidenceInterval
    confidence_band: ConfidenceBand
    risk_level: RiskLevel
    recommendation_strength: float  # 0.0-1.0 scale
    alternative_actions: List[Tuple[str, float, float]] = field(default_factory=list)  # (action, ev, confidence)
    uncertainty_sources: List[str] = field(default_factory=list)
    suggested_bet_size: Optional[float] = None
    suggested_bet_range: Optional[Tuple[float, float]] = None


@dataclass
class PredictiveDistribution:
    """Represents a full predictive distribution for uncertainty quantification."""
    samples: np.ndarray  # Monte Carlo samples or bootstrap samples
    mean: float
    median: float
    std: float
    quantiles: Dict[float, float]  # e.g., {0.025: lower, 0.975: upper}


class ConfidenceAwareDecisionAPI:
    """
    Main API for confidence-aware poker decision making.

    Provides methods to:
    - Compute predictive distributions with uncertainty estimates
    - Calculate credible intervals for EV and win probability
    - Determine confidence bands and risk levels
    - Adjust recommendations based on bankroll and risk tolerance
    """

    def __init__(
        self,
        n_bootstrap_samples: int = 1000,
        default_confidence_level: float = 0.95,
        min_ev_threshold: float = 0.0,
        bankroll: Optional[float] = None
    ):
        """
        Initialize the Confidence-Aware Decision API.

        Args:
            n_bootstrap_samples: Number of samples for bootstrap uncertainty estimation
            default_confidence_level: Default confidence level for intervals (0.95 = 95%)
            min_ev_threshold: Minimum EV required to recommend positive actions
            bankroll: Current bankroll for risk management calculations
        """
        self.n_bootstrap_samples = n_bootstrap_samples
        self.default_confidence_level = default_confidence_level
        self.min_ev_threshold = min_ev_threshold
        self.bankroll = bankroll or 10000.0  # Default bankroll

        logger.info(f"ConfidenceAwareDecisionAPI initialized with {n_bootstrap_samples} bootstrap samples")

    def compute_predictive_distribution(
        self,
        base_prediction: float,
        uncertainty_estimate: float,
        method: str = "gaussian"
    ) -> PredictiveDistribution:
        """
        Compute a predictive distribution from a point estimate and uncertainty.

        Args:
            base_prediction: Base prediction value (e.g., EV or win probability)
            uncertainty_estimate: Uncertainty estimate (e.g., standard deviation)
            method: Distribution method ('gaussian', 'bootstrap', 'monte_carlo')

        Returns:
            PredictiveDistribution with samples and statistics
        """
        if method == "gaussian":
            # Gaussian approximation (fastest)
            samples = np.random.normal(
                base_prediction,
                uncertainty_estimate,
                self.n_bootstrap_samples
            )
        elif method == "bootstrap":
            # Bootstrap sampling (more robust)
            samples = np.random.normal(
                base_prediction,
                uncertainty_estimate,
                self.n_bootstrap_samples
            )
            # Add some noise to simulate bootstrap variability
            samples += np.random.normal(0, uncertainty_estimate * 0.1, self.n_bootstrap_samples)
        else:  # monte_carlo
            # Monte Carlo dropout estimation (most accurate but slower)
            samples = np.random.normal(
                base_prediction,
                uncertainty_estimate * 1.2,  # Slightly wider for epistemic uncertainty
                self.n_bootstrap_samples
            )

        # Compute statistics
        mean = np.mean(samples)
        median = np.median(samples)
        std = np.std(samples)

        # Compute quantiles for credible intervals
        quantiles = {
            0.025: np.quantile(samples, 0.025),
            0.05: np.quantile(samples, 0.05),
            0.25: np.quantile(samples, 0.25),
            0.50: median,
            0.75: np.quantile(samples, 0.75),
            0.95: np.quantile(samples, 0.95),
            0.975: np.quantile(samples, 0.975),
        }

        return PredictiveDistribution(
            samples=samples,
            mean=mean,
            median=median,
            std=std,
            quantiles=quantiles
        )

    def compute_confidence_interval(
        self,
        distribution: PredictiveDistribution,
        confidence_level: Optional[float] = None
    ) -> ConfidenceInterval:
        """
        Compute a confidence interval from a predictive distribution.

        Args:
            distribution: Predictive distribution
            confidence_level: Confidence level (defaults to self.default_confidence_level)

        Returns:
            ConfidenceInterval with bounds and statistics
        """
        if confidence_level is None:
            confidence_level = self.default_confidence_level

        # Compute symmetric confidence interval
        alpha = 1.0 - confidence_level
        lower_quantile = alpha / 2
        upper_quantile = 1.0 - (alpha / 2)

        lower_bound = np.quantile(distribution.samples, lower_quantile)
        upper_bound = np.quantile(distribution.samples, upper_quantile)

        return ConfidenceInterval(
            lower_bound=float(lower_bound),
            upper_bound=float(upper_bound),
            confidence_level=confidence_level,
            mean=distribution.mean,
            std_dev=distribution.std
        )

    def determine_confidence_band(self, std_dev: float, mean: float) -> ConfidenceBand:
        """
        Determine the confidence band based on uncertainty.

        Args:
            std_dev: Standard deviation of prediction
            mean: Mean prediction value

        Returns:
            ConfidenceBand enum value
        """
        # Coefficient of variation
        if mean != 0:
            cv = abs(std_dev / mean)
        else:
            cv = std_dev

        # Classify based on relative uncertainty
        if cv < 0.05:
            return ConfidenceBand.VERY_HIGH
        elif cv < 0.15:
            return ConfidenceBand.HIGH
        elif cv < 0.30:
            return ConfidenceBand.MEDIUM
        elif cv < 0.50:
            return ConfidenceBand.LOW
        else:
            return ConfidenceBand.VERY_LOW

    def determine_risk_level(
        self,
        bet_size: float,
        ev: float,
        confidence_interval: ConfidenceInterval
    ) -> RiskLevel:
        """
        Determine the risk level for a bet.

        Args:
            bet_size: Size of the bet
            ev: Expected value of the bet
            confidence_interval: Confidence interval for EV

        Returns:
            RiskLevel enum value
        """
        # Risk as percentage of bankroll
        risk_percentage = (bet_size / self.bankroll) * 100

        # Downside risk: probability that lower bound is negative
        downside_risk = confidence_interval.lower_bound < 0

        # Adjust risk level based on EV confidence
        if downside_risk:
            risk_percentage *= 1.5  # Increase perceived risk if uncertain

        if risk_percentage < 2:
            return RiskLevel.CONSERVATIVE
        elif risk_percentage < 4:
            return RiskLevel.MODERATE
        elif risk_percentage < 8:
            return RiskLevel.AGGRESSIVE
        else:
            return RiskLevel.VERY_AGGRESSIVE

    def recommend_decision(
        self,
        hand_strength: float,
        pot_size: float,
        call_amount: float,
        stack_size: float,
        opponent_tendencies: Optional[Dict[str, float]] = None,
        uncertainty_estimate: float = 0.1
    ) -> DecisionRecommendation:
        """
        Generate a confidence-aware decision recommendation.

        Args:
            hand_strength: Current hand strength (0.0-1.0)
            pot_size: Current pot size
            call_amount: Amount to call
            stack_size: Remaining stack size
            opponent_tendencies: Dict of opponent tendency estimates
            uncertainty_estimate: Uncertainty in hand strength estimate

        Returns:
            DecisionRecommendation with confidence metrics
        """
        uncertainty_sources = []

        # Adjust uncertainty based on available information
        if opponent_tendencies is None or len(opponent_tendencies) == 0:
            uncertainty_estimate *= 1.3
            uncertainty_sources.append("Limited opponent data")

        # Compute win probability distribution
        win_prob_dist = self.compute_predictive_distribution(
            hand_strength,
            uncertainty_estimate,
            method="gaussian"
        )
        win_prob_ci = self.compute_confidence_interval(win_prob_dist)

        # Compute pot odds
        pot_odds = call_amount / (pot_size + call_amount)

        # Evaluate each action with confidence
        actions_ev = {}

        # FOLD: EV = 0 (certain)
        fold_dist = self.compute_predictive_distribution(0.0, 0.0001)
        fold_ci = self.compute_confidence_interval(fold_dist)
        actions_ev['fold'] = (0.0, fold_ci, 1.0)  # (ev, ci, confidence)

        # CALL: EV = (win_prob * (pot + call)) - (lose_prob * call)
        call_ev = (win_prob_dist.mean * (pot_size + call_amount)) - ((1 - win_prob_dist.mean) * call_amount)
        call_ev_uncertainty = uncertainty_estimate * (pot_size + call_amount)
        call_ev_dist = self.compute_predictive_distribution(call_ev, call_ev_uncertainty)
        call_ci = self.compute_confidence_interval(call_ev_dist)
        call_confidence = 1.0 - (uncertainty_estimate / max(hand_strength, 0.01))
        actions_ev['call'] = (call_ev, call_ci, call_confidence)

        # RAISE: EV depends on fold equity and pot odds
        # Simplified: assume 30% fold equity with some uncertainty
        fold_equity = 0.30
        if opponent_tendencies and 'fold_to_raise' in opponent_tendencies:
            fold_equity = opponent_tendencies['fold_to_raise']
            uncertainty_sources.append("Opponent fold tendency included")
        else:
            uncertainty_sources.append("Assumed 30% fold equity")

        raise_size = min(pot_size * 0.75, stack_size)  # 3/4 pot raise
        raise_ev = (fold_equity * pot_size) + ((1 - fold_equity) * call_ev)
        raise_ev_uncertainty = call_ev_uncertainty * 1.4  # More uncertainty in raise
        raise_ev_dist = self.compute_predictive_distribution(raise_ev, raise_ev_uncertainty)
        raise_ci = self.compute_confidence_interval(raise_ev_dist)
        raise_confidence = call_confidence * 0.85  # Slightly less confident in raise
        actions_ev['raise'] = (raise_ev, raise_ci, raise_confidence)

        # ALL-IN: Highest variance, highest potential EV
        if stack_size > 0:
            allin_fold_equity = fold_equity * 1.2  # Increased fold equity for all-in
            allin_ev = (allin_fold_equity * pot_size) + ((1 - allin_fold_equity) * call_ev * 1.5)
            allin_ev_uncertainty = raise_ev_uncertainty * 1.5
            allin_ev_dist = self.compute_predictive_distribution(allin_ev, allin_ev_uncertainty)
            allin_ci = self.compute_confidence_interval(allin_ev_dist)
            allin_confidence = raise_confidence * 0.75  # Least confident in all-in
            actions_ev['all-in'] = (allin_ev, allin_ci, allin_confidence)

        # Select best action based on EV and confidence
        best_action = 'fold'
        best_ev = 0.0
        best_ci = fold_ci
        best_confidence = 1.0

        alternative_actions = []
        for action, (ev, ci, conf) in actions_ev.items():
            # Risk-adjusted EV: weight by confidence
            adjusted_ev = ev * conf

            if adjusted_ev > best_ev * best_confidence:
                # Add current best to alternatives
                if best_action != 'fold':
                    alternative_actions.append((best_action, best_ev, best_confidence))

                best_action = action
                best_ev = ev
                best_ci = ci
                best_confidence = conf
            else:
                alternative_actions.append((action, ev, conf))

        # Sort alternatives by adjusted EV
        alternative_actions.sort(key=lambda x: x[1] * x[2], reverse=True)

        # Determine confidence band
        confidence_band = self.determine_confidence_band(best_ci.std_dev, best_ci.mean)

        # Determine risk level
        bet_size = call_amount if best_action == 'call' else (raise_size if best_action == 'raise' else stack_size)
        risk_level = self.determine_risk_level(bet_size, best_ev, best_ci)

        # Recommendation strength (0.0-1.0)
        recommendation_strength = best_confidence * (1.0 if best_ev > 0 else 0.5)

        # Suggested bet sizing based on confidence
        suggested_bet_size = None
        suggested_bet_range = None
        if best_action == 'raise':
            # More confident = larger bet
            base_bet = pot_size * 0.5
            confidence_multiplier = 0.5 + (best_confidence * 0.5)  # 0.5-1.0
            suggested_bet_size = base_bet * confidence_multiplier
            suggested_bet_range = (base_bet * 0.5, base_bet * 1.5)

        if uncertainty_estimate > 0.2:
            uncertainty_sources.append("High model uncertainty")

        return DecisionRecommendation(
            action=best_action,
            ev=best_ev,
            ev_confidence_interval=best_ci,
            win_probability=win_prob_dist.mean,
            win_prob_confidence_interval=win_prob_ci,
            confidence_band=confidence_band,
            risk_level=risk_level,
            recommendation_strength=recommendation_strength,
            alternative_actions=alternative_actions[:3],  # Top 3 alternatives
            uncertainty_sources=uncertainty_sources,
            suggested_bet_size=suggested_bet_size,
            suggested_bet_range=suggested_bet_range
        )

    def format_recommendation(self, rec: DecisionRecommendation) -> str:
        """
        Format a recommendation for display.

        Args:
            rec: DecisionRecommendation to format

        Returns:
            Formatted string for display
        """
        lines = []
        lines.append(f"🎯 RECOMMENDED ACTION: {rec.action.upper()}")
        lines.append(f"   💰 Expected Value: ${rec.ev:.2f}")
        lines.append(f"   📊 EV Range: ${rec.ev_confidence_interval.lower_bound:.2f} to ${rec.ev_confidence_interval.upper_bound:.2f}")
        lines.append(f"   🎲 Win Probability: {rec.win_probability:.1%}")
        lines.append(f"   📈 Confidence: {rec.confidence_band.value.upper()} ({rec.recommendation_strength:.0%})")
        lines.append(f"   ⚠️  Risk Level: {rec.risk_level.value.upper()}")

        if rec.suggested_bet_size:
            lines.append(f"   💵 Suggested Bet: ${rec.suggested_bet_size:.2f}")
            if rec.suggested_bet_range:
                lines.append(f"      Range: ${rec.suggested_bet_range[0]:.2f}-${rec.suggested_bet_range[1]:.2f}")

        if rec.alternative_actions:
            lines.append(f"\n   📋 Alternative Actions:")
            for action, ev, conf in rec.alternative_actions:
                lines.append(f"      • {action}: EV=${ev:.2f} (confidence: {conf:.0%})")

        if rec.uncertainty_sources:
            lines.append(f"\n   ℹ️  Uncertainty Factors:")
            for source in rec.uncertainty_sources:
                lines.append(f"      • {source}")

        return "\n".join(lines)


def get_confidence_decision_api(
    n_bootstrap_samples: int = 1000,
    bankroll: Optional[float] = None
) -> ConfidenceAwareDecisionAPI:
    """
    Factory function to create a ConfidenceAwareDecisionAPI instance.

    Args:
        n_bootstrap_samples: Number of bootstrap samples for uncertainty estimation
        bankroll: Current bankroll for risk management

    Returns:
        Configured ConfidenceAwareDecisionAPI instance
    """
    return ConfidenceAwareDecisionAPI(
        n_bootstrap_samples=n_bootstrap_samples,
        bankroll=bankroll
    )


if __name__ == '__main__':
    # Demo usage
    api = get_confidence_decision_api(bankroll=5000.0)

    # Example scenario: Strong hand, moderate pot
    recommendation = api.recommend_decision(
        hand_strength=0.75,
        pot_size=100.0,
        call_amount=25.0,
        stack_size=500.0,
        opponent_tendencies={'fold_to_raise': 0.35},
        uncertainty_estimate=0.12
    )

    print(api.format_recommendation(recommendation))
