"""Heuristic-driven AI bluff detection for PokerTool."""

from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional, Sequence

from .gto_solver import Action, Street
from .ml_opponent_modeling import HandHistory


@dataclass
class ActionTiming:
    """Capture timing data for a single betting decision."""

    stage: Street
    action: Action
    decision_time: float
    pot_before_action: float = 0.0
    effective_stack: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.stage, str):
            value = self.stage.strip()
            try:
                self.stage = Street[value.upper()]
            except KeyError:
                self.stage = Street(value.lower())
        if isinstance(self.action, str):
            value = self.action.strip()
            try:
                self.action = Action[value.upper()]
            except KeyError:
                self.action = Action(value.lower())


@dataclass
class ShowdownObservation:
    """Observed showdown outcome used for learning."""

    won_hand: bool
    revealed_hand_strength: float
    was_bluff: bool

    def __post_init__(self) -> None:
        self.revealed_hand_strength = max(0.0, min(1.0, self.revealed_hand_strength))


@dataclass
class BluffAssessment:
    """Output of a bluff analysis pass for a single hand."""

    player_id: str
    bluff_probability: float
    reliability: float
    signals: Dict[str, float]
    timestamp: float = field(default_factory=time.time)


@dataclass
class PlayerBluffProfile:
    """Persisted bluff-related telemetry for a player."""

    player_id: str
    hands_analyzed: int = 0
    suspicious_timing_events: int = 0
    aggressive_sequences: int = 0
    showdown_count: int = 0
    bluff_showdowns: int = 0
    recent_probabilities: Deque[float] = field(default_factory=lambda: deque(maxlen=50))
    last_assessment: Optional[BluffAssessment] = None
    last_updated: float = field(default_factory=time.time)

    @property
    def bluff_frequency(self) -> float:
        if self.showdown_count == 0:
            return 0.0
        return self.bluff_showdowns / self.showdown_count

    def average_probability(self) -> float:
        if not self.recent_probabilities:
            return 0.0
        return statistics.mean(self.recent_probabilities)


