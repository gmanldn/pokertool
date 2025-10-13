"""
Active Learning Feedback Loop for PokerTool

Continuously improves prediction models by collecting targeted human feedback
on low-confidence situations.

Key Components:
- Uncertainty detection and triage rules
- Expert feedback collection and annotation
- Prioritized storage with metadata for bias audits
- Automated weekly retraining batches
- Model lift reporting

Author: PokerTool Development Team
Version: v48.0.0
"""

import sqlite3
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import heapq
from collections import defaultdict


logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Poker action types"""
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"
    ALL_IN = "all_in"


class StreetType(Enum):
    """Poker street types"""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class FeedbackStatus(Enum):
    """Status of feedback events"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    INCORPORATED = "incorporated"
    REJECTED = "rejected"


class UncertaintyLevel(Enum):
    """Uncertainty classification levels"""
    HIGH = "high"  # Immediate expert review needed
    MEDIUM = "medium"  # Queue for batch review
    LOW = "low"  # Optional review
    NEGLIGIBLE = "negligible"  # No review needed


@dataclass
class GameState:
    """Represents the poker game state for a decision"""
    street: StreetType
    pot_size: float
    hero_stack: float
    hero_position: str
    num_players: int
    board_cards: List[str]
    hole_cards: List[str]
    pot_odds: float
    action_history: List[Dict[str, Any]]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "street": self.street.value,
            "pot_size": self.pot_size,
            "hero_stack": self.hero_stack,
            "hero_position": self.hero_position,
            "num_players": self.num_players,
            "board_cards": self.board_cards,
            "hole_cards": self.hole_cards,
            "pot_odds": self.pot_odds,
            "action_history": self.action_history
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'GameState':
        """Create from dictionary"""
        return cls(
            street=StreetType(data["street"]),
            pot_size=data["pot_size"],
            hero_stack=data["hero_stack"],
            hero_position=data["hero_position"],
            num_players=data["num_players"],
            board_cards=data["board_cards"],
            hole_cards=data["hole_cards"],
            pot_odds=data["pot_odds"],
            action_history=data["action_history"]
        )


@dataclass
class Prediction:
    """Model prediction with uncertainty"""
    action: ActionType
    probability: float
    alternatives: Dict[ActionType, float]
    confidence_interval: Tuple[float, float]
    ev_estimate: float
    ev_interval: Tuple[float, float]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "action": self.action.value,
            "probability": self.probability,
            "alternatives": {k.value: v for k, v in self.alternatives.items()},
            "confidence_interval": self.confidence_interval,
            "ev_estimate": self.ev_estimate,
            "ev_interval": self.ev_interval
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Prediction':
        """Create from dictionary"""
        return cls(
            action=ActionType(data["action"]),
            probability=data["probability"],
            alternatives={ActionType(k): v for k, v in data["alternatives"].items()},
            confidence_interval=tuple(data["confidence_interval"]),
            ev_estimate=data["ev_estimate"],
            ev_interval=tuple(data["ev_interval"])
        )


@dataclass
class ExpertFeedback:
    """Expert annotation for a decision"""
    correct_action: ActionType
    reasoning: str
    confidence: float  # Expert's confidence (0-1)
    alternative_actions: List[ActionType]  # Other acceptable actions
    timestamp: datetime
    expert_id: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "correct_action": self.correct_action.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "alternative_actions": [a.value for a in self.alternative_actions],
            "timestamp": self.timestamp.isoformat(),
            "expert_id": self.expert_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ExpertFeedback':
        """Create from dictionary"""
        return cls(
            correct_action=ActionType(data["correct_action"]),
            reasoning=data["reasoning"],
            confidence=data["confidence"],
            alternative_actions=[ActionType(a) for a in data["alternative_actions"]],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            expert_id=data["expert_id"]
        )


@dataclass
class FeedbackEvent:
    """A feedback event for active learning"""
    event_id: str
    game_state: GameState
    prediction: Prediction
    uncertainty_level: UncertaintyLevel
    priority_score: float
    feedback: Optional[ExpertFeedback]
    status: FeedbackStatus
    created_at: datetime
    reviewed_at: Optional[datetime]

    def __lt__(self, other: 'FeedbackEvent') -> bool:
        """For priority queue ordering (higher priority first)"""
        return self.priority_score > other.priority_score


