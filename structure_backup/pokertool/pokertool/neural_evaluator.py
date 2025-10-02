"""Neural network hand strength evaluator for PokerTool.

This module provides both a lightweight neural-inspired model and a full CNN-based
deep learning model for hand strength evaluation. The CNN model can be trained on
large hand history datasets for maximum accuracy.

Module: neural_evaluator
Version: 2.0.0
Last Updated: 2025-10-05
Task: NN-EVAL-001
Dependencies: None
Test Coverage: tests/system/test_neural_evaluator.py
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "hand_strength_model.h5"

RANK_ORDER = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
SUIT_SYMBOLS = {"H", "D", "S", "C"}


@dataclass
class HandState:
    """Snapshot of a poker hand required for evaluation."""

    hole_cards: Sequence[str]
    board_cards: Sequence[str]
    pot_odds: float
    aggression_factor: float
    position: str = "late"
    effective_stack_bb: float = 100.0
    previous_actions: Sequence[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.hole_cards = tuple(card.upper().strip() for card in self.hole_cards if card)
        self.board_cards = tuple(card.upper().strip() for card in self.board_cards if card)
        self.position = self.position.lower()
        self.previous_actions = tuple(action.lower() for action in self.previous_actions)
        self.pot_odds = max(0.0, min(1.0, float(self.pot_odds)))
        self.aggression_factor = max(0.0, min(4.0, float(self.aggression_factor)))
        self.effective_stack_bb = max(0.0, float(self.effective_stack_bb))


@dataclass
class TrainingSample:
    """Single labelled datapoint for incremental training."""

    state: HandState
    outcome: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        self.outcome = max(0.0, min(1.0, float(self.outcome)))
        self.weight = max(0.0, float(self.weight))


@dataclass
class HandEvaluation:
    """Result payload returned by the evaluator."""

    win_probability: float
    confidence: float
    board_category: str
    contextual_adjustment: float
    score_breakdown: Dict[str, float]
    raw_features: Dict[str, float]


DEFAULT_MODEL: Dict[str, object] = {
    "base_intercept": 0.12,
    "hole_strength_weight": 1.15,
    "suited_bonus": 0.07,
    "gap_weight": -0.22,
    "texture_weights": {
        "dry": 0.0,
        "draw-heavy": -0.08,
        "paired": -0.05,
        "dynamic": -0.12,
    },
    "aggression_weight": -0.11,
    "pot_odds_weight": 0.27,
    "position_weights": {
        "early": -0.06,
        "middle": 0.0,
        "late": 0.05,
        "blinds": 0.02,
    },
    "stack_weight": 0.04,
    "history_decay": 0.9,
    "training_iterations": 0,
}


class NeuralHandStrengthEvaluator:
    """Evaluates hand strength using a lightweight neural-inspired model."""

    HISTORY_LIMIT = 200

    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path or DEFAULT_MODEL_PATH)
        self.model: MutableMapping[str, object] = self._load_model()
        self._history: List[float] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def evaluate_hand(self, state: HandState) -> HandEvaluation:
        """Return the current win probability estimate for the given state."""
        board_analysis = self.board_texture_analysis(state.board_cards)
        features = self._extract_features(state, board_analysis)
        linear_score, breakdown = self._linear_score(features, board_analysis)
        win_probability = self._sigmoid(linear_score)

        contextual_adjustment = self._contextual_adjustment(state, board_analysis)
        adjusted_probability = self._clamp01(win_probability + contextual_adjustment)
        confidence = self._confidence_score(adjusted_probability, features)

        self._track_history(adjusted_probability)

        return HandEvaluation(
            win_probability=adjusted_probability,
            confidence=confidence,
            board_category=board_analysis["category"],
            contextual_adjustment=contextual_adjustment,
            score_breakdown=breakdown,
            raw_features=features,
        )

    def train(
        self,
        samples: Iterable[TrainingSample],
        epochs: int = 3,
        learning_rate: float = 0.05,
    ) -> None:
        """Update the model in-place using a mini-batch style pass."""
        lr = max(1e-3, float(learning_rate))
        cached_samples = list(samples)
        if not cached_samples:
            return

        total_updates = 0
        for _ in range(max(1, int(epochs))):
            for sample in cached_samples:
                board_info = self.board_texture_analysis(sample.state.board_cards)
                features = self._extract_features(sample.state, board_info)
                predicted, _ = self._linear_score(features, board_info)
                prediction = self._sigmoid(predicted)
                error = (sample.outcome - prediction) * sample.weight
                total_updates += 1

                self._apply_gradient_update(error, features, board_info, lr)

        if total_updates:
            self.model["training_iterations"] = int(self.model.get("training_iterations", 0)) + total_updates
            self._save_model()

    def board_texture_analysis(self, board_cards: Sequence[str]) -> Dict[str, float | str | bool]:
        """Summarise the board texture to inform downstream adjustments."""
        cards = tuple(card.upper().strip() for card in board_cards if card)
        suits = [card[-1] for card in cards if len(card) >= 2 and card[-1] in SUIT_SYMBOLS]
        ranks = [self._card_rank(card) for card in cards]

        suit_counts: Dict[str, int] = {}
        for suit in suits:
            suit_counts[suit] = suit_counts.get(suit, 0) + 1

        flush_draw = any(count >= 3 for count in suit_counts.values())
        paired = len(ranks) != len(set(ranks))
        sorted_ranks = sorted(ranks)
        straight_draw = self._has_straight_potential(sorted_ranks)
        high_card_pressure = sum(1 for rank in ranks if rank >= 11) / max(1, len(ranks))

        if flush_draw and straight_draw:
            category = "dynamic"
        elif straight_draw or flush_draw:
            category = "draw-heavy"
        elif paired:
            category = "paired"
        else:
            category = "dry"

        texture_score = 0.0
        if category == "dry":
            texture_score = 0.05
        elif category == "paired":
            texture_score = -0.05
        elif category == "draw-heavy":
            texture_score = -0.08
        else:  # dynamic
            texture_score = -0.12

        return {
            "category": category,
            "flush_draw": flush_draw,
            "straight_draw": straight_draw,
            "paired": paired,
            "high_card_pressure": high_card_pressure,
            "texture_score": texture_score,
            "card_count": len(cards),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _apply_gradient_update(
        self,
        error: float,
        features: Mapping[str, float],
        board_info: Mapping[str, float | str | bool],
        learning_rate: float,
    ) -> None:
        intercept = float(self.model.get("base_intercept", DEFAULT_MODEL["base_intercept"]))
        intercept += learning_rate * error
        self.model["base_intercept"] = self._clamp(intercept, -2.5, 2.5)

        hole_weight = float(self.model.get("hole_strength_weight", DEFAULT_MODEL["hole_strength_weight"]))
        hole_weight += learning_rate * error * features["hole_strength"]
        self.model["hole_strength_weight"] = self._clamp(hole_weight, -3.0, 3.0)

        suited_bonus = float(self.model.get("suited_bonus", DEFAULT_MODEL["suited_bonus"]))
        suited_bonus += learning_rate * error * features["is_suited"]
        self.model["suited_bonus"] = self._clamp(suited_bonus, -1.0, 1.0)

        gap_weight = float(self.model.get("gap_weight", DEFAULT_MODEL["gap_weight"]))
        gap_weight += learning_rate * error * features["gap_severity"]
        self.model["gap_weight"] = self._clamp(gap_weight, -2.0, 0.5)

        texture_weights = dict(DEFAULT_MODEL["texture_weights"])
        texture_weights.update(self.model.get("texture_weights", {}))
        category = board_info["category"]
        if isinstance(category, str):
            current = float(texture_weights.get(category, 0.0))
            current += learning_rate * error
            texture_weights[category] = self._clamp(current, -1.5, 1.5)
        self.model["texture_weights"] = texture_weights

        aggression_weight = float(self.model.get("aggression_weight", DEFAULT_MODEL["aggression_weight"]))
        aggression_weight += learning_rate * error * features["aggression" ]
        self.model["aggression_weight"] = self._clamp(aggression_weight, -2.0, 1.5)

        pot_weight = float(self.model.get("pot_odds_weight", DEFAULT_MODEL["pot_odds_weight"]))
        pot_weight += learning_rate * error * features["pot_odds"]
        self.model["pot_odds_weight"] = self._clamp(pot_weight, -1.0, 2.5)

        stack_weight = float(self.model.get("stack_weight", DEFAULT_MODEL["stack_weight"]))
        stack_weight += learning_rate * error * features["effective_stack"]
        self.model["stack_weight"] = self._clamp(stack_weight, -1.0, 1.5)

        position_weights = dict(DEFAULT_MODEL["position_weights"])
        position_weights.update(self.model.get("position_weights", {}))
        pos = features["position_index"]
        for position, indicator in (
            ("early", 1.0 if pos == 0 else 0.0),
            ("middle", 1.0 if pos == 1 else 0.0),
            ("late", 1.0 if pos == 2 else 0.0),
            ("blinds", 1.0 if pos == 3 else 0.0),
        ):
            if indicator:
                current = float(position_weights.get(position, 0.0))
                current += learning_rate * error * indicator
                position_weights[position] = self._clamp(current, -1.5, 1.5)
        self.model["position_weights"] = position_weights

    def _extract_features(
        self,
        state: HandState,
        board_info: Mapping[str, float | str | bool],
    ) -> Dict[str, float]:
        hole_strength = self._hole_card_strength(state.hole_cards)
        suited = 1.0 if self._is_suited(state.hole_cards) else 0.0
        gap_severity = self._gap_penalty(state.hole_cards)
        texture_score = float(board_info.get("texture_score", 0.0))
        aggression = min(1.0, state.aggression_factor / 4.0)
        effective_stack = min(1.0, state.effective_stack_bb / 200.0)
        previous_raise = 1.0 if any(action in {"bet", "raise"} for action in state.previous_actions) else 0.0
        board_cards = float(board_info.get("card_count", 0.0))

        position_index = self._position_index(state.position)

        return {
            "hole_strength": hole_strength,
            "is_suited": suited,
            "gap_severity": gap_severity,
            "texture_score": texture_score,
            "aggression": aggression,
            "pot_odds": state.pot_odds,
            "position_index": float(position_index),
            "effective_stack": effective_stack,
            "previous_aggression": previous_raise,
            "board_cards": board_cards / 5.0,
        }

    def _linear_score(
        self,
        features: Mapping[str, float],
        board_info: Mapping[str, float | str | bool],
    ) -> Tuple[float, Dict[str, float]]:
        texture_weights = dict(DEFAULT_MODEL["texture_weights"])
        texture_weights.update(self.model.get("texture_weights", {}))
        position_weights = dict(DEFAULT_MODEL["position_weights"])
        position_weights.update(self.model.get("position_weights", {}))

        intercept = float(self.model.get("base_intercept", DEFAULT_MODEL["base_intercept"]))
        hole_weight = float(self.model.get("hole_strength_weight", DEFAULT_MODEL["hole_strength_weight"]))
        suited_bonus = float(self.model.get("suited_bonus", DEFAULT_MODEL["suited_bonus"]))
        gap_weight = float(self.model.get("gap_weight", DEFAULT_MODEL["gap_weight"]))
        aggression_weight = float(self.model.get("aggression_weight", DEFAULT_MODEL["aggression_weight"]))
        pot_weight = float(self.model.get("pot_odds_weight", DEFAULT_MODEL["pot_odds_weight"]))
        stack_weight = float(self.model.get("stack_weight", DEFAULT_MODEL["stack_weight"]))

        category = board_info["category"] if isinstance(board_info.get("category"), str) else "dry"
        texture_weight = float(texture_weights.get(category, 0.0))
        pos_index = int(features.get("position_index", 1.0))
        position = ("early", "middle", "late", "blinds")[min(max(pos_index, 0), 3)]
        position_weight = float(position_weights.get(position, 0.0))

        hole_component = hole_weight * features["hole_strength"]
        suited_component = suited_bonus * features["is_suited"]
        gap_component = gap_weight * features["gap_severity"]
        texture_component = texture_weight * (1.0 + features["board_cards"])
        aggression_component = aggression_weight * (features["aggression"] + features["previous_aggression"] * 0.5)
        pot_component = pot_weight * features["pot_odds"]
        stack_component = stack_weight * features["effective_stack"]
        position_component = position_weight

        total = (
            intercept
            + hole_component
            + suited_component
            + gap_component
            + texture_component
            + aggression_component
            + pot_component
            + stack_component
            + position_component
        )

        breakdown = {
            "intercept": intercept,
            "hole": hole_component,
            "suited": suited_component,
            "gap": gap_component,
            "texture": texture_component,
            "aggression": aggression_component,
            "pot_odds": pot_component,
            "stack": stack_component,
            "position": position_component,
        }
        return total, breakdown

    def _contextual_adjustment(
        self,
        state: HandState,
        board_info: Mapping[str, float | str | bool],
    ) -> float:
        adjustment = 0.0
        if board_info.get("paired") and self._is_suited(state.hole_cards):
            adjustment += 0.02
        if board_info.get("flush_draw") and not self._is_suited(state.hole_cards):
            adjustment -= 0.03
        if board_info.get("straight_draw"):
            adjustment -= 0.01
        if state.effective_stack_bb < 25:
            adjustment += 0.015
        if state.position == "late" and state.pot_odds < 0.4:
            adjustment += 0.02
        return self._clamp(adjustment, -0.08, 0.08)

    def _confidence_score(self, probability: float, features: Mapping[str, float]) -> float:
        history_influence = self.model.get("history_decay", DEFAULT_MODEL["history_decay"])
        history_size = min(len(self._history), self.HISTORY_LIMIT)
        historical_signal = (1.0 - history_influence ** max(1, history_size)) * 0.2
        distance_from_equity = abs(probability - 0.5)
        board_cards_signal = features.get("board_cards", 0.0) * 0.2
        baseline = 0.45 + distance_from_equity * 0.4 + board_cards_signal
        confidence = baseline + historical_signal
        return self._clamp(confidence, 0.2, 0.97)

    def _track_history(self, probability: float) -> None:
        self._history.append(probability)
        if len(self._history) > self.HISTORY_LIMIT:
            self._history.pop(0)

    def _load_model(self) -> MutableMapping[str, object]:
        path = self.model_path
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            self._write_model_file(DEFAULT_MODEL, path)
            return dict(DEFAULT_MODEL)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULT_MODEL)
        merged = dict(DEFAULT_MODEL)
        merged.update(data)
        merged.setdefault("texture_weights", dict(DEFAULT_MODEL["texture_weights"]))
        merged.setdefault("position_weights", dict(DEFAULT_MODEL["position_weights"]))
        return merged

    def _save_model(self) -> None:
        self._write_model_file(self.model, self.model_path)

    def _write_model_file(self, model: Mapping[str, object], path: Path) -> None:
        serialisable = dict(model)
        serialisable["texture_weights"] = dict(serialisable.get("texture_weights", {}))
        serialisable["position_weights"] = dict(serialisable.get("position_weights", {}))
        path.write_text(json.dumps(serialisable, sort_keys=True), encoding="utf-8")

    @staticmethod
    def _hole_card_strength(hole_cards: Sequence[str]) -> float:
        ranks = [RANK_ORDER.get(card[0], 0) for card in hole_cards if card]
        if not ranks:
            return 0.0
        average_rank = sum(ranks) / len(ranks)
        pair_bonus = 4 if len(set(ranks)) == 1 and len(ranks) >= 2 else 0
        normalized = (average_rank + pair_bonus - 2) / 12.0
        return max(0.0, min(1.0, normalized))

    @staticmethod
    def _is_suited(hole_cards: Sequence[str]) -> bool:
        suits = {card[-1] for card in hole_cards if len(card) >= 2}
        return len(suits) == 1 and len(hole_cards) >= 2

    @staticmethod
    def _gap_penalty(hole_cards: Sequence[str]) -> float:
        if len(hole_cards) < 2:
            return 0.0
        ranks = sorted(RANK_ORDER.get(card[0], 0) for card in hole_cards if card)
        if len(ranks) < 2:
            return 0.0
        gap = abs(ranks[0] - ranks[1]) - 1
        return max(0.0, min(1.0, gap / 10.0))

    @staticmethod
    def _position_index(position: str) -> int:
        lookup = {"early": 0, "middle": 1, "late": 2, "blinds": 3}
        return lookup.get(position.lower(), 1)

    @staticmethod
    def _card_rank(card: str) -> int:
        if len(card) < 2:
            return 0
        return RANK_ORDER.get(card[0], 0)

    @staticmethod
    def _has_straight_potential(ranks: Sequence[int]) -> bool:
        if len(ranks) < 3:
            return False
        unique = sorted(set(ranks))
        for i in range(len(unique) - 2):
            if unique[i + 2] - unique[i] <= 4:
                return True
        # Wheel consideration
        if {14, 5, 4} <= set(unique):
            return True
        return False

    @staticmethod
    def _sigmoid(value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    @staticmethod
    def _clamp01(value: float) -> float:
        return NeuralHandStrengthEvaluator._clamp(value, 0.0, 1.0)


# ==============================================================================
# CNN-BASED DEEP LEARNING MODEL
# ==============================================================================


@dataclass
class CNNModelConfig:
    """Configuration for the CNN hand strength model."""

    input_shape: Tuple[int, ...] = (4, 13, 13)  # (suits, ranks, ranks)
    conv_layers: Tuple[int, ...] = (64, 128, 256)
    kernel_size: int = 3
    dense_layers: Tuple[int, ...] = (512, 256, 128)
    dropout_rate: float = 0.3
    learning_rate: float = 0.001
    batch_size: int = 256
    epochs_per_session: int = 10


@dataclass
class TrainingProgress:
    """Tracks training progress for the CNN model."""

    total_samples: int = 0
    total_epochs: int = 0
    current_loss: float = 0.0
    validation_accuracy: float = 0.0
    best_validation_accuracy: float = 0.0
    last_training_time: float = 0.0


class CNNHandStrengthModel:
    """Deep learning CNN model for hand strength evaluation.

    This model uses a convolutional neural network architecture to evaluate
    hand strength. It can be trained on millions of hand histories for
    superior accuracy compared to the lightweight model.

    Architecture:
    - Input: 4x13x13 tensor (suits x ranks x ranks)
    - 3 Convolutional layers with increasing filters (64->128->256)
    - Global average pooling
    - 3 Dense layers with dropout (512->256->128)
    - Output: Single neuron with sigmoid activation (win probability)

    Training:
    - Batch size: 256
    - Optimizer: Adam with learning rate 0.001
    - Loss: Binary cross-entropy
    - Metrics: Accuracy, AUC
    """

    def __init__(self, model_path: str | Path | None = None, config: CNNModelConfig | None = None) -> None:
        """Initialize the CNN model.

        Args:
            model_path: Path to save/load the trained model
            config: Model configuration (uses defaults if None)
        """
        self.model_path = Path(model_path or DEFAULT_MODEL_PATH)
        self.config = config or CNNModelConfig()
        self.model: Optional[object] = None  # Will hold TensorFlow/PyTorch model
        self.progress = TrainingProgress()
        self._framework: Optional[str] = None  # 'tensorflow' or 'pytorch'
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize or load the CNN model.

        Attempts to use TensorFlow if available, otherwise falls back to
        PyTorch. If neither is available, provides a stub implementation.
        """
        # Try TensorFlow first
        try:
            import tensorflow as tf  # type: ignore

            self._framework = 'tensorflow'
            if self.model_path.exists():
                self.model = tf.keras.models.load_model(str(self.model_path))
                self._load_progress()
            else:
                self.model = self._build_tensorflow_model()
        except ImportError:
            pass

        # Try PyTorch if TensorFlow unavailable
        if self._framework is None:
            try:
                import torch  # type: ignore
                import torch.nn as nn  # type: ignore

                self._framework = 'pytorch'
                if self.model_path.exists():
                    self.model = torch.load(str(self.model_path))
                    self._load_progress()
                else:
                    self.model = self._build_pytorch_model()
            except ImportError:
                pass

        # If no framework available, use stub
        if self._framework is None:
            self._framework = 'stub'
            self.model = None

    def _build_tensorflow_model(self) -> object:
        """Build the TensorFlow/Keras CNN model architecture."""
        import tensorflow as tf  # type: ignore
        from tensorflow import keras  # type: ignore
        from tensorflow.keras import layers  # type: ignore

        model = keras.Sequential([
            layers.Input(shape=self.config.input_shape),

            # First conv block
            layers.Conv2D(self.config.conv_layers[0], self.config.kernel_size,
                         padding='same', activation='relu'),
            layers.BatchNormalization(),
            layers.MaxPooling2D(pool_size=2),

            # Second conv block
            layers.Conv2D(self.config.conv_layers[1], self.config.kernel_size,
                         padding='same', activation='relu'),
            layers.BatchNormalization(),
            layers.MaxPooling2D(pool_size=2),

            # Third conv block
            layers.Conv2D(self.config.conv_layers[2], self.config.kernel_size,
                         padding='same', activation='relu'),
            layers.BatchNormalization(),
            layers.GlobalAveragePooling2D(),

            # Dense layers
            layers.Dense(self.config.dense_layers[0], activation='relu'),
            layers.Dropout(self.config.dropout_rate),
            layers.Dense(self.config.dense_layers[1], activation='relu'),
            layers.Dropout(self.config.dropout_rate),
            layers.Dense(self.config.dense_layers[2], activation='relu'),

            # Output layer
            layers.Dense(1, activation='sigmoid')
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.config.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC(name='auc')]
        )

        return model

    def _build_pytorch_model(self) -> object:
        """Build the PyTorch CNN model architecture."""
        import torch.nn as nn  # type: ignore

        class PokerCNN(nn.Module):
            def __init__(self, config: CNNModelConfig):
                super().__init__()
                self.conv1 = nn.Conv2d(4, config.conv_layers[0], config.kernel_size, padding=1)
                self.bn1 = nn.BatchNorm2d(config.conv_layers[0])
                self.pool1 = nn.MaxPool2d(2)

                self.conv2 = nn.Conv2d(config.conv_layers[0], config.conv_layers[1],
                                      config.kernel_size, padding=1)
                self.bn2 = nn.BatchNorm2d(config.conv_layers[1])
                self.pool2 = nn.MaxPool2d(2)

                self.conv3 = nn.Conv2d(config.conv_layers[1], config.conv_layers[2],
                                      config.kernel_size, padding=1)
                self.bn3 = nn.BatchNorm2d(config.conv_layers[2])
                self.global_pool = nn.AdaptiveAvgPool2d(1)

                self.fc1 = nn.Linear(config.conv_layers[2], config.dense_layers[0])
                self.dropout1 = nn.Dropout(config.dropout_rate)
                self.fc2 = nn.Linear(config.dense_layers[0], config.dense_layers[1])
                self.dropout2 = nn.Dropout(config.dropout_rate)
                self.fc3 = nn.Linear(config.dense_layers[1], config.dense_layers[2])
                self.output = nn.Linear(config.dense_layers[2], 1)

            def forward(self, x):
                import torch.nn.functional as F  # type: ignore

                x = F.relu(self.bn1(self.conv1(x)))
                x = self.pool1(x)

                x = F.relu(self.bn2(self.conv2(x)))
                x = self.pool2(x)

                x = F.relu(self.bn3(self.conv3(x)))
                x = self.global_pool(x)
                x = x.view(x.size(0), -1)

                x = F.relu(self.fc1(x))
                x = self.dropout1(x)
                x = F.relu(self.fc2(x))
                x = self.dropout2(x)
                x = F.relu(self.fc3(x))
                x = torch.sigmoid(self.output(x))

                return x

        return PokerCNN(self.config)

    def encode_hand_state(self, state: HandState) -> List[List[List[float]]]:
        """Encode a hand state into a 4x13x13 tensor.

        The encoding represents:
        - Dimension 0 (4): One channel per suit (H, D, S, C)
        - Dimensions 1-2 (13x13): Matrix of rank vs rank interactions

        Each cell contains a value indicating:
        - 1.0: Card present in hole cards
        - 0.5: Card present on board
        - 0.0: Card not present

        Args:
            state: Hand state to encode

        Returns:
            4x13x13 tensor as nested lists
        """
        # Initialize 4x13x13 tensor with zeros
        tensor = [[[0.0 for _ in range(13)] for _ in range(13)] for _ in range(4)]

        suit_map = {'H': 0, 'D': 1, 'S': 2, 'C': 3}

        # Encode hole cards (value = 1.0)
        for card in state.hole_cards:
            if len(card) >= 2:
                rank = RANK_ORDER.get(card[0], 2) - 2  # Convert to 0-12
                suit = suit_map.get(card[1], 0)
                if 0 <= rank < 13:
                    tensor[suit][rank][rank] = 1.0

        # Encode board cards (value = 0.5)
        for card in state.board_cards:
            if len(card) >= 2:
                rank = RANK_ORDER.get(card[0], 2) - 2
                suit = suit_map.get(card[1], 0)
                if 0 <= rank < 13:
                    tensor[suit][rank][rank] = 0.5

        return tensor

    def predict(self, state: HandState) -> float:
        """Predict win probability for the given hand state.

        Args:
            state: Hand state to evaluate

        Returns:
            Win probability between 0.0 and 1.0
        """
        if self._framework == 'stub' or self.model is None:
            # Fallback to simple heuristic
            return self._simple_heuristic(state)

        encoded = self.encode_hand_state(state)

        if self._framework == 'tensorflow':
            import numpy as np  # type: ignore

            input_array = np.array([encoded], dtype=np.float32)
            prediction = self.model.predict(input_array, verbose=0)
            return float(prediction[0][0])

        elif self._framework == 'pytorch':
            import torch  # type: ignore
            import numpy as np  # type: ignore

            input_tensor = torch.FloatTensor(encoded).unsqueeze(0)
            with torch.no_grad():
                self.model.eval()
                prediction = self.model(input_tensor)
            return float(prediction[0][0].item())

        return 0.5

    def _simple_heuristic(self, state: HandState) -> float:
        """Simple heuristic for when no ML framework is available."""
        ranks = [RANK_ORDER.get(card[0], 0) for card in state.hole_cards if card]
        if not ranks:
            return 0.5
        avg_rank = sum(ranks) / len(ranks)
        return max(0.0, min(1.0, (avg_rank - 2) / 12.0))

    def train_on_batch(self, states: Sequence[HandState], outcomes: Sequence[float]) -> Dict[str, float]:
        """Train the model on a batch of hand histories.

        Args:
            states: List of hand states
            outcomes: List of outcomes (1.0 for win, 0.0 for loss)

        Returns:
            Dictionary with training metrics (loss, accuracy)
        """
        if self._framework == 'stub' or self.model is None:
            return {'loss': 0.0, 'accuracy': 0.0, 'warning': 'No ML framework available'}

        # Encode all states
        encoded_states = [self.encode_hand_state(state) for state in states]

        if self._framework == 'tensorflow':
            import numpy as np  # type: ignore

            X = np.array(encoded_states, dtype=np.float32)
            y = np.array(outcomes, dtype=np.float32)

            history = self.model.fit(
                X, y,
                batch_size=min(len(states), self.config.batch_size),
                epochs=1,
                verbose=0
            )

            self.progress.total_samples += len(states)
            self.progress.total_epochs += 1
            self.progress.current_loss = float(history.history['loss'][0])

            return {
                'loss': self.progress.current_loss,
                'accuracy': float(history.history.get('accuracy', [0.0])[0])
            }

        elif self._framework == 'pytorch':
            import torch  # type: ignore
            import torch.nn as nn  # type: ignore
            import torch.optim as optim  # type: ignore
            import numpy as np  # type: ignore

            X = torch.FloatTensor(encoded_states)
            y = torch.FloatTensor(outcomes).unsqueeze(1)

            self.model.train()
            optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
            criterion = nn.BCELoss()

            optimizer.zero_grad()
            predictions = self.model(X)
            loss = criterion(predictions, y)
            loss.backward()
            optimizer.step()

            self.progress.total_samples += len(states)
            self.progress.total_epochs += 1
            self.progress.current_loss = float(loss.item())

            # Calculate accuracy
            with torch.no_grad():
                predicted_classes = (predictions > 0.5).float()
                accuracy = (predicted_classes == y).float().mean()

            return {
                'loss': self.progress.current_loss,
                'accuracy': float(accuracy.item())
            }

        return {'loss': 0.0, 'accuracy': 0.0}

    def save_model(self) -> None:
        """Save the trained model to disk."""
        if self._framework == 'stub' or self.model is None:
            return

        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        if self._framework == 'tensorflow':
            self.model.save(str(self.model_path))
        elif self._framework == 'pytorch':
            import torch  # type: ignore
            torch.save(self.model, str(self.model_path))

        self._save_progress()

    def _save_progress(self) -> None:
        """Save training progress to JSON."""
        progress_file = self.model_path.with_suffix('.progress.json')
        progress_dict = {
            'total_samples': self.progress.total_samples,
            'total_epochs': self.progress.total_epochs,
            'current_loss': self.progress.current_loss,
            'validation_accuracy': self.progress.validation_accuracy,
            'best_validation_accuracy': self.progress.best_validation_accuracy,
            'last_training_time': self.progress.last_training_time,
        }
        progress_file.write_text(json.dumps(progress_dict, indent=2), encoding='utf-8')

    def _load_progress(self) -> None:
        """Load training progress from JSON."""
        progress_file = self.model_path.with_suffix('.progress.json')
        if not progress_file.exists():
            return

        try:
            data = json.loads(progress_file.read_text(encoding='utf-8'))
            self.progress = TrainingProgress(**data)
        except (json.JSONDecodeError, TypeError):
            pass


