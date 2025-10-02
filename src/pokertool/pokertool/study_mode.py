"""Study mode utilities: quizzes, flashcards, and progress tracking."""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

DEFAULT_STUDY_DIR = Path.home() / ".pokertool" / "study"
DEFAULT_STUDY_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


def _now() -> float:
    return time.time()


@dataclass
class Flashcard:
    """Simple spaced-repetition flashcard."""

    card_id: str
    prompt: str
    answer: str
    tags: List[str] = field(default_factory=list)
    difficulty: int = 2
    ease_factor: float = 2.5
    interval_days: float = 0.0
    repetitions: int = 0
    last_reviewed_ts: float = 0.0
    due_ts: float = field(default_factory=_now)

    def mark_scheduled(self, interval_days: float, ease_factor: float, repetitions: int) -> None:
        self.interval_days = interval_days
        self.ease_factor = ease_factor
        self.repetitions = repetitions
        self.last_reviewed_ts = _now()
        self.due_ts = self.last_reviewed_ts + interval_days * 86400


@dataclass
class QuizQuestion:
    """Multiple choice quiz question."""

    question_id: str
    prompt: str
    choices: List[str]
    correct_index: int
    explanation: Optional[str] = None
    difficulty: str = "medium"

    def is_correct(self, answer_index: int) -> bool:
        return answer_index == self.correct_index


@dataclass
class QuizResult:
    """Result payload returned after grading a quiz."""

    quiz_id: str
    total_questions: int
    correct: int
    incorrect: int
    score: float
    responses: Dict[str, int]
    timestamp: float = field(default_factory=_now)


@dataclass
class Lesson:
    """Structured study lesson."""

    lesson_id: str
    title: str
    content: str
    topics: List[str]
    estimated_minutes: int
    resources: List[str] = field(default_factory=list)
    completed: bool = False
    last_completed_ts: Optional[float] = None


@dataclass
class StudyProgress:
    """Aggregated snapshot for UI dashboards."""

    total_flashcards: int
    due_flashcards: int
    quizzes_taken: int
    average_quiz_score: float
    lessons_completed: int
    total_lessons: int
    streak_days: int