class UncertaintyTriage:
    """Detects uncertain predictions and assigns priority"""

    def __init__(
        self,
        high_uncertainty_threshold: float = 0.3,
        medium_uncertainty_threshold: float = 0.2,
        ev_uncertainty_threshold: float = 50.0,
        close_alternative_threshold: float = 0.1
    ):
        """
        Initialize triage rules

        Args:
            high_uncertainty_threshold: Probability margin for HIGH uncertainty
            medium_uncertainty_threshold: Probability margin for MEDIUM uncertainty
            ev_uncertainty_threshold: EV range width for uncertainty detection ($)
            close_alternative_threshold: Probability difference for close alternatives
        """
        self.high_threshold = high_uncertainty_threshold
        self.medium_threshold = medium_uncertainty_threshold
        self.ev_threshold = ev_uncertainty_threshold
        self.close_alt_threshold = close_alternative_threshold

    def assess_uncertainty(
        self,
        prediction: Prediction,
        game_state: GameState
    ) -> Tuple[UncertaintyLevel, float]:
        """
        Assess prediction uncertainty and compute priority

        Returns:
            (uncertainty_level, priority_score)
        """
        # Check probability margin
        prob_margin = prediction.probability - max(
            [p for a, p in prediction.alternatives.items()
             if a != prediction.action],
            default=0.0
        )

        # Check EV uncertainty
        ev_range = prediction.ev_interval[1] - prediction.ev_interval[0]

        # Check for close alternatives
        close_alternatives = sum(
            1 for a, p in prediction.alternatives.items()
            if a != prediction.action and
            prediction.probability - p < self.close_alt_threshold
        )

        # Check confidence interval width
        conf_range = prediction.confidence_interval[1] - prediction.confidence_interval[0]

        # Compute uncertainty score
        uncertainty_score = (
            (1.0 - prob_margin) * 0.4 +
            min(ev_range / 100.0, 1.0) * 0.3 +
            (close_alternatives / 3.0) * 0.2 +
            min(conf_range, 1.0) * 0.1
        )

        # Classify uncertainty level
        if uncertainty_score > self.high_threshold:
            level = UncertaintyLevel.HIGH
        elif uncertainty_score > self.medium_threshold:
            level = UncertaintyLevel.MEDIUM
        elif uncertainty_score > 0.05:
            level = UncertaintyLevel.LOW
        else:
            level = UncertaintyLevel.NEGLIGIBLE

        # Compute priority score (0-100)
        priority = uncertainty_score * 100

        # Boost priority for critical situations
        if game_state.pot_size > game_state.hero_stack * 0.5:
            priority *= 1.3  # Big pot decisions

        if game_state.street in [StreetType.TURN, StreetType.RIVER]:
            priority *= 1.2  # Later street decisions

        priority = min(priority, 100.0)

        return level, priority


