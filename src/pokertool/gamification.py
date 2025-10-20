"""Gamification engine with achievements, badges, and progress tracking."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_GAMIFICATION_DIR = Path.home() / ".pokertool" / "gamification"
DEFAULT_GAMIFICATION_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Achievement:
    """Achievement definition."""

    achievement_id: str
    title: str
    description: str
    points: int
    condition: Dict[str, int]


@dataclass
class Badge:
    """Badge definition."""

    badge_id: str
    title: str
    description: str
    tier: str


@dataclass
class ProgressState:
    """Player gamification progress."""

    player_id: str
    experience: int = 0
    level: int = 1
    achievements_unlocked: List[str] = field(default_factory=list)
    badges_earned: List[str] = field(default_factory=list)
    streak_days: int = 0
    last_active_day: Optional[str] = None


class GamificationEngine:
    """Manages achievements, badges, and progress."""

    LEVEL_XP = 500

    def __init__(self, storage_dir: Path = DEFAULT_GAMIFICATION_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.achievements: Dict[str, Achievement] = {}
        self.badges: Dict[str, Badge] = {}
        self.progress: Dict[str, ProgressState] = {}
        self._state_file = self.storage_dir / 'gamification.json'
        self._load_state()

    # ------------------------------------------------------------------
    # Content registration
    # ------------------------------------------------------------------
    def register_achievement(self, achievement: Achievement) -> None:
        self.achievements[achievement.achievement_id] = achievement
        self._persist_state()

    def register_badge(self, badge: Badge) -> None:
        self.badges[badge.badge_id] = badge
        self._persist_state()

    # ------------------------------------------------------------------
    # Progress updates
    # ------------------------------------------------------------------
    def add_experience(self, player_id: str, amount: int) -> ProgressState:
        state = self.progress.setdefault(player_id, ProgressState(player_id=player_id))
        state.experience += amount
        new_level = max(state.level, state.experience // self.LEVEL_XP + 1)
        if new_level > state.level:
            state.level = new_level
        self._persist_state()
        return state

    def record_activity(self, player_id: str, activity_metrics: Dict[str, int]) -> ProgressState:
        state = self.progress.setdefault(player_id, ProgressState(player_id=player_id))
        today = time.strftime("%Y-%m-%d", time.localtime())
        if state.last_active_day == today:
            streak_increment = 0
        elif state.last_active_day:
            streak_increment = 1
        else:
            streak_increment = 1
        state.streak_days = state.streak_days + streak_increment if streak_increment else state.streak_days
        state.last_active_day = today

        for achievement in self.achievements.values():
            if achievement.achievement_id in state.achievements_unlocked:
                continue
            if all(activity_metrics.get(metric, 0) >= threshold for metric, threshold in achievement.condition.items()):
                state.achievements_unlocked.append(achievement.achievement_id)
                self.add_experience(player_id, achievement.points)
        self._persist_state()
        return state

    def award_badge(self, player_id: str, badge_id: str) -> None:
        if badge_id not in self.badges:
            raise KeyError(f"Unknown badge: {badge_id}")
        state = self.progress.setdefault(player_id, ProgressState(player_id=player_id))
        if badge_id not in state.badges_earned:
            state.badges_earned.append(badge_id)
            self._persist_state()

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def progress_snapshot(self, player_id: str) -> Optional[ProgressState]:
        return self.progress.get(player_id)

    def leaderboard(self, top_n: int = 10) -> List[ProgressState]:
        return sorted(self.progress.values(), key=lambda state: state.experience, reverse=True)[:top_n]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def export_state(self, filename: str = "gamification.json") -> Path:
        path = self.storage_dir / filename
        payload = {
            "achievements": [achievement.__dict__ for achievement in self.achievements.values()],
            "badges": [badge.__dict__ for badge in self.badges.values()],
            "progress": [state.__dict__ for state in self.progress.values()],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        if not self._state_file.exists():
            return
        try:
            data = json.loads(self._state_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return
        for achievement in data.get('achievements', []):
            self.achievements[achievement['achievement_id']] = Achievement(**achievement)
        for badge in data.get('badges', []):
            self.badges[badge['badge_id']] = Badge(**badge)
        for state in data.get('progress', []):
            self.progress[state['player_id']] = ProgressState(**state)

    def _persist_state(self) -> None:
        payload = {
            'achievements': [achievement.__dict__ for achievement in self.achievements.values()],
            'badges': [badge.__dict__ for badge in self.badges.values()],
            'progress': [state.__dict__ for state in self.progress.values()],
        }
        tmp = self._state_file.with_suffix('.tmp')
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
        tmp.replace(self._state_file)


__all__ = [
    "Achievement",
    "Badge",
    "GamificationEngine",
    "ProgressState",
]
