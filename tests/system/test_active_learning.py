"""
Test suite for Active Learning Feedback Loop

Tests all components of the active learning system including:
- Uncertainty triage
- Feedback storage
- Retraining scheduling
- End-to-end feedback loop

Author: PokerTool Development Team
Version: v48.0.0
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from pokertool.active_learning import (
    ActiveLearningFeedbackLoop,
    UncertaintyTriage,
    FeedbackStorage,
    RetrainingScheduler,
    ActionType,
    StreetType,
    FeedbackStatus,
    UncertaintyLevel,
    GameState,
    Prediction,
    ExpertFeedback,
    FeedbackEvent,
    get_active_learning
)


class TestGameState:
    """Test GameState dataclass"""

    def test_game_state_creation(self):
        """Test creating game state"""
        state = GameState(
            street=StreetType.FLOP,
            pot_size=100.0,
            hero_stack=500.0,
            hero_position="BTN",
            num_players=6,
            board_cards=["Ah", "Kd", "7s"],
            hole_cards=["Qh", "Jh"],
            pot_odds=0.25,
            action_history=[]
        )

        assert state.street == StreetType.FLOP
        assert state.pot_size == 100.0
        assert state.hero_position == "BTN"
        assert len(state.board_cards) == 3

    def test_game_state_serialization(self):
        """Test game state to/from dict"""
        state = GameState(
            street=StreetType.TURN,
            pot_size=150.0,
            hero_stack=450.0,
            hero_position="CO",
            num_players=4,
            board_cards=["Ah", "Kd", "7s", "2c"],
            hole_cards=["Qh", "Jh"],
            pot_odds=0.33,
            action_history=[{"player": "UTG", "action": "fold"}]
        )

        # Convert to dict and back
        state_dict = state.to_dict()
        restored = GameState.from_dict(state_dict)

        assert restored.street == state.street
        assert restored.pot_size == state.pot_size
        assert restored.board_cards == state.board_cards
        assert restored.action_history == state.action_history


class TestPrediction:
    """Test Prediction dataclass"""

    def test_prediction_creation(self):
        """Test creating prediction"""
        pred = Prediction(
            action=ActionType.CALL,
            probability=0.6,
            alternatives={ActionType.FOLD: 0.3, ActionType.RAISE: 0.1},
            confidence_interval=(0.5, 0.7),
            ev_estimate=25.0,
            ev_interval=(10.0, 40.0)
        )

        assert pred.action == ActionType.CALL
        assert pred.probability == 0.6
        assert ActionType.FOLD in pred.alternatives

    def test_prediction_serialization(self):
        """Test prediction to/from dict"""
        pred = Prediction(
            action=ActionType.RAISE,
            probability=0.7,
            alternatives={ActionType.CALL: 0.2, ActionType.FOLD: 0.1},
            confidence_interval=(0.6, 0.8),
            ev_estimate=50.0,
            ev_interval=(30.0, 70.0)
        )

        # Convert to dict and back
        pred_dict = pred.to_dict()
        restored = Prediction.from_dict(pred_dict)

        assert restored.action == pred.action
        assert restored.probability == pred.probability
        assert restored.ev_estimate == pred.ev_estimate


class TestExpertFeedback:
    """Test ExpertFeedback dataclass"""

    def test_feedback_creation(self):
        """Test creating expert feedback"""
        feedback = ExpertFeedback(
            correct_action=ActionType.RAISE,
            reasoning="Better fold equity with raise",
            confidence=0.8,
            alternative_actions=[ActionType.CALL],
            timestamp=datetime.now(),
            expert_id="expert_001"
        )

        assert feedback.correct_action == ActionType.RAISE
        assert feedback.confidence == 0.8
        assert ActionType.CALL in feedback.alternative_actions

    def test_feedback_serialization(self):
        """Test feedback to/from dict"""
        now = datetime.now()
        feedback = ExpertFeedback(
            correct_action=ActionType.FOLD,
            reasoning="Pot odds not favorable",
            confidence=0.9,
            alternative_actions=[],
            timestamp=now,
            expert_id="expert_002"
        )

        # Convert to dict and back
        feedback_dict = feedback.to_dict()
        restored = ExpertFeedback.from_dict(feedback_dict)

        assert restored.correct_action == feedback.correct_action
        assert restored.reasoning == feedback.reasoning
        assert restored.confidence == feedback.confidence


class TestUncertaintyTriage:
    """Test UncertaintyTriage class"""

    def test_high_uncertainty_detection(self):
        """Test detection of high uncertainty"""
        triage = UncertaintyTriage()

        # Create uncertain prediction
        pred = Prediction(
            action=ActionType.CALL,
            probability=0.35,  # Low margin
            alternatives={ActionType.FOLD: 0.33, ActionType.RAISE: 0.32},
            confidence_interval=(0.2, 0.5),
            ev_estimate=10.0,
            ev_interval=(-50.0, 70.0)  # Large EV range
        )

        state = GameState(
            street=StreetType.RIVER,
            pot_size=200.0,
            hero_stack=300.0,
            hero_position="BTN",
            num_players=2,
            board_cards=["Ah", "Kd", "7s", "2c", "9h"],
            hole_cards=["Qh", "Jh"],
            pot_odds=0.4,
            action_history=[]
        )

        level, priority = triage.assess_uncertainty(pred, state)

        assert level == UncertaintyLevel.HIGH
        assert priority > 30.0  # Should have high priority

    def test_low_uncertainty_detection(self):
        """Test detection of low uncertainty"""
        triage = UncertaintyTriage()

        # Create confident prediction
        pred = Prediction(
            action=ActionType.RAISE,
            probability=0.9,  # High confidence
            alternatives={ActionType.CALL: 0.08, ActionType.FOLD: 0.02},
            confidence_interval=(0.85, 0.95),
            ev_estimate=50.0,
            ev_interval=(45.0, 55.0)  # Narrow EV range
        )

        state = GameState(
            street=StreetType.PREFLOP,
            pot_size=30.0,
            hero_stack=500.0,
            hero_position="BTN",
            num_players=6,
            board_cards=[],
            hole_cards=["As", "Ad"],
            pot_odds=0.15,
            action_history=[]
        )

        level, priority = triage.assess_uncertainty(pred, state)

        # Should have low uncertainty (not high/medium)
        assert level in [UncertaintyLevel.LOW, UncertaintyLevel.NEGLIGIBLE]
        assert priority < 15.0  # Should have low priority

    def test_priority_boosting_big_pot(self):
        """Test priority boost for big pot decisions"""
        triage = UncertaintyTriage()

        pred = Prediction(
            action=ActionType.CALL,
            probability=0.5,
            alternatives={ActionType.FOLD: 0.3, ActionType.RAISE: 0.2},
            confidence_interval=(0.4, 0.6),
            ev_estimate=20.0,
            ev_interval=(0.0, 40.0)
        )

        # Big pot (>50% of stack)
        state = GameState(
            street=StreetType.TURN,
            pot_size=300.0,  # 60% of stack
            hero_stack=500.0,
            hero_position="BTN",
            num_players=3,
            board_cards=["Ah", "Kd", "7s", "2c"],
            hole_cards=["Qh", "Jh"],
            pot_odds=0.33,
            action_history=[]
        )

        level_big, priority_big = triage.assess_uncertainty(pred, state)

        # Small pot
        state.pot_size = 50.0

        level_small, priority_small = triage.assess_uncertainty(pred, state)

        # Big pot should have higher priority
        assert priority_big > priority_small


class TestFeedbackStorage:
    """Test FeedbackStorage class"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def storage(self, temp_db):
        """Create storage instance"""
        return FeedbackStorage(temp_db)

    @pytest.fixture
    def sample_event(self):
        """Create sample event"""
        return FeedbackEvent(
            event_id="test_event_001",
            game_state=GameState(
                street=StreetType.FLOP,
                pot_size=100.0,
                hero_stack=500.0,
                hero_position="BTN",
                num_players=4,
                board_cards=["Ah", "Kd", "7s"],
                hole_cards=["Qh", "Jh"],
                pot_odds=0.25,
                action_history=[]
            ),
            prediction=Prediction(
                action=ActionType.CALL,
                probability=0.5,
                alternatives={ActionType.FOLD: 0.3, ActionType.RAISE: 0.2},
                confidence_interval=(0.4, 0.6),
                ev_estimate=20.0,
                ev_interval=(10.0, 30.0)
            ),
            uncertainty_level=UncertaintyLevel.MEDIUM,
            priority_score=50.0,
            feedback=None,
            status=FeedbackStatus.PENDING,
            created_at=datetime.now(),
            reviewed_at=None
        )

    def test_storage_initialization(self, storage):
        """Test storage initialization"""
        assert os.path.exists(storage.db_path)

    def test_save_and_retrieve_event(self, storage, sample_event):
        """Test saving and retrieving event"""
        # Save event
        assert storage.save_event(sample_event)

        # Retrieve event
        retrieved = storage.get_event(sample_event.event_id)

        assert retrieved is not None
        assert retrieved.event_id == sample_event.event_id
        assert retrieved.uncertainty_level == sample_event.uncertainty_level
        assert retrieved.priority_score == sample_event.priority_score

    def test_get_pending_events(self, storage, sample_event):
        """Test retrieving pending events"""
        # Save multiple events
        for i in range(5):
            event = FeedbackEvent(
                event_id=f"event_{i}",
                game_state=sample_event.game_state,
                prediction=sample_event.prediction,
                uncertainty_level=UncertaintyLevel.MEDIUM,
                priority_score=50.0 + i,
                feedback=None,
                status=FeedbackStatus.PENDING,
                created_at=datetime.now(),
                reviewed_at=None
            )
            storage.save_event(event)

        # Get pending events
        pending = storage.get_pending_events(limit=10)

        assert len(pending) == 5
        # Should be sorted by priority (descending)
        assert pending[0].priority_score >= pending[-1].priority_score

    def test_get_reviewed_events(self, storage, sample_event):
        """Test retrieving reviewed events"""
        # Add feedback and mark as reviewed
        sample_event.feedback = ExpertFeedback(
            correct_action=ActionType.RAISE,
            reasoning="Test reasoning",
            confidence=0.8,
            alternative_actions=[],
            timestamp=datetime.now(),
            expert_id="expert_001"
        )
        sample_event.status = FeedbackStatus.REVIEWED
        sample_event.reviewed_at = datetime.now()

        storage.save_event(sample_event)

        # Get reviewed events
        reviewed = storage.get_reviewed_events()

        assert len(reviewed) == 1
        assert reviewed[0].status == FeedbackStatus.REVIEWED
        assert reviewed[0].feedback is not None

    def test_mark_incorporated(self, storage, sample_event):
        """Test marking events as incorporated"""
        # Save event
        sample_event.status = FeedbackStatus.REVIEWED
        storage.save_event(sample_event)

        # Mark as incorporated
        batch_id = "batch_001"
        storage.mark_incorporated([sample_event.event_id], batch_id)

        # Retrieve and verify
        event = storage.get_event(sample_event.event_id)

        assert event.status == FeedbackStatus.INCORPORATED