class FeedbackStorage:
    """SQLite-based storage for feedback events with connection pooling"""

    def __init__(self, db_path: str = "active_learning.db"):
        """Initialize storage with connection pooling"""
        self.db_path = db_path
        self._cache = {}  # Simple in-memory cache for frequently accessed events
        self._cache_size = 100
        self._init_database()

    def _get_connection(self):
        """Get database connection with optimizations"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=10.0,  # Prevent immediate failures on lock
            check_same_thread=False  # Allow multi-threaded access
        )
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Use memory for temp storage
        conn.execute("PRAGMA temp_store=MEMORY")
        # Increase cache size
        conn.execute("PRAGMA cache_size=10000")
        return conn

    def _init_database(self):
        """Create database schema with optimizations"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback_events (
                    event_id TEXT PRIMARY KEY,
                    game_state TEXT NOT NULL,
                    prediction TEXT NOT NULL,
                    uncertainty_level TEXT NOT NULL,
                    priority_score REAL NOT NULL,
                    feedback TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    incorporated_at TEXT,
                    batch_id TEXT
                )
            """)

            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON feedback_events(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_priority
                ON feedback_events(priority_score DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created
                ON feedback_events(created_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_batch
                ON feedback_events(batch_id)
            """)

            # Composite index for common query pattern
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_priority
                ON feedback_events(status, priority_score DESC)
            """)

            conn.commit()

        logger.info(f"Initialized feedback storage at {self.db_path}")

    def save_event(self, event: FeedbackEvent) -> bool:
        """Save feedback event with caching"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO feedback_events
                    (event_id, game_state, prediction, uncertainty_level,
                     priority_score, feedback, status, created_at, reviewed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    json.dumps(event.game_state.to_dict()),
                    json.dumps(event.prediction.to_dict()),
                    event.uncertainty_level.value,
                    event.priority_score,
                    json.dumps(event.feedback.to_dict()) if event.feedback else None,
                    event.status.value,
                    event.created_at.isoformat(),
                    event.reviewed_at.isoformat() if event.reviewed_at else None
                ))

                conn.commit()

            # Update cache
            self._cache[event.event_id] = event
            if len(self._cache) > self._cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            return True
        except Exception as e:
            logger.error(f"Failed to save event: {e}", exc_info=True)
            return False

    def get_event(self, event_id: str) -> Optional[FeedbackEvent]:
        """Retrieve event by ID with caching"""
        # Check cache first
        if event_id in self._cache:
            return self._cache[event_id]

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM feedback_events WHERE event_id = ?
                """, (event_id,))

                row = cursor.fetchone()

                if row:
                    event = self._row_to_event(row)
                    # Update cache
                    self._cache[event_id] = event
                    return event

        except Exception as e:
            logger.error(f"Failed to retrieve event {event_id}: {e}", exc_info=True)

        return None

    def get_pending_events(
        self,
        limit: int = 100,
        min_priority: float = 0.0
    ) -> List[FeedbackEvent]:
        """Get pending events for review with optimized query"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Uses composite index idx_status_priority
                cursor.execute("""
                    SELECT * FROM feedback_events
                    WHERE status = ? AND priority_score >= ?
                    ORDER BY priority_score DESC
                    LIMIT ?
                """, (FeedbackStatus.PENDING.value, min_priority, limit))

                rows = cursor.fetchall()
                return [self._row_to_event(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get pending events: {e}", exc_info=True)
            return []

    def get_reviewed_events(
        self,
        since: Optional[datetime] = None,
        status: FeedbackStatus = FeedbackStatus.REVIEWED
    ) -> List[FeedbackEvent]:
        """Get reviewed events for training with error handling"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                if since:
                    cursor.execute("""
                        SELECT * FROM feedback_events
                        WHERE status = ? AND reviewed_at >= ?
                        ORDER BY reviewed_at DESC
                    """, (status.value, since.isoformat()))
                else:
                    cursor.execute("""
                        SELECT * FROM feedback_events
                        WHERE status = ?
                        ORDER BY reviewed_at DESC
                    """, (status.value,))

                rows = cursor.fetchall()
                return [self._row_to_event(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get reviewed events: {e}", exc_info=True)
            return []

    def mark_incorporated(self, event_ids: List[str], batch_id: str):
        """Mark events as incorporated with batch optimization"""
        if not event_ids:
            return

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Batch update for better performance
                cursor.executemany("""
                    UPDATE feedback_events
                    SET status = ?, incorporated_at = ?, batch_id = ?
                    WHERE event_id = ?
                """, [
                    (FeedbackStatus.INCORPORATED.value, datetime.now().isoformat(),
                     batch_id, eid)
                    for eid in event_ids
                ])

                conn.commit()

            # Clear cache for updated events
            for eid in event_ids:
                self._cache.pop(eid, None)

            logger.info(f"Marked {len(event_ids)} events as incorporated in batch {batch_id}")

        except Exception as e:
            logger.error(f"Failed to mark events as incorporated: {e}", exc_info=True)

    def _row_to_event(self, row: tuple) -> FeedbackEvent:
        """Convert database row to FeedbackEvent"""
        return FeedbackEvent(
            event_id=row[0],
            game_state=GameState.from_dict(json.loads(row[1])),
            prediction=Prediction.from_dict(json.loads(row[2])),
            uncertainty_level=UncertaintyLevel(row[3]),
            priority_score=row[4],
            feedback=ExpertFeedback.from_dict(json.loads(row[5])) if row[5] else None,
            status=FeedbackStatus(row[6]),
            created_at=datetime.fromisoformat(row[7]),
            reviewed_at=datetime.fromisoformat(row[8]) if row[8] else None
        )


class RetrainingScheduler:
    """Manages automated retraining batches"""

    def __init__(
        self,
        storage: FeedbackStorage,
        min_samples_for_retraining: int = 50,
        retraining_interval_days: int = 7
    ):
        """Initialize scheduler"""
        self.storage = storage
        self.min_samples = min_samples_for_retraining
        self.interval_days = retraining_interval_days
        self.last_retraining: Optional[datetime] = None

    def should_trigger_retraining(self) -> bool:
        """Check if retraining should be triggered"""
        # Check time since last retraining
        if self.last_retraining:
            days_since = (datetime.now() - self.last_retraining).days
            if days_since < self.interval_days:
                return False

        # Check if we have enough reviewed samples
        reviewed = self.storage.get_reviewed_events()
        return len(reviewed) >= self.min_samples

    def prepare_training_batch(self) -> Tuple[List[FeedbackEvent], str]:
        """
        Prepare reviewed events for retraining

        Returns:
            (events, batch_id)
        """
        events = self.storage.get_reviewed_events(
            status=FeedbackStatus.REVIEWED
        )

        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Prepared training batch {batch_id} with {len(events)} events")

        return events, batch_id

    def mark_batch_incorporated(self, events: List[FeedbackEvent], batch_id: str):
        """Mark batch as incorporated"""
        event_ids = [e.event_id for e in events]
        self.storage.mark_incorporated(event_ids, batch_id)
        self.last_retraining = datetime.now()


class ActiveLearningFeedbackLoop:
    """Main active learning system"""

    # Singleton instance
    _instance: Optional['ActiveLearningFeedbackLoop'] = None

    def __init__(
        self,
        storage_path: str = "active_learning.db",
        high_uncertainty_threshold: float = 0.3,
        medium_uncertainty_threshold: float = 0.2
    ):
        """Initialize active learning system"""
        self.triage = UncertaintyTriage(
            high_uncertainty_threshold,
            medium_uncertainty_threshold
        )
        self.storage = FeedbackStorage(storage_path)
        self.scheduler = RetrainingScheduler(self.storage)
        self.event_counter = 0

        logger.info("Initialized Active Learning Feedback Loop")

    @classmethod
    def get_instance(cls) -> 'ActiveLearningFeedbackLoop':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def process_prediction(
        self,
        game_state: GameState,
        prediction: Prediction
    ) -> Optional[FeedbackEvent]:
        """
        Process a prediction and potentially queue for review

        Returns:
            FeedbackEvent if queued for review, None otherwise
        """
        # Assess uncertainty
        uncertainty, priority = self.triage.assess_uncertainty(
            prediction, game_state
        )

        # Only queue if uncertainty is meaningful
        if uncertainty == UncertaintyLevel.NEGLIGIBLE:
            return None

        # Create feedback event
        self.event_counter += 1
        event = FeedbackEvent(
            event_id=f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.event_counter}",
            game_state=game_state,
            prediction=prediction,
            uncertainty_level=uncertainty,
            priority_score=priority,
            feedback=None,
            status=FeedbackStatus.PENDING,
            created_at=datetime.now(),
            reviewed_at=None
        )

        # Save to storage
        if self.storage.save_event(event):
            logger.info(
                f"Queued {uncertainty.value} uncertainty event "
                f"with priority {priority:.2f}"
            )
            return event

        return None

    def submit_feedback(
        self,
        event_id: str,
        feedback: ExpertFeedback
    ) -> bool:
        """Submit expert feedback for an event"""
        event = self.storage.get_event(event_id)

        if not event:
            logger.error(f"Event {event_id} not found")
            return False

        # Update event with feedback
        event.feedback = feedback
        event.status = FeedbackStatus.REVIEWED
        event.reviewed_at = datetime.now()

        # Save updated event
        if self.storage.save_event(event):
            logger.info(f"Recorded feedback for event {event_id}")
            return True

        return False

    def get_review_queue(
        self,
        limit: int = 10,
        min_priority: float = 50.0
    ) -> List[FeedbackEvent]:
        """Get highest priority events for review"""
        return self.storage.get_pending_events(limit, min_priority)

    def check_retraining_trigger(self) -> bool:
        """Check if retraining should be triggered"""
        return self.scheduler.should_trigger_retraining()

    def prepare_retraining_batch(self) -> Tuple[List[FeedbackEvent], str]:
        """Prepare batch for retraining"""
        return self.scheduler.prepare_training_batch()

    def complete_retraining(
        self,
        events: List[FeedbackEvent],
        batch_id: str,
        model_lift: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Complete retraining and generate report

        Args:
            events: Events used in retraining
            batch_id: Batch identifier
            model_lift: Performance improvements (e.g., {"accuracy": 0.05})

        Returns:
            Report dictionary
        """
        # Mark events as incorporated
        self.scheduler.mark_batch_incorporated(events, batch_id)

        # Generate report
        report = {
            "batch_id": batch_id,
            "num_events": len(events),
            "model_lift": model_lift,
            "completed_at": datetime.now().isoformat(),
            "events_by_uncertainty": self._count_by_uncertainty(events),
            "events_by_street": self._count_by_street(events),
            "average_priority": sum(e.priority_score for e in events) / len(events)
        }

        logger.info(
            f"Completed retraining batch {batch_id}: "
            f"{len(events)} events, lift: {model_lift}"
        )

        return report

    def get_statistics(self) -> Dict[str, Any]:
        """Get active learning statistics"""
        pending = self.storage.get_pending_events(limit=10000)
        reviewed = self.storage.get_reviewed_events()

        return {
            "total_pending": len(pending),
            "total_reviewed": len(reviewed),
            "pending_by_uncertainty": self._count_by_uncertainty(pending),
            "reviewed_by_uncertainty": self._count_by_uncertainty(reviewed),
            "average_pending_priority": (
                sum(e.priority_score for e in pending) / len(pending)
                if pending else 0.0
            ),
            "last_retraining": (
                self.scheduler.last_retraining.isoformat()
                if self.scheduler.last_retraining else None
            ),
            "retraining_ready": self.check_retraining_trigger()
        }

    def _count_by_uncertainty(self, events: List[FeedbackEvent]) -> Dict[str, int]:
        """Count events by uncertainty level"""
        counts = defaultdict(int)
        for event in events:
            counts[event.uncertainty_level.value] += 1
        return dict(counts)

    def _count_by_street(self, events: List[FeedbackEvent]) -> Dict[str, int]:
        """Count events by street"""
        counts = defaultdict(int)
        for event in events:
            counts[event.game_state.street.value] += 1
        return dict(counts)


# Global singleton accessor
def get_active_learning() -> ActiveLearningFeedbackLoop:
    """Get global active learning instance"""
    return ActiveLearningFeedbackLoop.get_instance()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Initialize system
    al = ActiveLearningFeedbackLoop()

    # Example game state
    game_state = GameState(
        street=StreetType.TURN,
        pot_size=150.0,
        hero_stack=500.0,
        hero_position="BTN",
        num_players=4,
        board_cards=["Ah", "Kd", "7s", "2c"],
        hole_cards=["Qh", "Jh"],
        pot_odds=0.33,
        action_history=[
            {"player": "UTG", "action": "fold"},
            {"player": "CO", "action": "raise", "amount": 15}
        ]
    )

    # Example uncertain prediction
    prediction = Prediction(
        action=ActionType.CALL,
        probability=0.45,
        alternatives={
            ActionType.FOLD: 0.30,
            ActionType.RAISE: 0.25
        },
        confidence_interval=(0.35, 0.55),
        ev_estimate=25.0,
        ev_interval=(-10.0, 60.0)
    )

    # Process prediction
    event = al.process_prediction(game_state, prediction)

    if event:
        print(f"Created event: {event.event_id}")
        print(f"Uncertainty: {event.uncertainty_level.value}")
        print(f"Priority: {event.priority_score:.2f}")

        # Simulate expert feedback
        feedback = ExpertFeedback(
            correct_action=ActionType.RAISE,
            reasoning="With flush draw and overcards, raising has better fold equity",
            confidence=0.8,
            alternative_actions=[ActionType.CALL],
            timestamp=datetime.now(),
            expert_id="expert_001"
        )

        # Submit feedback
        al.submit_feedback(event.event_id, feedback)

        # Get statistics
        stats = al.get_statistics()
        print("\nStatistics:")
        print(json.dumps(stats, indent=2))
