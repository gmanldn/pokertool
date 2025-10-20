"""Tests for the gamification engine."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.gamification import Achievement, Badge, GamificationEngine


def create_engine(tmp_path: Path) -> GamificationEngine:
    storage = tmp_path / "gamification"
    return GamificationEngine(storage_dir=storage)


def test_achievements_badges_and_leaderboard(tmp_path):
    engine = create_engine(tmp_path)
    achievement = Achievement(achievement_id="volume_grinder", title="Volume Grinder", description="Play 100 hands in a day", points=200, condition={"hands_played": 100})
    engine.register_achievement(achievement)

    badge = Badge(badge_id="marathon", title="Marathon", description="Complete 7-day streak", tier="gold")
    engine.register_badge(badge)

    metrics = {"hands_played": 120}
    state = engine.record_activity("hero", metrics)
    assert "volume_grinder" in state.achievements_unlocked
    assert state.level >= 1

    engine.award_badge("hero", "marathon")
    assert "marathon" in engine.progress_snapshot("hero").badges_earned

    engine.add_experience("rival", 900)
    leaderboard = engine.leaderboard()
    assert leaderboard[0].player_id in {"hero", "rival"}

    export_path = engine.export_state()
    assert export_path.exists()
