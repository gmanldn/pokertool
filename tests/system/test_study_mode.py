"""Tests for study mode flashcards, quizzes, and lessons."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.study_mode import (
    Flashcard,
    Lesson,
    QuizQuestion,
    StudyModeManager,
)


def create_manager(tmp_path: Path) -> StudyModeManager:
    storage = tmp_path / "study"
    return StudyModeManager(storage_dir=storage)


def test_flashcard_spaced_repetition_flow(tmp_path):
    manager = create_manager(tmp_path)
    cards = [
        Flashcard(card_id="preflop_ranges", prompt="What is UTG opening % at 100bb?", answer="~14%"),
        Flashcard(card_id="cbet_spots", prompt="When to c-bet low boards?", answer="High freq"),
    ]
    manager.upsert_flashcards(cards)

    due_cards = manager.get_due_flashcards()
    assert {card.card_id for card in due_cards} == {"preflop_ranges", "cbet_spots"}

    reviewed = manager.review_flashcard("preflop_ranges", quality=5)
    assert reviewed is not None
    assert reviewed.repetitions == 1
    assert reviewed.ease_factor >= 2.5
    assert reviewed.interval_days >= 1.0
    assert reviewed.due_ts > time.time()

    # Low quality response should reset repetitions and shorten interval.
    reviewed = manager.review_flashcard("preflop_ranges", quality=2)
    assert reviewed.repetitions == 0
    assert reviewed.interval_days <= 1.0


def test_quiz_session_scoring_and_persistence(tmp_path):
    manager = create_manager(tmp_path)
    question_bank = [
        QuizQuestion(
            question_id="q1",
            prompt="What is pot odds to call half-pot bet?",
            choices=["2:1", "3:1", "1:1", "4:1"],
            correct_index=0,
        ),
        QuizQuestion(
            question_id="q2",
            prompt="Best bluffing candidate?",
            choices=["No equity", "Backdoor draws", "Pure value", "Nut hand"],
            correct_index=1,
        ),
        QuizQuestion(
            question_id="q3",
            prompt="Which street has most leverage?",
            choices=["Turn", "Flop", "River", "Preflop"],
            correct_index=2,
        ),
    ]

    session = manager.start_quiz("fundamentals", question_bank)
    session.answer("q1", 0)
    session.answer("q2", 1)
    session.answer("q3", 3)
    result = manager.finalize_quiz(session)

    assert result.total_questions == 3
    assert result.correct == 2
    assert result.score == 66.67

    # Reload manager to confirm persistence saved quiz history.
    reloaded = create_manager(tmp_path)
    snapshot = reloaded.get_progress_snapshot()
    assert snapshot.quizzes_taken == 1
    assert snapshot.average_quiz_score == 66.67
    assert snapshot.streak_days >= 1


def test_lesson_tracking_updates_progress(tmp_path):
    manager = create_manager(tmp_path)
    lessons = [
        Lesson(
            lesson_id="combo_math",
            title="Combinatorics Essentials",
            content="Counting combos for suited, offsuit, and pairs.",
            topics=["math", "range analysis"],
            estimated_minutes=8,
        ),
        Lesson(
            lesson_id="solver_basics",
            title="Solver Review",
            content="Interpreting solver outputs for river spots.",
            topics=["solver"],
            estimated_minutes=12,
        ),
    ]
    manager.add_lessons(lessons)

    pending = manager.get_lessons(include_completed=False)
    assert len(pending) == 2

    completed = manager.complete_lesson("combo_math")
    assert completed and completed.completed is True

    snapshot = manager.get_progress_snapshot()
    assert snapshot.lessons_completed == 1
    assert snapshot.total_lessons == 2
    assert snapshot.total_flashcards == 0
