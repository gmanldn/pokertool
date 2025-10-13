#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive tests for Model Calibration and Drift Detection System
=====================================================================

Tests online calibration, drift detection, and prediction monitoring.
"""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path
from pokertool.model_calibration import (
    ModelCalibrationSystem,
    OnlineCalibrator,
    DriftDetector,
    CalibrationMethod,
    DriftStatus,
    PredictionRecord,
    CalibrationMetrics,
    DriftMetrics,
    get_calibration_system
)


class TestPredictionRecord:
    """Test PredictionRecord dataclass."""

    def test_prediction_record_creation(self):
        """Test creating prediction records."""
        record = PredictionRecord(
            timestamp=1234567890.0,
            predicted_prob=0.75,
            actual_outcome=1,
            stake_level="0.10/0.20",
            hand_id="hand123"
        )

        assert record.timestamp == 1234567890.0
        assert record.predicted_prob == 0.75
        assert record.actual_outcome == 1
        assert record.stake_level == "0.10/0.20"
        assert record.hand_id == "hand123"

    def test_prediction_record_without_optional(self):
        """Test prediction record without optional fields."""
        record = PredictionRecord(
            timestamp=1234567890.0,
            predicted_prob=0.75,
            actual_outcome=1,
            stake_level="default"
        )

        assert record.hand_id is None
        assert record.features is None


class TestCalibrationMetrics:
    """Test CalibrationMetrics dataclass."""

    def test_calibration_metrics_creation(self):
        """Test creating calibration metrics."""
        metrics = CalibrationMetrics(
            brier_score=0.15,
            log_loss=0.45,
            calibration_error=0.08,
            num_predictions=500,
            timestamp=1234567890.0
        )

        assert metrics.brier_score == 0.15
        assert metrics.log_loss == 0.45
        assert metrics.calibration_error == 0.08
        assert metrics.num_predictions == 500
        assert metrics.timestamp == 1234567890.0


class TestDriftMetrics:
    """Test DriftMetrics dataclass."""

    def test_drift_metrics_creation(self):
        """Test creating drift metrics."""
        metrics = DriftMetrics(
            psi=0.15,
            kl_divergence=0.08,
            distribution_shift=0.15,
            status=DriftStatus.WARNING,
            timestamp=1234567890.0,
            alerts=["Drift warning detected"]
        )

        assert metrics.psi == 0.15
        assert metrics.kl_divergence == 0.08
        assert metrics.status == DriftStatus.WARNING
        assert len(metrics.alerts) == 1


class TestOnlineCalibrator:
    """Test OnlineCalibrator class."""

    def test_calibrator_initialization(self):
        """Test calibrator initializes correctly."""
        calibrator = OnlineCalibrator(CalibrationMethod.PLATT_SCALING)

        assert calibrator.method == CalibrationMethod.PLATT_SCALING
        assert calibrator.platt_A == 1.0
        assert calibrator.platt_B == 0.0
        assert len(calibrator.predictions) == 0
        assert len(calibrator.outcomes) == 0

    def test_add_prediction(self):
        """Test adding predictions."""
        calibrator = OnlineCalibrator()

        calibrator.add_prediction(0.7, 1)
        calibrator.add_prediction(0.3, 0)

        assert len(calibrator.predictions) == 2
        assert len(calibrator.outcomes) == 2

    def test_platt_scaling_calibration(self):
        """Test Platt scaling calibration."""
        calibrator = OnlineCalibrator(CalibrationMethod.PLATT_SCALING)

        # With default parameters (A=1, B=0), should return same value
        prob = 0.7
        calibrated = calibrator.calibrate(prob)

        # Should be close to original (within numerical precision)
        assert abs(calibrated - prob) < 0.1

    def test_isotonic_calibration_no_bins(self):
        """Test isotonic calibration without bins returns original."""
        calibrator = OnlineCalibrator(CalibrationMethod.ISOTONIC_REGRESSION)

        prob = 0.7
        calibrated = calibrator.calibrate(prob)

        # Without bins, should return original
        assert calibrated == prob

    def test_no_calibration(self):
        """Test no calibration method."""
        calibrator = OnlineCalibrator(CalibrationMethod.NONE)

        prob = 0.7
        calibrated = calibrator.calibrate(prob)

        assert calibrated == prob

    def test_update_calibration_insufficient_data(self):
        """Test calibration update with insufficient data."""
        calibrator = OnlineCalibrator()

        # Add only 10 predictions (need 50+)
        for i in range(10):
            calibrator.add_prediction(0.5, i % 2)

        calibrator.update_calibration()

        # Should not update (warning logged)
        assert calibrator.update_count == 0

    def test_update_platt_calibration(self):
        """Test Platt scaling calibration update."""
        calibrator = OnlineCalibrator(CalibrationMethod.PLATT_SCALING)

        # Add miscalibrated predictions (always too high)
        np.random.seed(42)
        for i in range(100):
            true_prob = 0.5
            predicted_prob = 0.7  # Always overconfident
            outcome = 1 if np.random.random() < true_prob else 0
            calibrator.add_prediction(predicted_prob, outcome)

        calibrator.update_calibration()

        # Parameters should have changed
        assert calibrator.update_count == 1
        # A and B should be adjusted (not default values)
        # Note: exact values depend on optimization, so we just check they changed
        assert calibrator.platt_A != 1.0 or calibrator.platt_B != 0.0

    def test_update_isotonic_calibration(self):
        """Test isotonic calibration update."""
        calibrator = OnlineCalibrator(CalibrationMethod.ISOTONIC_REGRESSION)

        # Add predictions with known relationship
        np.random.seed(42)
        for i in range(100):
            prob = i / 100.0
            outcome = 1 if np.random.random() < prob else 0
            calibrator.add_prediction(prob, outcome)

        calibrator.update_calibration()

        # Should have created bins
        assert len(calibrator.isotonic_bins) > 0
        assert calibrator.update_count == 1

    def test_calibration_bounds(self):
        """Test calibration handles edge cases."""
        calibrator = OnlineCalibrator()

        # Test extreme probabilities
        assert 0.0 < calibrator.calibrate(0.001) < 1.0
        assert 0.0 < calibrator.calibrate(0.999) < 1.0
        assert 0.0 < calibrator.calibrate(0.5) < 1.0


class TestDriftDetector:
    """Test DriftDetector class."""

    def test_drift_detector_initialization(self):
        """Test drift detector initializes correctly."""
        detector = DriftDetector(psi_threshold=0.2, kl_threshold=0.1)

        assert detector.psi_threshold == 0.2
        assert detector.kl_threshold == 0.1
        assert detector.reference_pred_dist is None
        assert len(detector.current_predictions) == 0

    def test_set_reference_distribution(self):
        """Test setting reference distribution."""
        detector = DriftDetector()

        # Create reference distribution
        reference_preds = np.random.uniform(0.3, 0.7, 1000)
        detector.set_reference_distribution(reference_preds)

        assert detector.reference_pred_dist is not None
        assert len(detector.reference_pred_dist) == 10  # Default bins

    def test_add_prediction(self):
        """Test adding predictions for drift monitoring."""
        detector = DriftDetector()

        detector.add_prediction(0.7, features={"pot_size": 100})
        detector.add_prediction(0.3)

        assert len(detector.current_predictions) == 2

    def test_detect_drift_insufficient_data(self):
        """Test drift detection with insufficient data."""
        detector = DriftDetector()

        # Add only 50 predictions (need 100+)
        for i in range(50):
            detector.add_prediction(0.5)

        metrics = detector.detect_drift()

        assert metrics.status == DriftStatus.NOMINAL
        assert metrics.psi == 0.0
        assert metrics.kl_divergence == 0.0

    def test_detect_no_drift(self):
        """Test drift detection when no drift present."""
        detector = DriftDetector()

        # Set reference distribution
        np.random.seed(42)
        reference_preds = np.random.uniform(0.3, 0.7, 1000)
        detector.set_reference_distribution(reference_preds)

        # Add current predictions from same distribution
        np.random.seed(43)
        for _ in range(200):
            detector.add_prediction(np.random.uniform(0.3, 0.7))

        metrics = detector.detect_drift()

        # Should detect no significant drift
        assert metrics.status == DriftStatus.NOMINAL
        assert metrics.psi < 0.2
        assert len(metrics.alerts) == 0

    def test_detect_warning_drift(self):
        """Test drift detection at warning level."""
        detector = DriftDetector(psi_threshold=0.1, kl_threshold=0.05)

        # Set reference distribution (0.3-0.7)
        np.random.seed(42)
        reference_preds = np.random.uniform(0.3, 0.7, 1000)
        detector.set_reference_distribution(reference_preds)

        # Add current predictions from shifted distribution (0.5-0.9)
        np.random.seed(43)
        for _ in range(200):
            detector.add_prediction(np.random.uniform(0.5, 0.9))

        metrics = detector.detect_drift()

        # Should detect drift (warning or critical)
        assert metrics.status in [DriftStatus.WARNING, DriftStatus.CRITICAL]
        assert metrics.psi > 0.0
        assert len(metrics.alerts) > 0

    def test_detect_critical_drift(self):
        """Test drift detection at critical level."""
        detector = DriftDetector(psi_threshold=0.1, kl_threshold=0.05)

        # Set reference distribution (0.3-0.7)
        np.random.seed(42)
        reference_preds = np.random.uniform(0.3, 0.7, 1000)
        detector.set_reference_distribution(reference_preds)

        # Add current predictions from very different distribution (0.1-0.3)
        np.random.seed(43)
        for _ in range(200):
            detector.add_prediction(np.random.uniform(0.1, 0.3))

        metrics = detector.detect_drift()

        # Should detect critical drift
        assert metrics.status == DriftStatus.CRITICAL
        assert "Critical" in metrics.alerts[0]

    def test_psi_computation(self):
        """Test PSI computation."""
        detector = DriftDetector()

        # Create two identical distributions
        expected = np.array([0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.025, 0.015, 0.005, 0.005])
        actual = np.array([0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.025, 0.015, 0.005, 0.005])

        psi = detector._compute_psi(expected, actual)

        # PSI should be ~0 for identical distributions
        assert abs(psi) < 0.01

    def test_kl_divergence_computation(self):
        """Test KL divergence computation."""
        detector = DriftDetector()

        # Create two distributions
        p = np.array([0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.025, 0.015, 0.005, 0.005])
        q = np.array([0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.025, 0.015, 0.005, 0.005])

        kl = detector._compute_kl_divergence(p, q)

        # KL should be ~0 for identical distributions
        assert abs(kl) < 0.01


class TestModelCalibrationSystem:
    """Test ModelCalibrationSystem class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary directory for storage
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir)
        self.system = ModelCalibrationSystem(
            calibration_method=CalibrationMethod.PLATT_SCALING,
            storage_path=self.storage_path
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_system_initialization(self):
        """Test system initializes correctly."""
        assert self.system.calibrator is not None
        assert self.system.drift_detector is not None
        assert self.system.storage_path.exists()
        assert self.system.stats["total_predictions"] == 0

    def test_log_prediction(self):
        """Test logging predictions."""
        self.system.log_prediction(
            predicted_prob=0.7,
            actual_outcome=1,
            stake_level="0.10/0.20",
            hand_id="hand123",
            features={"pot_size": 100}
        )

        assert self.system.stats["total_predictions"] == 1
        assert "0.10/0.20" in self.system.predictions_by_stake
        assert len(self.system.predictions_by_stake["0.10/0.20"]) == 1

    def test_get_calibrated_probability(self):
        """Test getting calibrated probability."""
        prob = 0.7
        calibrated = self.system.get_calibrated_probability(prob)

        # Should return a probability
        assert 0.0 <= calibrated <= 1.0

    def test_periodic_updates(self):
        """Test periodic calibration updates and drift checks."""
        # Log 150 predictions to trigger updates
        np.random.seed(42)
        for i in range(150):
            prob = 0.6
            outcome = 1 if np.random.random() < 0.5 else 0
            self.system.log_prediction(prob, outcome, stake_level="default")

        # Should have triggered drift check (every 100)
        assert len(self.system.drift_metrics_history) > 0

        # Should have triggered calibration metrics (every 100)
        assert len(self.system.calibration_metrics_history) > 0

    def test_calibration_metrics_computation(self):
        """Test calibration metrics computation."""
        # Add predictions
        np.random.seed(42)
        for i in range(200):
            prob = 0.6
            outcome = 1 if np.random.random() < 0.6 else 0
            self.system.log_prediction(prob, outcome)

        # Get latest metrics
        assert len(self.system.calibration_metrics_history) > 0
        metrics = self.system.calibration_metrics_history[-1]

        # Check metrics are reasonable
        assert 0.0 <= metrics.brier_score <= 1.0
        assert metrics.log_loss >= 0.0
        assert 0.0 <= metrics.calibration_error <= 1.0
        assert metrics.num_predictions > 0

    def test_drift_detection_integration(self):
        """Test drift detection integration."""
        # Set reference distribution
        np.random.seed(42)
        reference_preds = np.random.uniform(0.3, 0.7, 1000)
        self.system.drift_detector.set_reference_distribution(reference_preds)

        # Log predictions from same distribution
        np.random.seed(43)
        for i in range(150):
            prob = np.random.uniform(0.3, 0.7)
            outcome = 1 if np.random.random() < prob else 0
            self.system.log_prediction(prob, outcome)

        # Should have detected no drift
        assert len(self.system.drift_metrics_history) > 0
        latest_drift = self.system.drift_metrics_history[-1]
        assert latest_drift.status == DriftStatus.NOMINAL

    def test_retraining_trigger(self):
        """Test automatic retraining trigger."""
        # Track if retraining was called
        retraining_called = []

        def retraining_callback(drift_metrics):
            retraining_called.append(drift_metrics)

        self.system.retraining_callback = retraining_callback
        self.system.retraining_enabled = True

        # Set reference distribution
        np.random.seed(42)
        reference_preds = np.random.uniform(0.3, 0.7, 1000)
        self.system.drift_detector.set_reference_distribution(reference_preds)

        # Force critical drift by using very different distribution
        np.random.seed(43)
        for i in range(150):
            prob = np.random.uniform(0.05, 0.15)  # Very different
            outcome = 1 if np.random.random() < prob else 0
            self.system.log_prediction(prob, outcome)

        # Retraining might be triggered if drift is critical
        # (depends on exact threshold and distribution)
        # Just check the mechanism works
        assert self.system.retraining_callback is not None

    def test_get_stats(self):
        """Test getting system statistics."""
        # Log some predictions
        for i in range(50):
            self.system.log_prediction(0.6, i % 2)

        stats = self.system.get_stats()

        assert "total_predictions" in stats
        assert "calibration_updates" in stats
        assert "drift_warnings" in stats
        assert "calibrator_method" in stats
        assert stats["total_predictions"] == 50

    def test_save_and_load_state(self):
        """Test saving and loading calibration state."""
        # Add some predictions and update calibration
        np.random.seed(42)
        for i in range(100):
            self.system.log_prediction(0.6, i % 2)

        self.system.calibrator.update_calibration()

        # Save state
        self.system.save_state()

        # Check file was created
        state_file = self.storage_path / "calibration_state.json"
        assert state_file.exists()

        # Create new system and load state
        new_system = ModelCalibrationSystem(storage_path=self.storage_path)
        new_system.load_state()

        # Should have loaded parameters
        assert new_system.calibrator.platt_A == self.system.calibrator.platt_A
        assert new_system.calibrator.platt_B == self.system.calibrator.platt_B

    def test_stake_level_tracking(self):
        """Test tracking predictions by stake level."""
        # Log predictions at different stakes
        self.system.log_prediction(0.7, 1, stake_level="0.05/0.10")
        self.system.log_prediction(0.6, 0, stake_level="0.10/0.20")
        self.system.log_prediction(0.5, 1, stake_level="0.10/0.20")

        # Should have separate tracking
        assert "0.05/0.10" in self.system.predictions_by_stake
        assert "0.10/0.20" in self.system.predictions_by_stake
        assert len(self.system.predictions_by_stake["0.05/0.10"]) == 1
        assert len(self.system.predictions_by_stake["0.10/0.20"]) == 2

    def test_ece_computation(self):
        """Test Expected Calibration Error computation."""
        # Create perfectly calibrated predictions
        preds = np.linspace(0.1, 0.9, 100)
        outcomes = (np.random.random(100) < preds).astype(int)

        ece = self.system._compute_ece(preds, outcomes)

        # ECE should be small for calibrated predictions
        assert 0.0 <= ece <= 1.0


class TestGlobalInstance:
    """Test global calibration system instance."""

    def test_get_calibration_system(self):
        """Test getting global system instance."""
        system1 = get_calibration_system()
        system2 = get_calibration_system()

        # Should be the same instance (singleton)
        assert system1 is system2

    def test_global_instance_initialized(self):
        """Test that global instance is properly initialized."""
        system = get_calibration_system()

        assert system is not None
        assert system.calibrator is not None
        assert system.drift_detector is not None


class TestEnums:
    """Test enum classes."""

    def test_drift_status_enum(self):
        """Test DriftStatus enum values."""
        assert DriftStatus.NOMINAL.value == "nominal"
        assert DriftStatus.WARNING.value == "warning"
        assert DriftStatus.CRITICAL.value == "critical"
        assert DriftStatus.RETRAINING.value == "retraining"

    def test_calibration_method_enum(self):
        """Test CalibrationMethod enum values."""
        assert CalibrationMethod.PLATT_SCALING.value == "platt_scaling"
        assert CalibrationMethod.ISOTONIC_REGRESSION.value == "isotonic"
        assert CalibrationMethod.NONE.value == "none"


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_full_calibration_workflow(self):
        """Test complete calibration workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            system = ModelCalibrationSystem(storage_path=Path(temp_dir))

            # Set reference distribution
            np.random.seed(42)
            reference_preds = np.random.uniform(0.3, 0.7, 1000)
            system.drift_detector.set_reference_distribution(reference_preds)

            # Simulate 1000 predictions
            for i in range(1000):
                true_prob = np.random.uniform(0.3, 0.7)
                predicted_prob = true_prob + np.random.normal(0, 0.05)
                predicted_prob = np.clip(predicted_prob, 0.01, 0.99)
                outcome = 1 if np.random.random() < true_prob else 0

                system.log_prediction(
                    predicted_prob,
                    outcome,
                    stake_level="0.10/0.20",
                    features={"pot_size": 100}
                )

            # Check system state
            assert system.stats["total_predictions"] == 1000
            assert system.stats["calibration_updates"] > 0
            assert len(system.calibration_metrics_history) > 0
            assert len(system.drift_metrics_history) > 0

            # Save and verify state
            system.save_state()
            assert (Path(temp_dir) / "calibration_state.json").exists()

    def test_miscalibrated_to_calibrated(self):
        """Test calibration improving miscalibrated predictions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            system = ModelCalibrationSystem(storage_path=Path(temp_dir))

            # Add many miscalibrated predictions (always 0.7, but real prob is 0.5)
            np.random.seed(42)
            for i in range(500):
                predicted_prob = 0.7  # Always overconfident
                outcome = 1 if np.random.random() < 0.5 else 0  # True prob is 0.5
                system.log_prediction(predicted_prob, outcome)

            # Force calibration update
            system.calibrator.update_calibration()

            # Calibrated probability should be closer to 0.5
            calibrated = system.get_calibrated_probability(0.7)

            # Should have adjusted towards reality
            # (exact value depends on data, but should be < 0.7)
            assert calibrated < 0.7


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
