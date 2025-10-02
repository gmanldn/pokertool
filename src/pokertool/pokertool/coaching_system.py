"""Adaptive coaching system providing real-time poker guidance."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import HandAnalysisResult, analyse_hand, Card, Position, parse_card

try:
    from pokertool.modules.poker_screen_scraper import TableState
except ImportError:  # pragma: no cover - optional dependency during tests
    TableState = Any  # type: ignore

COACHING_DIR = Path.home() / ".pokertool" / "coaching"
COACHING_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = COACHING_DIR / "progress.json"


@dataclass
class DetectedMistake:
    """Represents a detected mistake for a particular hand."""

    category: str
    severity: str
    description: str
    recommended_action: str
    equity_impact: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class RealTimeAdvice:
    """Structured real-time coaching hint."""

    summary: str
    reasoning: str
    recommended_action: str
    confidence: float


@dataclass
class TrainingScenario:
    """Guided training spot the player can review."""

    scenario_id: str
    description: str
    stage: str
    hero_cards: List[str]
    board_cards: List[str]
    stack_depth: str
    pot: float
    to_call: float
    recommended_action: str
    difficulty: str
    focus: str
    tags: List[str]
    completed: bool = False


@dataclass
class CoachingProgress:
    """Aggregated progress snapshot used for UI summaries."""

    hands_reviewed: int
    mistakes_by_category: Dict[str, int]
    scenarios_completed: int
    streak_days: int
    last_tip: Optional[str]
    accuracy_score: float


@dataclass
class CoachingFeedback:
    """Full coaching payload after evaluating a hand."""

    mistakes: List[DetectedMistake]
    real_time_advice: Optional[RealTimeAdvice]
    personalized_tips: List[str]


class CoachingSystem:
    """High-level coordinator for poker coaching insights."""

    _DEFAULT_PROGRESS = {
        "hands_reviewed": 0,
        "mistakes_by_category": {},
        "scenarios_completed": [],
        "recent_mistakes": [],
        "last_session_date": None,
        "streak_days": 0,
        "tips": [],
        "accuracy_history": [],
    }

    def __init__(self, storage_file: Path = PROGRESS_FILE):
        self.storage_file = storage_file
        self.progress: Dict[str, Any] = {}
        self._load_progress()
        self._scenarios = self._build_default_scenarios()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_progress(self) -> None:
        if self.storage_file.exists():
            try:
                self.progress = json.loads(self.storage_file.read_text())
            except json.JSONDecodeError:
                self.progress = json.loads(json.dumps(self._DEFAULT_PROGRESS))
        else:
            self.progress = json.loads(json.dumps(self._DEFAULT_PROGRESS))
        # Ensure mandatory keys exist
        for key, default_value in self._DEFAULT_PROGRESS.items():
            if isinstance(default_value, list):
                self.progress.setdefault(key, list(default_value))
            elif isinstance(default_value, dict):
                self.progress.setdefault(key, dict(default_value))
            else:
                self.progress.setdefault(key, default_value)

    def _save_progress(self) -> None:
        tmp_path = self.storage_file.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(self.progress, indent=2))
        tmp_path.replace(self.storage_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def evaluate_hand(
        self,
        hand_result: Optional[HandAnalysisResult],
        player_action: str,
        pot: Optional[float] = None,
        to_call: Optional[float] = None,
        position: Optional[Position] = None,
        table_stage: Optional[str] = None
    ) -> CoachingFeedback:
        """Evaluate a completed hand decision and return coaching feedback."""
        self._update_daily_streak()
        self.progress["hands_reviewed"] = int(self.progress.get("hands_reviewed", 0)) + 1

        mistakes = self._detect_mistakes(hand_result, player_action, pot, to_call, position, table_stage)
        advice = self._build_real_time_advice_from_result(hand_result, table_stage, to_call)
        tips = self._generate_personalized_tips(mistakes)

        feedback = CoachingFeedback(mistakes=mistakes, real_time_advice=advice, personalized_tips=tips)
        self._update_progress_with_feedback(feedback)
        self._save_progress()
        return feedback

    def get_real_time_advice(self, table_state: TableState) -> Optional[RealTimeAdvice]:
        """Generate live coaching advice from the current table state."""
        try:
            hero_cards = self._normalize_cards(table_state.hero_cards)
            board_cards = self._normalize_cards(table_state.board_cards)
            position = getattr(table_state, "hero_position", None)
            position_enum = None
            if isinstance(position, Position):
                position_enum = position
            elif isinstance(position, str):
                try:
                    position_enum = Position[position]
                except KeyError:
                    try:
                        position_enum = Position(position)
                    except ValueError:
                        position_enum = None

            hand_result = None
            if hero_cards:
                hand_result = analyse_hand(hero_cards, board_cards, position_enum, table_state.pot_size, table_state.current_bet)
            return self._build_real_time_advice_from_result(
                hand_result,
                getattr(table_state, "stage", None),
                getattr(table_state, "current_bet", None)
            )
        except Exception:
            return None

    def get_training_scenarios(self) -> List[TrainingScenario]:
        """Return all training scenarios with completion state."""
        completed = set(self.progress.get("scenarios_completed", []))
        scenarios = []
        for scenario in self._scenarios:
            scenario.completed = scenario.scenario_id in completed
            scenarios.append(scenario)
        return scenarios

    def mark_scenario_completed(self, scenario_id: str) -> None:
        completed = set(self.progress.get("scenarios_completed", []))
        completed.add(scenario_id)
        self.progress["scenarios_completed"] = sorted(completed)
        self._save_progress()

    def get_progress_snapshot(self) -> CoachingProgress:
        """Return aggregate progress information for display."""
        mistakes = self.progress.get("mistakes_by_category", {})
        completed = self.progress.get("scenarios_completed", [])
        accuracy = self._calculate_accuracy_score(mistakes)
        tips = self.progress.get("tips", [])
        last_tip = tips[-1] if tips else None
        return CoachingProgress(
            hands_reviewed=int(self.progress.get("hands_reviewed", 0)),
            mistakes_by_category=dict(mistakes),
            scenarios_completed=len(completed),
            streak_days=int(self.progress.get("streak_days", 0)),
            last_tip=last_tip,
            accuracy_score=accuracy,
        )

    def get_personalized_tips(self) -> List[str]:
        """Return cumulative personalized tips based on progress."""
        mistakes = self.progress.get("mistakes_by_category", {})
        return self._build_tip_library(mistakes)

    # ------------------------------------------------------------------
    # Mistake detection & advice generation
    # ------------------------------------------------------------------
    def _detect_mistakes(
        self,
        hand_result: Optional[HandAnalysisResult],
        player_action: str,
        pot: Optional[float],
        to_call: Optional[float],
        position: Optional[Position],
        table_stage: Optional[str]
    ) -> List[DetectedMistake]:
        if not hand_result:
            return []

        mistakes: List[DetectedMistake] = []
        action = (player_action or "").strip().lower()
        recommended = (hand_result.advice or "").strip().lower() or "fold"
        strength = float(hand_result.strength)

        pot = float(pot or 0.0)
        to_call = float(to_call or 0.0)
        pot_odds = (to_call / (pot + to_call)) if (pot + to_call) > 0 else None

        def add_mistake(category: str, severity: str, description: str, equity: float, fallback_action: str) -> None:
            mistakes.append(
                DetectedMistake(
                    category=category,
                    severity=severity,
                    description=description,
                    recommended_action=recommended if recommended else fallback_action,
                    equity_impact=round(equity, 3),
                )
            )

        # Missed value: strong hand but passive choice
        if strength >= 0.75 and action in {"fold", "check"}:
            add_mistake(
                "missed_value",
                "major",
                "Strong made hand played passively. Consider betting or raising for value.",
                equity=0.45,
                fallback_action="raise",
            )

        # Over aggressive with mediocre strength
        if strength <= 0.35 and action in {"raise", "bet", "all-in"}:
            add_mistake(
                "over_aggression",
                "major",
                "Weak holding escalated the pot. Tighten range in this spot.",
                equity=0.4,
                fallback_action="fold",
            )

        # Failure to defend with good pot odds
        if pot_odds is not None and pot_odds <= 0.22 and action == "fold" and strength >= 0.45:
            add_mistake(
                "pot_odds",
                "moderate",
                "Profitably defend against the bet size given the equity requirement.",
                equity=0.25,
                fallback_action="call",
            )

        # Deviating from solver recommendation when confidence high
        if recommended and action and action != recommended:
            severity = "moderate" if strength >= 0.55 else "minor"
            add_mistake(
                "deviation",
                severity,
                f"Action '{action}' deviates from recommended '{recommended}'.",
                equity=0.2 if severity == "moderate" else 0.1,
                fallback_action=recommended,
            )

        # Positional leak heuristics
        if position is not None and action in {"call", "limp"} and position.category() == "Early" and strength < 0.55:
            add_mistake(
                "positional_leak",
                "minor",
                "Calling from early position with marginal strength is risky.",
                equity=0.12,
                fallback_action="fold",
            )

        if table_stage and table_stage.lower() == "river" and strength >= 0.65 and action == "check":
            add_mistake(
                "thin_value",
                "minor",
                "River check misses thin value opportunity against capped ranges.",
                equity=0.15,
                fallback_action="bet",
            )

        return mistakes

    def _build_real_time_advice_from_result(
        self,
        hand_result: Optional[HandAnalysisResult],
        stage: Optional[str],
        to_call: Optional[float]
    ) -> Optional[RealTimeAdvice]:
        if not hand_result:
            return None
        stage_label = (stage or "Unknown").capitalize()
        recommended = (hand_result.advice or "fold").lower()
        confidence = min(max(hand_result.strength, 0.0), 1.0)
        odds_text = ""
        if to_call:
            odds_text = f" Facing a bet of ${to_call:.2f}."
        summary = f"{stage_label}: Recommended action is {recommended.upper()} with confidence {confidence:.0%}."
        reasoning = hand_result.details.get("reason", "Blend of range strength and pot odds.") if hand_result.details else "Range advantage detected."
        return RealTimeAdvice(
            summary=summary,
            reasoning=reasoning + odds_text,
            recommended_action=recommended,
            confidence=confidence,
        )

    def _generate_personalized_tips(self, mistakes: List[DetectedMistake]) -> List[str]:
        if not mistakes:
            return ["Solid decision making! Keep reviewing your strongest hands to lock in good habits."]

        tips = []
        categories = {mistake.category for mistake in mistakes}
        if "missed_value" in categories:
            tips.append("Look for chances to extract thin value when holding 70%+ equity hands.")
        if "over_aggression" in categories:
            tips.append("Balance aggression by favoring folds with sub-35% equity hands preflop.")
        if "pot_odds" in categories:
            tips.append("Calculate pot odds quickly: defend more when the required equity is under 25%.")
        if "positional_leak" in categories:
            tips.append("Tighten early-position calling range; prefer suited broadways and high pairs.")
        if "thin_value" in categories:
            tips.append("On rivers, bet small with medium-strength hands versus missed draws.")
        if "deviation" in categories:
            tips.append("Review solver outputs for similar spots to build intuition for recommended lines.")
        return tips

    def _update_progress_with_feedback(self, feedback: CoachingFeedback) -> None:
        mistakes_log = self.progress.setdefault("recent_mistakes", [])
        for mistake in feedback.mistakes:
            entry = {
                "timestamp": mistake.timestamp,
                "category": mistake.category,
                "severity": mistake.severity,
                "equity": mistake.equity_impact,
                "recommended": mistake.recommended_action,
            }
            mistakes_log.append(entry)
            mistakes_log[:] = mistakes_log[-50:]
            counts = self.progress.setdefault("mistakes_by_category", {})
            counts[mistake.category] = counts.get(mistake.category, 0) + 1

        if feedback.personalized_tips:
            tips = self.progress.setdefault("tips", [])
            tips.extend(tip for tip in feedback.personalized_tips if tip not in tips)

        accuracy_history = self.progress.setdefault("accuracy_history", [])
        accuracy_score = 1.0 - min(sum(m.equity_impact for m in feedback.mistakes), 1.0)
        accuracy_history.append(accuracy_score)
        accuracy_history[:] = accuracy_history[-100:]

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _calculate_accuracy_score(self, mistakes: Dict[str, int]) -> float:
        total_mistakes = sum(mistakes.values())
        if total_mistakes == 0:
            history = self.progress.get("accuracy_history", [])
            return statistics.mean(history) if history else 1.0
        return max(0.0, 1.0 - (total_mistakes / max(self.progress.get("hands_reviewed", 1), 1)))

    def _normalize_cards(self, cards: Optional[List[Any]]) -> List[Card]:
        normalized: List[Card] = []
        if not cards:
            return normalized
        for card in cards:
            if isinstance(card, Card):
                normalized.append(card)
            elif isinstance(card, str):
                try:
                    normalized.append(parse_card(card))
                except ValueError:
                    continue
        return normalized

    def _update_daily_streak(self) -> None:
        today = time.strftime("%Y-%m-%d")
        last_date = self.progress.get("last_session_date")
        if last_date == today:
            return
        if last_date is not None:
            last_time = time.strptime(last_date, "%Y-%m-%d")
            yesterday = time.localtime(time.time() - 86400)
            if last_time.tm_year == yesterday.tm_year and last_time.tm_yday == yesterday.tm_yday:
                self.progress["streak_days"] = int(self.progress.get("streak_days", 0)) + 1
            else:
                self.progress["streak_days"] = 1
        else:
            self.progress["streak_days"] = 1
        self.progress["last_session_date"] = today

    def _build_default_scenarios(self) -> List[TrainingScenario]:
        scenarios = [
            TrainingScenario(
                scenario_id="COACH-S1",
                description="BTN open facing 3-bet from SB with suited connectors.",
                stage="preflop",
                hero_cards=["Jc", "Tc"],
                board_cards=[],
                stack_depth="100bb",
                pot=2.5,
                to_call=7.5,
                recommended_action="call",
                difficulty="Intermediate",
                focus="3-bet defense",
                tags=["preflop", "defense", "position"],
            ),
            TrainingScenario(
                scenario_id="COACH-S2",
                description="Flop c-bet decision on A♠7♦2♣ after raising preflop.",
                stage="flop",
                hero_cards=["Ah", "Kd"],
                board_cards=["As", "7d", "2c"],
                stack_depth="90bb",
                pot=9.0,
                to_call=0.0,
                recommended_action="bet",
                difficulty="Beginner",
                focus="value_betting",
                tags=["flop", "cbet", "value"],
            ),
            TrainingScenario(
                scenario_id="COACH-S3",
                description="River bluff spot after missed flush draw heads-up.",
                stage="river",
                hero_cards=["Qh", "Jh"],
                board_cards=["9h", "Th", "2s", "2d", "5c"],
                stack_depth="60bb",
                pot=25.0,
                to_call=0.0,
                recommended_action="bet",
                difficulty="Advanced",
                focus="bluffing",
                tags=["river", "bluff", "polarized"],
            ),
        ]
        return scenarios

    def _build_tip_library(self, mistakes: Dict[str, int]) -> List[str]:
        tips: List[str] = []
        if mistakes.get("missed_value", 0) >= 3:
            tips.append("Consider reviewing value betting charts for top pair and better.")
        if mistakes.get("over_aggression", 0) >= 3:
            tips.append("Dial back semi-bluffs when equity is under 35%.")
        if mistakes.get("pot_odds", 0) >= 2:
            tips.append("Memorize quick pot-odds tables for common bet sizes (25%, 33%, 50%, 66%).")
        if mistakes.get("positional_leak", 0) >= 2:
            tips.append("Open tighter ranges from early seats; shift marginal hands to late position.")
        if mistakes.get("thin_value", 0) >= 2:
            tips.append("Review thin value betting modules focusing on paired boards.")
        if mistakes.get("deviation", 0) >= 4:
            tips.append("Tag hands where you deviated for later solver study sessions.")
        if not tips:
            tips.append("Great job! Expand the sample size to confirm your current strategy's robustness.")
        return tips


__all__ = [
    "CoachingSystem",
    "CoachingFeedback",
    "CoachingProgress",
    "TrainingScenario",
    "RealTimeAdvice",
    "DetectedMistake",
]
