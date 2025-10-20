#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Real-Time Model Calibration and Drift Correction for PokerTool
================================================================

Monitors prediction quality, detects model drift, and automatically
applies calibration updates to maintain accurate win probability
and EV predictions as opponent pools evolve.

Features:
- Online prediction monitoring and outcome tracking
- Population Stability Index (PSI) drift detection
- KL divergence for distribution shift detection
- Online Platt scaling and isotonic regression calibration
- Automatic retraining triggers
- Stake-level tracking and alerting

Version: 1.0.0
"""

from __future__ import annotations

import logging
import json
import time
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class DriftStatus(Enum):
    """Model drift status levels."""
    NOMINAL = "nominal"          # No drift detected
    WARNING = "warning"          # Minor drift, monitoring
    CRITICAL = "critical"        # Significant drift, needs action
    RETRAINING = "retraining"    # Retraining in progress


class CalibrationMethod(Enum):
    """Available calibration methods."""
    PLATT_SCALING = "platt_scaling"
    ISOTONIC_REGRESSION = "isotonic"
    NONE = "none"


@dataclass
class PredictionRecord:
    """Record of a single prediction and its outcome."""
    timestamp: float
    predicted_prob: float
    actual_outcome: int  # 0 or 1
    stake_level: str
    hand_id: Optional[str] = None
    features: Optional[Dict[str, Any]] = None


@dataclass
class CalibrationMetrics:
    """Metrics for calibration quality assessment."""
    brier_score: float
    log_loss: float
    calibration_error: float  # Expected Calibration Error (ECE)
    num_predictions: int
    timestamp: float


@dataclass
class DriftMetrics:
    """Metrics for drift detection."""
    psi: float  # Population Stability Index
    kl_divergence: float  # KL divergence
    distribution_shift: float  # Max distribution shift
    status: DriftStatus
    timestamp: float
    alerts: List[str] = field(default_factory=list)


class OnlineCalibrator:
    """
    Online calibration module using Platt scaling or isotonic regression.

    Maintains calibration parameters that can be updated incrementally
    as new prediction-outcome pairs arrive.
    """

    def __init__(self, method: CalibrationMethod = CalibrationMethod.PLATT_SCALING):
        """
        Initialize the online calibrator.

        Args:
            method: Calibration method to use
        """
        self.method = method
        self.predictions = deque(maxlen=10000)  # Keep last 10k predictions
        self.outcomes = deque(maxlen=10000)

        # Platt scaling parameters: P(y=1) = 1 / (1 + exp(A*f + B))
        self.platt_A = 1.0
        self.platt_B = 0.0

        # Isotonic regression bins
        self.isotonic_bins = []

        self.last_update = time.time()
        self.update_count = 0

        logger.info(f"OnlineCalibrator initialized with method: {method.value}")

    def add_prediction(self, predicted_prob: float, actual_outcome: int):
        """
        Add a prediction-outcome pair for calibration.

        Args:
            predicted_prob: Predicted probability (0-1)
            actual_outcome: Actual outcome (0 or 1)
        """
        self.predictions.append(predicted_prob)
        self.outcomes.append(actual_outcome)

    def calibrate(self, prob: float) -> float:
        """
        Apply calibration to a predicted probability.

        Args:
            prob: Uncalibrated probability

        Returns:
            Calibrated probability
        """
        if self.method == CalibrationMethod.NONE:
            return prob
        elif self.method == CalibrationMethod.PLATT_SCALING:
            return self._platt_calibrate(prob)
        elif self.method == CalibrationMethod.ISOTONIC_REGRESSION:
            return self._isotonic_calibrate(prob)
        return prob

    def _platt_calibrate(self, prob: float) -> float:
        """Apply Platt scaling calibration."""
        # Convert probability to logit
        eps = 1e-7
        prob = np.clip(prob, eps, 1 - eps)
        logit = np.log(prob / (1 - prob))

        # Apply Platt parameters
        calibrated_logit = self.platt_A * logit + self.platt_B

        # Convert back to probability
        calibrated_prob = 1.0 / (1.0 + np.exp(-calibrated_logit))
        return float(calibrated_prob)

    def _isotonic_calibrate(self, prob: float) -> float:
        """Apply isotonic regression calibration."""
        if not self.isotonic_bins:
            return prob

        # Find appropriate bin
        for bin_min, bin_max, calibrated_value in self.isotonic_bins:
            if bin_min <= prob <= bin_max:
                return calibrated_value

        # If outside bins, return original
        return prob

    def update_calibration(self, warm_start: bool = True):
        """
        Update calibration parameters based on accumulated predictions.

        Args:
            warm_start: Whether to warm start from previous parameters
        """
        if len(self.predictions) < 50:
            logger.warning("Not enough predictions for calibration update")
            return

        preds = np.array(self.predictions)
        outcomes = np.array(self.outcomes)

        if self.method == CalibrationMethod.PLATT_SCALING:
            self._update_platt_scaling(preds, outcomes, warm_start)
        elif self.method == CalibrationMethod.ISOTONIC_REGRESSION:
            self._update_isotonic(preds, outcomes)

        self.last_update = time.time()
        self.update_count += 1
        logger.info(f"Calibration updated (count: {self.update_count})")

    def _update_platt_scaling(self, preds: np.ndarray, outcomes: np.ndarray, warm_start: bool):
        """Update Platt scaling parameters using logistic regression."""
        from scipy.optimize import minimize

        # Convert predictions to logits
        eps = 1e-7
        preds = np.clip(preds, eps, 1 - eps)
        logits = np.log(preds / (1 - preds))

        # Define loss function
        def platt_loss(params):
            A, B = params
            calibrated_logits = A * logits + B
            probs = 1.0 / (1.0 + np.exp(-calibrated_logits))
            probs = np.clip(probs, eps, 1 - eps)
            # Binary cross-entropy loss
            loss = -np.mean(outcomes * np.log(probs) + (1 - outcomes) * np.log(1 - probs))
            return loss

        # Optimize
        initial_params = [self.platt_A, self.platt_B] if warm_start else [1.0, 0.0]
        result = minimize(platt_loss, initial_params, method='BFGS')

        if result.success:
            self.platt_A, self.platt_B = result.x
            logger.info(f"Platt parameters updated: A={self.platt_A:.4f}, B={self.platt_B:.4f}")
        else:
            logger.warning("Platt scaling optimization failed")

    def _update_isotonic(self, preds: np.ndarray, outcomes: np.ndarray):
        """Update isotonic regression bins."""
        from sklearn.isotonic import IsotonicRegression

        # Fit isotonic regression
        iso_reg = IsotonicRegression(out_of_bounds='clip')
        calibrated = iso_reg.fit_transform(preds, outcomes)

        # Create bins
        self.isotonic_bins = []
        sorted_indices = np.argsort(preds)
        sorted_preds = preds[sorted_indices]
        sorted_calibrated = calibrated[sorted_indices]

        # Group into 20 bins
        bin_size = len(preds) // 20
        for i in range(0, len(preds), bin_size):
            bin_preds = sorted_preds[i:i+bin_size]
            bin_calibrated = sorted_calibrated[i:i+bin_size]
            if len(bin_preds) > 0:
                self.isotonic_bins.append((
                    float(bin_preds.min()),
                    float(bin_preds.max()),
                    float(bin_calibrated.mean())
                ))

        logger.info(f"Isotonic regression updated with {len(self.isotonic_bins)} bins")


class DriftDetector:
    """
    Drift detection using PSI and KL divergence.

    Monitors distribution shifts in predictions and features to detect
    when the model's assumptions are no longer valid.
    """

    def __init__(self, psi_threshold: float = 0.2, kl_threshold: float = 0.1):
        """
        Initialize drift detector.

        Args:
            psi_threshold: PSI threshold for drift warning
            kl_threshold: KL divergence threshold for drift warning
        """
        self.psi_threshold = psi_threshold
        self.kl_threshold = kl_threshold

        # Reference distributions (from training data)
        self.reference_pred_dist = None
        self.reference_feature_dists = {}

        # Current distributions (rolling window)
        self.current_predictions = deque(maxlen=1000)
        self.current_features = deque(maxlen=1000)

        logger.info(f"DriftDetector initialized (PSI threshold: {psi_threshold}, KL threshold: {kl_threshold})")

    def set_reference_distribution(self, predictions: np.ndarray, features: Optional[Dict[str, np.ndarray]] = None):
        """
        Set reference distributions from training data.

        Args:
            predictions: Array of predictions from training set
            features: Dictionary of feature arrays
        """
        self.reference_pred_dist = self._compute_histogram(predictions)

        if features:
            for feature_name, feature_values in features.items():
                self.reference_feature_dists[feature_name] = self._compute_histogram(feature_values)

        logger.info("Reference distributions set")

    def add_prediction(self, prediction: float, features: Optional[Dict[str, float]] = None):
        """Add a prediction for drift monitoring."""
        self.current_predictions.append(prediction)
        if features:
            self.current_features.append(features)

    def detect_drift(self) -> DriftMetrics:
        """
        Detect drift in predictions and features.

        Returns:
            DriftMetrics with drift status and scores
        """
        if len(self.current_predictions) < 100:
            return DriftMetrics(
                psi=0.0,
                kl_divergence=0.0,
                distribution_shift=0.0,
                status=DriftStatus.NOMINAL,
                timestamp=time.time()
            )

        # Check if reference distribution is set
        if self.reference_pred_dist is None:
            # No reference distribution set, use current as reference
            self.reference_pred_dist = self._compute_histogram(np.array(self.current_predictions))
            return DriftMetrics(
                psi=0.0,
                kl_divergence=0.0,
                distribution_shift=0.0,
                status=DriftStatus.NOMINAL,
                timestamp=time.time()
            )

        # Compute PSI for predictions
        current_dist = self._compute_histogram(np.array(self.current_predictions))
        psi = self._compute_psi(self.reference_pred_dist, current_dist)

        # Compute KL divergence
        kl_div = self._compute_kl_divergence(self.reference_pred_dist, current_dist)

        # Determine status
        alerts = []
        if psi > self.psi_threshold * 2 or kl_div > self.kl_threshold * 2:
            status = DriftStatus.CRITICAL
            alerts.append(f"Critical drift detected: PSI={psi:.4f}, KL={kl_div:.4f}")
        elif psi > self.psi_threshold or kl_div > self.kl_threshold:
            status = DriftStatus.WARNING
            alerts.append(f"Drift warning: PSI={psi:.4f}, KL={kl_div:.4f}")
        else:
            status = DriftStatus.NOMINAL

        return DriftMetrics(
            psi=psi,
            kl_divergence=kl_div,
            distribution_shift=max(psi, kl_div),
            status=status,
            timestamp=time.time(),
            alerts=alerts
        )

    def _compute_histogram(self, data: np.ndarray, bins: int = 10) -> np.ndarray:
        """Compute histogram for PSI/KL calculation."""
        hist, _ = np.histogram(data, bins=bins, range=(0, 1))
        hist = hist + 1  # Add 1 to avoid division by zero
        hist = hist / hist.sum()  # Normalize
        return hist

    def _compute_psi(self, expected: np.ndarray, actual: np.ndarray) -> float:
        """
        Compute Population Stability Index (PSI).

        PSI = Σ (actual% - expected%) * ln(actual% / expected%)
        """
        psi = np.sum((actual - expected) * np.log(actual / expected))
        return float(psi)

    def _compute_kl_divergence(self, p: np.ndarray, q: np.ndarray) -> float:
        """
        Compute KL divergence KL(P||Q).

        KL(P||Q) = Σ P(i) * log(P(i) / Q(i))
        """
        kl = np.sum(p * np.log(p / q))
        return float(kl)


class ModelCalibrationSystem:
    """
    Complete model calibration and drift correction system.

    Integrates prediction monitoring, drift detection, online calibration,
    and automatic retraining triggers.
    """

    def __init__(
        self,
        calibration_method: CalibrationMethod = CalibrationMethod.PLATT_SCALING,
        storage_path: Optional[Path] = None
    ):
        """
        Initialize the calibration system.

        Args:
            calibration_method: Method for online calibration
            storage_path: Path to store prediction logs and calibration state
        """
        self.calibrator = OnlineCalibrator(calibration_method)
        self.drift_detector = DriftDetector()

        self.storage_path = storage_path or Path("model_calibration_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Prediction storage
        self.predictions_by_stake = {}  # stake_level -> List[PredictionRecord]

        # Metrics history
        self.calibration_metrics_history = deque(maxlen=1000)
        self.drift_metrics_history = deque(maxlen=1000)

        # Retraining flags
        self.retraining_enabled = True
        self.retraining_callback: Optional[Callable] = None

        # Statistics
        self.stats = {
            "total_predictions": 0,
            "calibration_updates": 0,
            "drift_warnings": 0,
            "drift_critical": 0,
            "retraining_triggered": 0
        }

        logger.info("ModelCalibrationSystem initialized")

    def log_prediction(
        self,
        predicted_prob: float,
        actual_outcome: int,
        stake_level: str = "default",
        hand_id: Optional[str] = None,
        features: Optional[Dict[str, Any]] = None
    ):
        """
        Log a prediction and its outcome for calibration and drift monitoring.

        Args:
            predicted_prob: Predicted probability (0-1)
            actual_outcome: Actual outcome (0 or 1)
            stake_level: Stake level identifier
            hand_id: Optional hand identifier
            features: Optional feature dictionary for drift detection
        """
        record = PredictionRecord(
            timestamp=time.time(),
            predicted_prob=predicted_prob,
            actual_outcome=actual_outcome,
            stake_level=stake_level,
            hand_id=hand_id,
            features=features
        )

        # Store prediction
        if stake_level not in self.predictions_by_stake:
            self.predictions_by_stake[stake_level] = deque(maxlen=10000)
        self.predictions_by_stake[stake_level].append(record)

        # Add to calibrator and drift detector
        self.calibrator.add_prediction(predicted_prob, actual_outcome)
        self.drift_detector.add_prediction(predicted_prob, features)

        self.stats["total_predictions"] += 1

        # Periodically update calibration and check drift
        if self.stats["total_predictions"] % 100 == 0:
            self._check_and_update()

    def get_calibrated_probability(self, prob: float) -> float:
        """
        Get calibrated probability.

        Args:
            prob: Uncalibrated probability

        Returns:
            Calibrated probability
        """
        return self.calibrator.calibrate(prob)

    def _check_and_update(self):
        """Periodic check for drift and calibration updates."""
        # Check drift
        drift_metrics = self.drift_detector.detect_drift()
        self.drift_metrics_history.append(drift_metrics)

        if drift_metrics.status == DriftStatus.WARNING:
            self.stats["drift_warnings"] += 1
            logger.warning(f"Drift warning: {drift_metrics.alerts}")
        elif drift_metrics.status == DriftStatus.CRITICAL:
            self.stats["drift_critical"] += 1
            logger.error(f"Critical drift: {drift_metrics.alerts}")

            # Trigger retraining if enabled
            if self.retraining_enabled and self.retraining_callback:
                logger.info("Triggering automatic retraining")
                self.retraining_callback(drift_metrics)
                self.stats["retraining_triggered"] += 1

        # Update calibration every 500 predictions
        if self.stats["total_predictions"] % 500 == 0:
            self.calibrator.update_calibration(warm_start=True)
            self.stats["calibration_updates"] += 1

        # Compute and store calibration metrics
        if self.stats["total_predictions"] % 100 == 0:
            metrics = self._compute_calibration_metrics()
            self.calibration_metrics_history.append(metrics)

    def _compute_calibration_metrics(self) -> CalibrationMetrics:
        """Compute current calibration quality metrics."""
        preds = list(self.calibrator.predictions)
        outcomes = list(self.calibrator.outcomes)

        if len(preds) < 10:
            return CalibrationMetrics(
                brier_score=0.0,
                log_loss=0.0,
                calibration_error=0.0,
                num_predictions=0,
                timestamp=time.time()
            )

        preds = np.array(preds)
        outcomes = np.array(outcomes)

        # Brier score
        brier = np.mean((preds - outcomes) ** 2)

        # Log loss
        eps = 1e-7
        preds_clipped = np.clip(preds, eps, 1 - eps)
        log_loss = -np.mean(outcomes * np.log(preds_clipped) + (1 - outcomes) * np.log(1 - preds_clipped))

        # Expected Calibration Error (ECE)
        ece = self._compute_ece(preds, outcomes)

        return CalibrationMetrics(
            brier_score=float(brier),
            log_loss=float(log_loss),
            calibration_error=float(ece),
            num_predictions=len(preds),
            timestamp=time.time()
        )

    def _compute_ece(self, preds: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
        """Compute Expected Calibration Error."""
        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0

        for i in range(n_bins):
            mask = (preds >= bins[i]) & (preds < bins[i + 1])
            if mask.sum() > 0:
                bin_preds = preds[mask]
                bin_outcomes = outcomes[mask]
                avg_pred = bin_preds.mean()
                avg_outcome = bin_outcomes.mean()
                ece += mask.sum() / len(preds) * abs(avg_pred - avg_outcome)

        return ece

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            **self.stats,
            "calibrator_method": self.calibrator.method.value,
            "calibrator_updates": self.calibrator.update_count,
            "drift_status": self.drift_metrics_history[-1].status.value if self.drift_metrics_history else "unknown",
            "latest_calibration_metrics": asdict(self.calibration_metrics_history[-1]) if self.calibration_metrics_history else None
        }

    def save_state(self):
        """Save calibration state to disk."""
        state = {
            "calibrator_method": self.calibrator.method.value,
            "platt_A": self.calibrator.platt_A,
            "platt_B": self.calibrator.platt_B,
            "isotonic_bins": self.calibrator.isotonic_bins,
            "stats": self.stats,
            "timestamp": time.time()
        }

        state_path = self.storage_path / "calibration_state.json"
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"Calibration state saved to {state_path}")

    def load_state(self):
        """Load calibration state from disk."""
        state_path = self.storage_path / "calibration_state.json"
        if not state_path.exists():
            logger.warning("No saved state found")
            return

        with open(state_path, 'r') as f:
            state = json.load(f)

        self.calibrator.platt_A = state.get("platt_A", 1.0)
        self.calibrator.platt_B = state.get("platt_B", 0.0)
        self.calibrator.isotonic_bins = state.get("isotonic_bins", [])
        self.stats = state.get("stats", self.stats)

        logger.info(f"Calibration state loaded from {state_path}")


# Global calibration system instance
_calibration_system: Optional[ModelCalibrationSystem] = None


def get_calibration_system() -> ModelCalibrationSystem:
    """Get the global calibration system instance."""
    global _calibration_system
    if _calibration_system is None:
        _calibration_system = ModelCalibrationSystem()
    return _calibration_system


if __name__ == '__main__':
    # Test the calibration system
    print("Testing Model Calibration System...")

    system = ModelCalibrationSystem()

    # Simulate some predictions
    np.random.seed(42)
    for i in range(1000):
        # Simulate slightly miscalibrated predictions
        true_prob = np.random.uniform(0.3, 0.7)
        predicted_prob = true_prob + np.random.normal(0, 0.1)
        predicted_prob = np.clip(predicted_prob, 0.01, 0.99)
        outcome = 1 if np.random.random() < true_prob else 0

        system.log_prediction(predicted_prob, outcome, stake_level="0.10/0.20")

    # Get statistics
    stats = system.get_stats()
    print(f"\nCalibration System Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test calibration
    test_prob = 0.6
    calibrated = system.get_calibrated_probability(test_prob)
    print(f"\nCalibration test:")
    print(f"  Original: {test_prob}")
    print(f"  Calibrated: {calibrated:.4f}")

    print("\n✓ Model Calibration System test complete")