class BluffDetectionEngine:
    """Central orchestrator for bluff signal analysis."""

    QUICK_DECISION_THRESHOLD = 1.8
    SLOW_DECISION_THRESHOLD = 9.0

    def __init__(self, recent_window: int = 25):
        self._profiles: Dict[str, PlayerBluffProfile] = {}
        self._recent_window = recent_window

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def analyse_hand(
        self,
        player_id: str,
        hand_history: HandHistory,
        action_timings: Optional[Sequence[ActionTiming]] = None,
        showdown: Optional[ShowdownObservation] = None
    ) -> BluffAssessment:
        """Analyse a hand and update the underlying bluff profile."""
        profile = self._profiles.setdefault(player_id, PlayerBluffProfile(player_id))
        profile.hands_analyzed += 1

        timings = list(action_timings or [])
        timing_score = self._score_timing_signals(profile, timings)
        pattern_score = self._score_betting_patterns(profile, hand_history)
        historical_score = self._score_historical(profile)

        combined = 0.4 * timing_score + 0.4 * pattern_score + 0.2 * historical_score
        bluff_probability = max(0.0, min(1.0, combined))

        reliability = self._calculate_reliability(profile, len(timings), showdown is not None)

        showdown_adjustment: Optional[float] = None
        if showdown:
            bluff_probability, showdown_adjustment = self._update_from_showdown(profile, showdown, bluff_probability)
        else:
            profile.last_updated = time.time()

        assessment = BluffAssessment(
            player_id=player_id,
            bluff_probability=bluff_probability,
            reliability=reliability,
            signals={
                'timing': timing_score,
                'patterns': pattern_score,
                'historical': historical_score,
            }
        )
        if showdown_adjustment is not None:
            assessment.signals['post_showdown_adjustment'] = showdown_adjustment
        profile.recent_probabilities.append(bluff_probability)
        profile.last_assessment = assessment
        profile.last_updated = assessment.timestamp
        return assessment

    def get_profile(self, player_id: str) -> Optional[PlayerBluffProfile]:
        """Return the immutable profile snapshot for a player."""
        return self._profiles.get(player_id)

    def get_bluff_frequency(self, player_id: str) -> float:
        """Return the tracked showdown bluff frequency for a player."""
        profile = self._profiles.get(player_id)
        if not profile:
            return 0.0
        return profile.bluff_frequency

    # ------------------------------------------------------------------
    # Internal scoring helpers
    # ------------------------------------------------------------------
    def _score_timing_signals(self, profile: PlayerBluffProfile, timings: Sequence[ActionTiming]) -> float:
        if not timings:
            return 0.0

        suspicious_weight = 0.0
        total_weight = 0.0
        for timing in timings:
            if timing.action not in {Action.BET, Action.RAISE, Action.ALL_IN}:
                continue
            total_weight += 1.0
            if timing.decision_time <= self.QUICK_DECISION_THRESHOLD:
                suspicious_weight += 0.6
            elif timing.decision_time >= self.SLOW_DECISION_THRESHOLD:
                suspicious_weight += 0.4

            stack_ratio = 0.0
            if timing.effective_stack > 0:
                stack_ratio = timing.pot_before_action / timing.effective_stack
            if stack_ratio < 0.25 and timing.decision_time < 1.0:
                suspicious_weight += 0.3
            elif stack_ratio > 0.9 and timing.decision_time > 7.0:
                suspicious_weight += 0.2

        if total_weight == 0:
            return 0.0

        score = min(1.0, suspicious_weight / total_weight)
        if score >= 0.6:
            profile.suspicious_timing_events += 1
        return score

    def _score_betting_patterns(self, profile: PlayerBluffProfile, hand_history: HandHistory) -> float:
        actions = hand_history.actions or []
        if not actions:
            return 0.0

        aggressive_actions = 0
        streets_aggressed = set()
        overbet_signals = 0
        pot_reference = max(hand_history.pot_size, 1.0)

        for street, action, amount in actions:
            if isinstance(street, Street):
                street_value = street.value
            else:
                street_value = str(street).lower()

            if action in {Action.BET, Action.RAISE, Action.ALL_IN}:
                aggressive_actions += 1
                streets_aggressed.add(street_value)
                if amount >= pot_reference * 0.75:
                    overbet_signals += 1
                if street_value in {'turn', 'river'} and amount >= pot_reference * 0.5:
                    overbet_signals += 0.5

        if aggressive_actions == 0:
            return 0.0

        aggression_component = min(1.0, aggressive_actions * 0.18)
        street_component = min(0.4, len(streets_aggressed) * 0.18)
        overbet_component = min(0.4, overbet_signals * 0.2)
        score = min(1.0, aggression_component + street_component + overbet_component)
        if score >= 0.55:
            profile.aggressive_sequences += 1
        return score

    def _score_historical(self, profile: PlayerBluffProfile) -> float:
        if profile.showdown_count >= 3:
            baseline = 0.35 + 0.65 * profile.bluff_frequency
            return max(0.0, min(1.0, baseline))

        if profile.hands_analyzed == 0:
            return 0.0
        return max(0.0, min(0.6, profile.suspicious_timing_events / profile.hands_analyzed))

    def _calculate_reliability(self, profile: PlayerBluffProfile, timing_events: int, observed_showdown: bool) -> float:
        base = 0.15
        base += min(0.45, profile.showdown_count / 10.0)
        base += min(0.2, profile.hands_analyzed / 60.0)
        if timing_events:
            base += min(0.1, timing_events / 20.0)
        if observed_showdown:
            base += 0.1
        decay = max(0.0, (time.time() - profile.last_updated) / 600.0)
        return max(0.1, min(1.0, base - decay))

    def _update_from_showdown(
        self,
        profile: PlayerBluffProfile,
        showdown: ShowdownObservation,
        current_probability: float
    ) -> tuple[float, float]:
        profile.showdown_count += 1
        if showdown.was_bluff:
            profile.bluff_showdowns += 1
        profile.last_updated = time.time()

        adjustment = 0.0
        if showdown.was_bluff:
            adjustment = 0.1
        elif current_probability > 0.6:
            adjustment = -0.05
        adjusted = max(0.0, min(1.0, current_probability + adjustment))
        return adjusted, adjustment


__all__ = [
    'ActionTiming',
    'ShowdownObservation',
    'BluffAssessment',
    'PlayerBluffProfile',
    'BluffDetectionEngine',
]