class TestRetrainingScheduler:
    """Test RetrainingScheduler class"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def scheduler(self, temp_db):
        """Create scheduler instance"""
        storage = FeedbackStorage(temp_db)
        return RetrainingScheduler(
            storage,
            min_samples_for_retraining=5,
            retraining_interval_days=1
        )

    def test_should_not_trigger_without_samples(self, scheduler):
        """Test that retraining doesn't trigger without enough samples"""
        assert not scheduler.should_trigger_retraining()

    def test_should_trigger_with_enough_samples(self, scheduler):
        """Test that retraining triggers with enough samples"""
        # Add reviewed events
        for i in range(10):
            event = FeedbackEvent(
                event_id=f"event_{i}",
                game_state=GameState(
                    street=StreetType.FLOP,
                    pot_size=100.0,
                    hero_stack=500.0,
                    hero_position="BTN",
                    num_players=4,
                    board_cards=["Ah", "Kd", "7s"],
                    hole_cards=["Qh", "Jh"],
                    pot_odds=0.25,
                    action_history=[]
                ),
                prediction=Prediction(
                    action=ActionType.CALL,
                    probability=0.5,
                    alternatives={},
                    confidence_interval=(0.4, 0.6),
                    ev_estimate=20.0,
                    ev_interval=(10.0, 30.0)
                ),
                uncertainty_level=UncertaintyLevel.MEDIUM,
                priority_score=50.0,
                feedback=ExpertFeedback(
                    correct_action=ActionType.RAISE,
                    reasoning="Test",
                    confidence=0.8,
                    alternative_actions=[],
                    timestamp=datetime.now(),
                    expert_id="expert_001"
                ),
                status=FeedbackStatus.REVIEWED,
                created_at=datetime.now(),
                reviewed_at=datetime.now()
            )
            scheduler.storage.save_event(event)

        assert scheduler.should_trigger_retraining()

    def test_prepare_training_batch(self, scheduler):
        """Test preparing training batch"""
        # Add reviewed events
        for i in range(5):
            event = FeedbackEvent(
                event_id=f"event_{i}",
                game_state=GameState(
                    street=StreetType.FLOP,
                    pot_size=100.0,
                    hero_stack=500.0,
                    hero_position="BTN",
                    num_players=4,
                    board_cards=["Ah", "Kd", "7s"],
                    hole_cards=["Qh", "Jh"],
                    pot_odds=0.25,
                    action_history=[]
                ),
                prediction=Prediction(
                    action=ActionType.CALL,
                    probability=0.5,
                    alternatives={},
                    confidence_interval=(0.4, 0.6),
                    ev_estimate=20.0,
                    ev_interval=(10.0, 30.0)
                ),
                uncertainty_level=UncertaintyLevel.MEDIUM,
                priority_score=50.0,
                feedback=ExpertFeedback(
                    correct_action=ActionType.RAISE,
                    reasoning="Test",
                    confidence=0.8,
                    alternative_actions=[],
                    timestamp=datetime.now(),
                    expert_id="expert_001"
                ),
                status=FeedbackStatus.REVIEWED,
                created_at=datetime.now(),
                reviewed_at=datetime.now()
            )
            scheduler.storage.save_event(event)

        events, batch_id = scheduler.prepare_training_batch()

        assert len(events) == 5
        assert batch_id.startswith("batch_")