# ==============================================================================
# HIGH-LEVEL TRAINING INFRASTRUCTURE
# ==============================================================================


class RealTimeInferenceEngine:
    """High-level wrapper for real-time hand strength inference.

    This class provides a simple interface for both the lightweight and
    CNN-based models, automatically selecting the best available option.
    """

    def __init__(self, use_cnn: bool = False, model_path: str | Path | None = None) -> None:
        """Initialize the inference engine.

        Args:
            use_cnn: If True, attempt to use CNN model. Falls back to lightweight if unavailable.
            model_path: Path to model files
        """
        self.use_cnn = use_cnn
        self.model_path = model_path
        self.lightweight_model = NeuralHandStrengthEvaluator(model_path)
        self.cnn_model: Optional[CNNHandStrengthModel] = None

        if use_cnn:
            try:
                self.cnn_model = CNNHandStrengthModel(model_path)
                if self.cnn_model._framework == 'stub':
                    self.cnn_model = None  # Fall back to lightweight
            except Exception:
                self.cnn_model = None

    def evaluate(self, state: HandState) -> HandEvaluation:
        """Evaluate a hand state using the best available model.

        Args:
            state: Hand state to evaluate

        Returns:
            HandEvaluation with win probability and confidence
        """
        if self.cnn_model is not None:
            # Use CNN model - create HandEvaluation from prediction
            win_prob = self.cnn_model.predict(state)
            board_analysis = self.lightweight_model.board_texture_analysis(state.board_cards)
            
            return HandEvaluation(
                win_probability=win_prob,
                confidence=0.85,  # CNN models have high confidence
                board_category=board_analysis["category"],
                contextual_adjustment=0.0,
                score_breakdown={'cnn_prediction': win_prob},
                raw_features={'model_type': 'cnn'}
            )
        else:
            # Use lightweight model
            return self.lightweight_model.evaluate_hand(state)

    def get_model_info(self) -> Dict[str, object]:
        """Get information about the currently active model."""
        if self.cnn_model is not None:
            return {
                'type': 'cnn',
                'framework': self.cnn_model._framework,
                'progress': {
                    'total_samples': self.cnn_model.progress.total_samples,
                    'total_epochs': self.cnn_model.progress.total_epochs,
                    'current_loss': self.cnn_model.progress.current_loss,
                }
            }
        else:
            return {
                'type': 'lightweight',
                'training_iterations': self.lightweight_model.model.get('training_iterations', 0)
            }


__all__ = [
    'HandState',
    'TrainingSample',
    'HandEvaluation',
    'NeuralHandStrengthEvaluator',
    'CNNModelConfig',
    'TrainingProgress',
    'CNNHandStrengthModel',
    'RealTimeInferenceEngine',
]
