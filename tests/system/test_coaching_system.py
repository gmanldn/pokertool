"""Unit tests for the coaching integration system."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from pokertool.coaching_system import CoachingSystem
from pokertool.core import HandAnalysisResult, Position


def create_system(tmp_path: Path) -> CoachingSystem:
    storage = tmp_path / "progress.json"
    return CoachingSystem(storage_file=storage)


def test_mistake_detection_and_progress_tracking():
    with TemporaryDirectory() as tmp_dir:
        system = create_system(Path(tmp_dir))

        result = HandAnalysisResult(
            strength=0.82,
            advice='raise',
            details={'reason': 'Top pair strong kicker'}
        )

        feedback = system.evaluate_hand(
            hand_result=result,
            player_action='check',
            pot=15.0,
            to_call=3.0,
            position=Position.BTN,
            table_stage='river'
        )

        assert feedback.mistakes, 'Expected a missed value mistake to be detected'
        categories = {mistake.category for mistake in feedback.mistakes}
        assert 'missed_value' in categories

        snapshot = system.get_progress_snapshot()
        assert snapshot.hands_reviewed == 1
        assert snapshot.mistakes_by_category.get('missed_value') == 1
        assert snapshot.accuracy_score < 1.0
        assert snapshot.last_tip is None or isinstance(snapshot.last_tip, str)


def test_training_scenarios_can_be_completed():
    with TemporaryDirectory() as tmp_dir:
        system = create_system(Path(tmp_dir))
        scenarios = system.get_training_scenarios()
        assert len(scenarios) >= 3

        target = scenarios[0]
        assert not target.completed
        system.mark_scenario_completed(target.scenario_id)

        refreshed = system.get_training_scenarios()
        refreshed_lookup = {scenario.scenario_id: scenario for scenario in refreshed}
        assert refreshed_lookup[target.scenario_id].completed

        snapshot = system.get_progress_snapshot()
        assert snapshot.scenarios_completed == 1


def test_real_time_advice_generation():
    with TemporaryDirectory() as tmp_dir:
        system = create_system(Path(tmp_dir))

        table_state = SimpleNamespace(
            hero_cards=['As', 'Ks'],
            board_cards=['Ad', '7c', '2h'],
            pot_size=12.0,
            current_bet=4.0,
            stage='flop',
            hero_position='BTN'
        )

        advice = system.get_real_time_advice(table_state)
        assert advice is not None
        assert 'Recommended action' in advice.summary
        assert advice.recommended_action in {'bet', 'raise', 'call', 'fold', 'check'}

        tips = system.get_personalized_tips()
        assert tips, 'Expected at least one generic coaching tip'