class TestActiveLearningFeedbackLoop:
    """Test ActiveLearningFeedbackLoop main class"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def feedback_loop(self, temp_db):
        """Create feedback loop instance"""
        return ActiveLearningFeedbackLoop(storage_path=temp_db)

    def test_process_confident_prediction(self, feedback_loop):
        """Test processing confident prediction (low uncertainty)"""
        state = GameState(
            street=StreetType.PREFLOP,
            pot_size=30.0,
            hero_stack=500.0,
            hero_position="BTN",
            num_players=6,
            board_cards=[],
            hole_cards=["As", "Ad"],
            pot_odds=0.15,
            action_history=[]
        )

        # Confident prediction
        pred = Prediction(
            action=ActionType.RAISE,
            probability=0.95,
            alternatives={ActionType.CALL: 0.03, ActionType.FOLD: 0.02},
            confidence_interval=(0.9, 0.97),
            ev_estimate=50.0,
            ev_interval=(48.0, 52.0)
        )

        event = feedback_loop.process_prediction(state, pred)

        # If event created, it should have low priority
        if event:
            assert event.uncertainty_level in [UncertaintyLevel.LOW, UncertaintyLevel.NEGLIGIBLE]
            assert event.priority_score < 20.0

    def test_process_uncertain_prediction(self, feedback_loop):
        """Test processing uncertain prediction (should queue)"""
        state = GameState(
            street=StreetType.TURN,
            pot_size=150.0,
            hero_stack=500.0,
            hero_position="BTN",
            num_players=3,
            board_cards=["Ah", "Kd", "7s", "2c"],
            hole_cards=["Qh", "Jh"],
            pot_odds=0.33,
            action_history=[]
        )

        # Uncertain prediction
        pred = Prediction(
            action=ActionType.CALL,
            probability=0.4,
            alternatives={ActionType.FOLD: 0.35, ActionType.RAISE: 0.25},
            confidence_interval=(0.3, 0.5),
            ev_estimate=15.0,
            ev_interval=(-20.0, 50.0)
        )

        event = feedback_loop.process_prediction(state, pred)

        # Should create event for uncertain prediction
        assert event is not None
        assert event.uncertainty_level in [UncertaintyLevel.HIGH, UncertaintyLevel.MEDIUM]
        assert event.priority_score > 0.0

    def test_submit_and_retrieve_feedback(self, feedback_loop):
        """Test submitting and retrieving feedback"""
        # First create an uncertain event
        state = GameState(
            street=StreetType.FLOP,
            pot_size=100.0,
            hero_stack=500.0,
            hero_position="BTN",
            num_players=4,
            board_cards=["Ah", "Kd", "7s"],
            hole_cards=["Qh", "Jh"],
            pot_odds=0.25,
            action_history=[]
        )

        pred = Prediction(
            action=ActionType.CALL,
            probability=0.45,
            alternatives={ActionType.FOLD: 0.30, ActionType.RAISE: 0.25},
            confidence_interval=(0.35, 0.55),
            ev_estimate=20.0,
            ev_interval=(0.0, 40.0)
        )

        event = feedback_loop.process_prediction(state, pred)
        assert event is not None

        # Submit feedback
        feedback = ExpertFeedback(
            correct_action=ActionType.RAISE,
            reasoning="Better fold equity",
            confidence=0.8,
            alternative_actions=[ActionType.CALL],
            timestamp=datetime.now(),
            expert_id="expert_001"
        )

        success = feedback_loop.submit_feedback(event.event_id, feedback)
        assert success

        # Verify event was updated
        updated_event = feedback_loop.storage.get_event(event.event_id)
        assert updated_event.status == FeedbackStatus.REVIEWED
        assert updated_event.feedback is not None
        assert updated_event.feedback.correct_action == ActionType.RAISE

    def test_get_review_queue(self, feedback_loop):
        """Test getting review queue"""
        # Create multiple uncertain predictions
        for i in range(5):
            state = GameState(
                street=StreetType.TURN,
                pot_size=100.0 + i * 20,
                hero_stack=500.0,
                hero_position="BTN",
                num_players=4,
                board_cards=["Ah", "Kd", "7s", "2c"],
                hole_cards=["Qh", "Jh"],
                pot_odds=0.3,
                action_history=[]
            )

            pred = Prediction(
                action=ActionType.CALL,
                probability=0.4 + i * 0.02,
                alternatives={ActionType.FOLD: 0.35, ActionType.RAISE: 0.25},
                confidence_interval=(0.3, 0.5),
                ev_estimate=20.0,
                ev_interval=(0.0, 40.0)
            )

            feedback_loop.process_prediction(state, pred)

        # Get review queue
        queue = feedback_loop.get_review_queue(limit=3)

        # Should get top 3 priority items
        assert len(queue) <= 3

    def test_statistics(self, feedback_loop):
        """Test getting statistics"""
        # Create some events
        for i in range(3):
            state = GameState(
                street=StreetType.FLOP,
                pot_size=100.0,
                hero_stack=500.0,
                hero_position="BTN",
                num_players=4,
                board_cards=["Ah", "Kd", "7s"],
                hole_cards=["Qh", "Jh"],
                pot_odds=0.25,
                action_history=[]
            )

            pred = Prediction(
                action=ActionType.CALL,
                probability=0.4,
                alternatives={ActionType.FOLD: 0.35, ActionType.RAISE: 0.25},
                confidence_interval=(0.3, 0.5),
                ev_estimate=20.0,
                ev_interval=(0.0, 40.0)
            )

            feedback_loop.process_prediction(state, pred)

        stats = feedback_loop.get_statistics()

        assert "total_pending" in stats
        assert "total_reviewed" in stats
        assert stats["total_pending"] >= 0

    def test_complete_retraining(self, feedback_loop):
        """Test completing retraining cycle"""
        # Create and review events
        events = []
        for i in range(5):
            state = GameState(
                street=StreetType.FLOP,
                pot_size=100.0,
                hero_stack=500.0,
                hero_position="BTN",
                num_players=4,
                board_cards=["Ah", "Kd", "7s"],
                hole_cards=["Qh", "Jh"],
                pot_odds=0.25,
                action_history=[]
            )

            pred = Prediction(
                action=ActionType.CALL,
                probability=0.4,
                alternatives={ActionType.FOLD: 0.35, ActionType.RAISE: 0.25},
                confidence_interval=(0.3, 0.5),
                ev_estimate=20.0,
                ev_interval=(0.0, 40.0)
            )

            event = feedback_loop.process_prediction(state, pred)
            if event:
                feedback = ExpertFeedback(
                    correct_action=ActionType.RAISE,
                    reasoning="Test",
                    confidence=0.8,
                    alternative_actions=[],
                    timestamp=datetime.now(),
                    expert_id="expert_001"
                )
                feedback_loop.submit_feedback(event.event_id, feedback)
                events.append(event)

        # Complete retraining
        batch_id = "test_batch_001"
        model_lift = {"accuracy": 0.05, "f1_score": 0.03}

        report = feedback_loop.complete_retraining(events, batch_id, model_lift)

        assert report["batch_id"] == batch_id
        assert report["model_lift"] == model_lift
        assert report["num_events"] == len(events)


class TestGlobalAccessor:
    """Test global singleton accessor"""

    def test_get_active_learning_singleton(self):
        """Test that global accessor returns singleton"""
        al1 = get_active_learning()
        al2 = get_active_learning()

        # Should be same instance
        assert al1 is al2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
