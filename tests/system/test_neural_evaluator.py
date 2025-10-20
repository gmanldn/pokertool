"""System tests for the neural hand strength evaluator."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.neural_evaluator import HandState, NeuralHandStrengthEvaluator, TrainingSample

MODEL_SOURCE = Path(__file__).resolve().parents[2] / "src" / "pokertool" / "models" / "hand_strength_model.h5"


def _build_evaluator(tmp_path: Path) -> NeuralHandStrengthEvaluator:
    model_copy = tmp_path / "hand_strength_model.h5"
    shutil.copyfile(MODEL_SOURCE, model_copy)
    return NeuralHandStrengthEvaluator(model_path=model_copy)


def test_evaluator_returns_probabilities_and_confidence(tmp_path: Path) -> None:
    evaluator = _build_evaluator(tmp_path)
    state = HandState(
        hole_cards=("As", "Kd"),
        board_cards=("2h", "7d", "9c"),
        pot_odds=0.32,
        aggression_factor=0.75,
        position="late",
        effective_stack_bb=65,
        previous_actions=("raise", "bet"),
    )

    result = evaluator.evaluate_hand(state)
    assert 0.0 <= result.win_probability <= 1.0
    assert 0.2 <= result.confidence <= 0.97
    assert result.board_category in {"dry", "paired", "draw-heavy", "dynamic"}
    assert abs(result.score_breakdown["hole"]) > 0
    assert "hole_strength" in result.raw_features


def test_training_improves_relative_strength(tmp_path: Path) -> None:
    evaluator = _build_evaluator(tmp_path)

    strong = HandState(
        hole_cards=("Ah", "Ad"),
        board_cards=("Kd", "Qc", "2c"),
        pot_odds=0.28,
        aggression_factor=0.8,
        position="late",
        effective_stack_bb=90,
    )
    weak = HandState(
        hole_cards=("7c", "2d"),
        board_cards=("Kd", "Qc", "2c"),
        pot_odds=0.28,
        aggression_factor=0.4,
        position="early",
        effective_stack_bb=90,
    )

    baseline_gap = evaluator.evaluate_hand(strong).win_probability - evaluator.evaluate_hand(weak).win_probability

    samples = [
        TrainingSample(state=strong, outcome=1.0, weight=2.0),
        TrainingSample(state=weak, outcome=0.0, weight=1.5),
    ]
    evaluator.train(samples, epochs=6, learning_rate=0.12)

    updated_gap = evaluator.evaluate_hand(strong).win_probability - evaluator.evaluate_hand(weak).win_probability
    assert updated_gap > baseline_gap + 0.02
    assert evaluator.model["training_iterations"] >= 12


def test_board_texture_analysis_detects_draws(tmp_path: Path) -> None:
    evaluator = _build_evaluator(tmp_path)
    board = ("Ah", "Kh", "Qh")
    analysis = evaluator.board_texture_analysis(board)

    assert analysis["flush_draw"] is True
    assert analysis["straight_draw"] is True
    assert analysis["category"] == "dynamic"
    assert pytest.approx(analysis["high_card_pressure"], rel=1e-3) == 1.0


def test_cnn_model_encoding() -> None:
    """Test that CNN model properly encodes hand states."""
    from pokertool.neural_evaluator import CNNHandStrengthModel
    
    model = CNNHandStrengthModel()
    state = HandState(
        hole_cards=("As", "Kd"),
        board_cards=("Qh", "Jc", "Ts"),
        pot_odds=0.3,
        aggression_factor=1.0,
    )
    
    encoded = model.encode_hand_state(state)
    
    # Check tensor shape
    assert len(encoded) == 4  # 4 suits
    assert all(len(suit) == 13 for suit in encoded)  # 13 ranks
    assert all(len(row) == 13 for suit in encoded for row in suit)  # 13 ranks
    
    # Check that some values are non-zero
    flat = [val for suit in encoded for row in suit for val in row]
    assert any(val > 0 for val in flat)


def test_cnn_model_prediction_fallback() -> None:
    """Test that CNN model falls back gracefully when no framework available."""
    from pokertool.neural_evaluator import CNNHandStrengthModel
    
    model = CNNHandStrengthModel()
    state = HandState(
        hole_cards=("As", "Ad"),
        board_cards=("Kh", "Qc", "Jd"),
        pot_odds=0.25,
        aggression_factor=0.5,
    )
    
    prediction = model.predict(state)
    
    # Should return a valid probability
    assert 0.0 <= prediction <= 1.0
    
    # For AA, should be relatively high
    assert prediction > 0.5


def test_cnn_model_training_stub() -> None:
    """Test that CNN model training works even without ML framework."""
    from pokertool.neural_evaluator import CNNHandStrengthModel
    
    model = CNNHandStrengthModel()
    
    states = [
        HandState(
            hole_cards=("As", "Ad"),
            board_cards=("Kh", "Qc", "2d"),
            pot_odds=0.3,
            aggression_factor=1.0,
        ),
        HandState(
            hole_cards=("7c", "2d"),
            board_cards=("Kh", "Qc", "2d"),
            pot_odds=0.3,
            aggression_factor=0.3,
        ),
    ]
    outcomes = [1.0, 0.0]
    
    # Should not raise an error
    metrics = model.train_on_batch(states, outcomes)
    
    assert 'loss' in metrics
    assert 'accuracy' in metrics


def test_realtime_inference_engine() -> None:
    """Test the real-time inference engine wrapper."""
    from pokertool.neural_evaluator import RealTimeInferenceEngine
    
    engine = RealTimeInferenceEngine(use_cnn=False)
    
    state = HandState(
        hole_cards=("As", "Kd"),
        board_cards=("Qh", "Jc", "Ts"),
        pot_odds=0.3,
        aggression_factor=1.0,
    )
    
    result = engine.evaluate(state)
    
    assert 0.0 <= result.win_probability <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.board_category in {"dry", "paired", "draw-heavy", "dynamic"}
    
    # Check model info
    info = engine.get_model_info()
    assert 'type' in info
    assert info['type'] in {'lightweight', 'cnn'}


def test_cnn_model_config() -> None:
    """Test CNN model configuration."""
    from pokertool.neural_evaluator import CNNModelConfig, CNNHandStrengthModel
    
    config = CNNModelConfig(
        conv_layers=(32, 64, 128),
        dense_layers=(256, 128, 64),
        learning_rate=0.0005,
        batch_size=128,
    )
    
    model = CNNHandStrengthModel(config=config)
    
    assert model.config.conv_layers == (32, 64, 128)
    assert model.config.dense_layers == (256, 128, 64)
    assert model.config.learning_rate == 0.0005
    assert model.config.batch_size == 128

