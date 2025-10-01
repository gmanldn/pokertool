"""Tests for the AI bluff detection engine."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.bluff_detection import (
    ActionTiming,
    BluffDetectionEngine,
    ShowdownObservation,
)
from pokertool.gto_solver import Action, Street
from pokertool.ml_opponent_modeling import HandHistory


def _build_aggressive_hand(hand_id: str) -> HandHistory:
    return HandHistory(
        hand_id=hand_id,
        player_id="villain",
        position="BTN",
        hole_cards=["As", "7d"],
        board=["Kh", "8c", "2s", "Jd", "4h"],
        actions=[
            (Street.FLOP.value, Action.BET, 80.0),
            (Street.TURN.value, Action.BET, 95.0),
            (Street.RIVER.value, Action.ALL_IN, 220.0),
        ],
        pot_size=260.0,
        stack_size=400.0,
        showdown=False,
    )


def _fast_action_timings() -> List[ActionTiming]:
    return [
        ActionTiming(stage=Street.FLOP, action=Action.BET, decision_time=0.9, pot_before_action=120.0, effective_stack=400.0),
        ActionTiming(stage=Street.TURN, action=Action.BET, decision_time=1.1, pot_before_action=200.0, effective_stack=310.0),
        ActionTiming(stage=Street.RIVER, action=Action.ALL_IN, decision_time=1.4, pot_before_action=260.0, effective_stack=220.0),
    ]


def test_aggressive_signals_trigger_high_bluff_probability():
    engine = BluffDetectionEngine()
    hand = _build_aggressive_hand("H001")
    assessment = engine.analyse_hand("villain", hand, _fast_action_timings())

    assert assessment.bluff_probability > 0.6
    assert assessment.signals["timing"] >= 0.6
    assert assessment.signals["patterns"] >= 0.5
    assert assessment.reliability >= 0.15


def test_showdown_learning_tracks_frequency_and_reliability_growth():
    engine = BluffDetectionEngine()
    hand = _build_aggressive_hand("H002")

    first = engine.analyse_hand("villain", hand, _fast_action_timings())
    assert first.reliability < 0.5

    for idx in range(3):
        showdown = ShowdownObservation(
            won_hand=idx % 2 == 0,
            revealed_hand_strength=0.25,
            was_bluff=True,
        )
        engine.analyse_hand("villain", hand, _fast_action_timings(), showdown)

    profile = engine.get_profile("villain")
    assert profile is not None
    assert profile.showdown_count == 3
    assert engine.get_bluff_frequency("villain") == 1.0

    latest = engine.analyse_hand("villain", hand, _fast_action_timings())
    assert latest.reliability > first.reliability


def test_false_positive_showdown_tempers_future_estimates():
    engine = BluffDetectionEngine()
    hand = _build_aggressive_hand("H003")

    pre_showdown = engine.analyse_hand("villain", hand, _fast_action_timings())
    assert pre_showdown.bluff_probability > 0.6

    # Player shows value after a suspicious line, expect adjustment downward.
    showdown = ShowdownObservation(
        won_hand=True,
        revealed_hand_strength=0.9,
        was_bluff=False,
    )
    post_showdown = engine.analyse_hand("villain", hand, _fast_action_timings(), showdown)
    assert post_showdown.signals.get("post_showdown_adjustment", 0.0) <= 0.0
    assert post_showdown.bluff_probability <= pre_showdown.bluff_probability