class StudyPersistence:
    """JSON persistence for study assets."""

    def __init__(self, storage_dir: Path = DEFAULT_STUDY_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "progress.json"

    def load(self) -> Dict[str, object]:
        if not self.storage_file.exists():
            return {
                "flashcards": {},
                "lessons": {},
                "quizzes": [],
                "streak": {
                    "last_session_day": None,
                    "days": 0,
                },
            }
        try:
            return json.loads(self.storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "flashcards": {},
                "lessons": {},
                "quizzes": [],
                "streak": {
                    "last_session_day": None,
                    "days": 0,
                },
            }

    def save(self, payload: Dict[str, object]) -> None:
        tmp_path = self.storage_file.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(self.storage_file)


class SpacedRepetitionScheduler:
    """Implements an SM-2 inspired spaced-repetition algorithm."""

    MIN_EASE = 1.3
    DEFAULT_EASE = 2.5
    INITIAL_INTERVALS = (1.0, 6.0)

    def schedule(self, card: Flashcard, quality: int) -> None:
        quality = max(0, min(5, quality))
        ease = card.ease_factor or self.DEFAULT_EASE
        repetitions = card.repetitions

        if quality < 3:
            repetitions = 0
            interval = 1.0 if quality == 2 else 0.5
        else:
            if repetitions == 0:
                interval = self.INITIAL_INTERVALS[0]
            elif repetitions == 1:
                interval = self.INITIAL_INTERVALS[1]
            else:
                interval = card.interval_days * ease
            repetitions += 1
            ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            ease = max(self.MIN_EASE, ease)

        card.mark_scheduled(interval, ease, repetitions)


class QuizSession:
    """Represents an in-progress quiz."""

    def __init__(self, quiz_id: str, questions: Sequence[QuizQuestion]):
        self.quiz_id = quiz_id
        self.questions = list(questions)
        self.responses: Dict[str, int] = {}

    def answer(self, question_id: str, choice_index: int) -> None:
        self.responses[question_id] = choice_index

    def grade(self) -> QuizResult:
        correct = 0
        for question in self.questions:
            answer = self.responses.get(question.question_id, -1)
            if question.is_correct(answer):
                correct += 1
        incorrect = max(0, len(self.questions) - correct)
        score = (correct / len(self.questions)) * 100 if self.questions else 0.0
        return QuizResult(
            quiz_id=self.quiz_id,
            total_questions=len(self.questions),
            correct=correct,
            incorrect=incorrect,
            score=round(score, 2),
            responses=dict(self.responses),
        )


class StudyModeManager:
    """High-level API for study mode features."""

    def __init__(self, storage_dir: Path = DEFAULT_STUDY_DIR):
        self._storage = StudyPersistence(storage_dir)
        state = self._storage.load()
        self._flashcards: Dict[str, Flashcard] = {
            card_id: Flashcard(**data)
            for card_id, data in state.get("flashcards", {}).items()
        }
        self._lessons: Dict[str, Lesson] = {
            lesson_id: Lesson(**data)
            for lesson_id, data in state.get("lessons", {}).items()
        }
        self._quiz_history: List[QuizResult] = [
            QuizResult(**result)
            for result in state.get("quizzes", [])
        ]
        self._streak = state.get("streak", {"last_session_day": None, "days": 0})
        self._scheduler = SpacedRepetitionScheduler()

    # ------------------------------------------------------------------
    # Flashcards
    # ------------------------------------------------------------------
    def upsert_flashcards(self, cards: Iterable[Flashcard]) -> None:
        for card in cards:
            if card.card_id not in self._flashcards:
                card.ease_factor = card.ease_factor or SpacedRepetitionScheduler.DEFAULT_EASE
                card.due_ts = min(card.due_ts, _now()) if card.due_ts else _now()
            self._flashcards[card.card_id] = card
        self._persist()

    def get_due_flashcards(self, limit: int = 10) -> List[Flashcard]:
        due = [card for card in self._flashcards.values() if card.due_ts <= _now()]
        due.sort(key=lambda c: c.due_ts)
        return due[:limit]

    def review_flashcard(self, card_id: str, quality: int) -> Optional[Flashcard]:
        card = self._flashcards.get(card_id)
        if not card:
            return None
        self._scheduler.schedule(card, quality)
        self._update_streak()
        self._persist()
        return card

    # ------------------------------------------------------------------
    # Quizzes
    # ------------------------------------------------------------------
    def start_quiz(self, quiz_id: str, questions: Sequence[QuizQuestion]) -> QuizSession:
        return QuizSession(quiz_id, questions)

    def finalize_quiz(self, session: QuizSession) -> QuizResult:
        result = session.grade()
        self._quiz_history.append(result)
        self._update_streak()
        self._persist()
        return result

    # ------------------------------------------------------------------
    # Lessons
    # ------------------------------------------------------------------
    def add_lessons(self, lessons: Iterable[Lesson]) -> None:
        for lesson in lessons:
            self._lessons[lesson.lesson_id] = lesson
        self._persist()

    def complete_lesson(self, lesson_id: str) -> Optional[Lesson]:
        lesson = self._lessons.get(lesson_id)
        if not lesson:
            return None
        lesson.completed = True
        lesson.last_completed_ts = _now()
        self._update_streak()
        self._persist()
        return lesson

    def get_lessons(self, include_completed: bool = True) -> List[Lesson]:
        lessons = list(self._lessons.values())
        if not include_completed:
            lessons = [lesson for lesson in lessons if not lesson.completed]
        lessons.sort(key=lambda l: (l.completed, l.estimated_minutes))
        return lessons

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def get_progress_snapshot(self) -> StudyProgress:
        total_cards = len(self._flashcards)
        due_cards = len(self.get_due_flashcards(limit=total_cards or 1))
        total_lessons = len(self._lessons)
        lessons_completed = sum(1 for lesson in self._lessons.values() if lesson.completed)
        quizzes_taken = len(self._quiz_history)
        average_score = (
            sum(result.score for result in self._quiz_history) / quizzes_taken
            if quizzes_taken else 0.0
        )
        return StudyProgress(
            total_flashcards=total_cards,
            due_flashcards=due_cards,
            quizzes_taken=quizzes_taken,
            average_quiz_score=round(average_score, 2),
            lessons_completed=lessons_completed,
            total_lessons=total_lessons,
            streak_days=int(self._streak.get("days", 0)),
        )

    def export_state(self) -> Dict[str, object]:
        return {
            "flashcards": {card_id: self._asdict(card) for card_id, card in self._flashcards.items()},
            "lessons": {lesson_id: self._asdict(lesson) for lesson_id, lesson in self._lessons.items()},
            "quizzes": [self._asdict(result) for result in self._quiz_history],
            "streak": dict(self._streak),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _persist(self) -> None:
        payload = self.export_state()
        self._storage.save(payload)

    def _update_streak(self) -> None:
        today = time.strftime("%Y-%m-%d", time.localtime())
        last_day = self._streak.get("last_session_day")
        if last_day == today:
            return
        if last_day:
            # Increase streak if previous day was yesterday; otherwise reset.
            last_ts = time.mktime(time.strptime(last_day, "%Y-%m-%d"))
            delta_days = int((_now() - last_ts) // 86400)
            if delta_days == 1:
                self._streak["days"] = int(self._streak.get("days", 0)) + 1
            elif delta_days > 1:
                self._streak["days"] = 1
        else:
            self._streak["days"] = 1
        self._streak["last_session_day"] = today

    @staticmethod
    def _asdict(obj) -> Dict[str, object]:
        if isinstance(obj, Flashcard):
            return {
                "card_id": obj.card_id,
                "prompt": obj.prompt,
                "answer": obj.answer,
                "tags": obj.tags,
                "difficulty": obj.difficulty,
                "ease_factor": obj.ease_factor,
                "interval_days": obj.interval_days,
                "repetitions": obj.repetitions,
                "last_reviewed_ts": obj.last_reviewed_ts,
                "due_ts": obj.due_ts,
            }
        if isinstance(obj, Lesson):
            return {
                "lesson_id": obj.lesson_id,
                "title": obj.title,
                "content": obj.content,
                "topics": obj.topics,
                "estimated_minutes": obj.estimated_minutes,
                "resources": obj.resources,
                "completed": obj.completed,
                "last_completed_ts": obj.last_completed_ts,
            }
        if isinstance(obj, QuizResult):
            return {
                "quiz_id": obj.quiz_id,
                "total_questions": obj.total_questions,
                "correct": obj.correct,
                "incorrect": obj.incorrect,
                "score": obj.score,
                "responses": obj.responses,
                "timestamp": obj.timestamp,
            }
        raise TypeError(f"Unsupported object type for serialization: {type(obj)!r}")


__all__ = [
    "Flashcard",
    "QuizQuestion",
    "QuizResult",
    "Lesson",
    "StudyProgress",
    "StudyModeManager",
    "SpacedRepetitionScheduler",
    "QuizSession",
]
