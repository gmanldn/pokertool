"""
Comprehensive tests for Sequential Opponent State Fusion

Tests transformer architecture, rolling window aggregation,
temporal embeddings, caching, and prediction integration.
"""

import pytest
import numpy as np
import time
import tempfile
from pathlib import Path

from pokertool.sequential_opponent_fusion import (
    ActionType, Street, PlayerAction, HandSequence,
    SimpleTransformer, SequentialOpponentFusion,
    SequenceFeatures, get_fusion_system
)


class TestPlayerAction:
    """Test PlayerAction dataclass"""

    def test_create_action(self):
        """Test creating a player action"""
        action = PlayerAction(
            player_id="player1",
            action=ActionType.RAISE,
            amount=100.0,
            street=Street.FLOP,
            position=3,
            pot_size=250.0,
            stack_size=1500.0,
            timestamp=time.time(),
            time_taken=2.5
        )

        assert action.player_id == "player1"
        assert action.action == ActionType.RAISE
        assert action.amount == 100.0
        assert action.street == Street.FLOP

    def test_action_to_vector(self):
        """Test converting action to feature vector"""
        action = PlayerAction(
            player_id="player1",
            action=ActionType.BET,
            amount=50.0,
            street=Street.PREFLOP,
            position=2,
            pot_size=100.0,
            stack_size=1000.0,
            timestamp=time.time(),
            time_taken=1.5
        )

        vector = action.to_vector()
        assert isinstance(vector, np.ndarray)
        assert vector.shape == (7,)
        assert vector[0] == ActionType.BET.value
        assert vector[1] == 50.0
        assert vector[2] == Street.PREFLOP.value

    def test_action_to_dict(self):
        """Test converting action to dictionary"""
        action = PlayerAction(
            player_id="player2",
            action=ActionType.CALL,
            amount=25.0,
            street=Street.TURN,
            position=4,
            pot_size=200.0,
            stack_size=800.0,
            timestamp=123456.0,
            time_taken=3.0
        )

        d = action.to_dict()
        assert d['player_id'] == "player2"
        assert d['action'] == "CALL"
        assert d['amount'] == 25.0
        assert d['street'] == "TURN"


class TestHandSequence:
    """Test HandSequence dataclass"""

    def test_create_hand_sequence(self):
        """Test creating a hand sequence"""
        actions = [
            PlayerAction("p1", ActionType.RAISE, 50, Street.PREFLOP,
                        2, 15, 1000, time.time(), 2.0),
            PlayerAction("p2", ActionType.CALL, 50, Street.PREFLOP,
                        3, 100, 950, time.time(), 1.5),
        ]

        hand = HandSequence(
            hand_id="hand123",
            actions=actions,
            outcome={"p1": 100.0, "p2": -100.0},
            timestamp=time.time()
        )

        assert hand.hand_id == "hand123"
        assert len(hand.actions) == 2
        assert hand.outcome["p1"] == 100.0

    def test_get_player_actions(self):
        """Test filtering actions by player"""
        actions = [
            PlayerAction("p1", ActionType.RAISE, 50, Street.PREFLOP,
                        2, 15, 1000, time.time(), 2.0),
            PlayerAction("p2", ActionType.CALL, 50, Street.PREFLOP,
                        3, 100, 950, time.time(), 1.5),
            PlayerAction("p1", ActionType.BET, 75, Street.FLOP,
                        2, 100, 950, time.time(), 3.0),
        ]

        hand = HandSequence("hand1", actions, {}, time.time())

        p1_actions = hand.get_player_actions("p1")
        assert len(p1_actions) == 2
        assert all(a.player_id == "p1" for a in p1_actions)

        p2_actions = hand.get_player_actions("p2")
        assert len(p2_actions) == 1
        assert p2_actions[0].action == ActionType.CALL

    def test_hand_to_dict(self):
        """Test converting hand to dictionary"""
        actions = [
            PlayerAction("p1", ActionType.FOLD, 0, Street.PREFLOP,
                        1, 10, 1000, time.time(), 1.0),
        ]

        hand = HandSequence("hand456", actions, {"p1": -10}, 123456.0)
        d = hand.to_dict()

        assert d['hand_id'] == "hand456"
        assert len(d['actions']) == 1
        assert d['outcome']['p1'] == -10


class TestSimpleTransformer:
    """Test transformer architecture"""

    def test_create_transformer(self):
        """Test creating transformer"""
        transformer = SimpleTransformer(
            input_dim=7,
            hidden_dim=64,
            num_heads=4,
            num_layers=2
        )

        assert transformer.input_dim == 7
        assert transformer.hidden_dim == 64
        assert transformer.num_heads == 4
        assert transformer.num_layers == 2

    def test_embed_sequence(self):
        """Test sequence embedding"""
        transformer = SimpleTransformer(input_dim=7, hidden_dim=64)

        # Create test sequence
        sequence = np.random.randn(10, 7).astype(np.float32)
        embedded = transformer.embed_sequence(sequence)

        assert embedded.shape == (10, 64)

    def test_self_attention(self):
        """Test self-attention mechanism"""
        transformer = SimpleTransformer(input_dim=7, hidden_dim=64, num_heads=4)

        # Create test input
        x = np.random.randn(10, 64).astype(np.float32)
        weights = transformer.attention_weights[0]

        output, attention = transformer.self_attention(x, weights)

        assert output.shape == (10, 64)
        assert attention.shape == (10, 10)

        # Attention should sum to 1 along columns
        attention_sums = attention.sum(axis=1)
        np.testing.assert_allclose(attention_sums, 1.0, rtol=1e-5)

    def test_forward_pass(self):
        """Test complete forward pass"""
        transformer = SimpleTransformer(
            input_dim=7,
            hidden_dim=64,
            num_heads=4,
            num_layers=2
        )

        # Create test sequence
        sequence = np.random.randn(15, 7).astype(np.float32)
        embeddings, attention_history = transformer.forward(sequence)

        assert embeddings.shape == (15, 64)
        assert len(attention_history) == 2  # 2 layers
        assert all(a.shape == (15, 15) for a in attention_history)

    def test_layer_norm(self):
        """Test layer normalization"""
        transformer = SimpleTransformer()

        x = np.random.randn(10, 64).astype(np.float32)
        normed = transformer._layer_norm(x)

        # Check that mean is close to 0 and std is close to 1
        assert normed.shape == x.shape
        assert np.abs(normed.mean()) < 0.1
        assert np.abs(normed.std() - 1.0) < 0.1


class TestSequentialOpponentFusion:
    """Test main fusion system"""

    def test_create_fusion_system(self):
        """Test creating fusion system"""
        fusion = SequentialOpponentFusion(window_size=50, cache_size=1000)

        assert fusion.window_size == 50
        assert fusion.cache_size == 1000
        assert len(fusion.player_histories) == 0

    def test_add_hand(self):
        """Test adding hand to history"""
        fusion = SequentialOpponentFusion(window_size=10)

        actions = [
            PlayerAction("p1", ActionType.RAISE, 50, Street.PREFLOP,
                        2, 15, 1000, time.time(), 2.0),
            PlayerAction("p2", ActionType.CALL, 50, Street.PREFLOP,
                        3, 100, 950, time.time(), 1.5),
        ]

        hand = HandSequence("hand1", actions, {"p1": 100, "p2": -100}, time.time())
        fusion.add_hand(hand)

        assert len(fusion.player_histories["p1"]) == 1
        assert len(fusion.player_histories["p2"]) == 1
        assert fusion.stats['sequences_processed'] == 1
        assert fusion.stats['players_tracked'] == 2

    def test_window_size_limit(self):
        """Test that window size is respected"""
        fusion = SequentialOpponentFusion(window_size=5)

        # Add 10 hands for same player
        for i in range(10):
            actions = [
                PlayerAction("p1", ActionType.RAISE, 50, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.0),
            ]
            hand = HandSequence(f"hand{i}", actions, {"p1": 0}, time.time())
            fusion.add_hand(hand)

        # Should only keep last 5
        assert len(fusion.player_histories["p1"]) == 5
        assert fusion.player_histories["p1"][0].hand_id == "hand5"
        assert fusion.player_histories["p1"][-1].hand_id == "hand9"

    def test_get_player_embedding_insufficient_history(self):
        """Test embedding with insufficient history"""
        fusion = SequentialOpponentFusion()

        # No history
        embedding = fusion.get_player_embedding("unknown_player")
        assert embedding is None

        # Add one hand (insufficient)
        actions = [
            PlayerAction("p1", ActionType.FOLD, 0, Street.PREFLOP,
                        1, 10, 1000, time.time(), 1.0),
        ]
        hand = HandSequence("hand1", actions, {"p1": -10}, time.time())
        fusion.add_hand(hand)

        embedding = fusion.get_player_embedding("p1")
        assert embedding is None  # Still insufficient

    def test_get_player_embedding_sufficient_history(self):
        """Test embedding with sufficient history"""
        fusion = SequentialOpponentFusion()

        # Add multiple hands with multiple actions
        for i in range(10):
            actions = [
                PlayerAction("p1", ActionType.RAISE, 50 + i*10, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.0 + i*0.1),
                PlayerAction("p1", ActionType.BET, 75 + i*5, Street.FLOP,
                            2, 100, 950, time.time(), 3.0),
            ]
            hand = HandSequence(f"hand{i}", actions, {"p1": 100}, time.time())
            fusion.add_hand(hand)

        embedding = fusion.get_player_embedding("p1")

        assert embedding is not None
        assert isinstance(embedding, SequenceFeatures)
        assert len(embedding.embedding) == 64  # hidden_dim
        assert 0 <= embedding.aggression_score <= 1
        assert 0 <= embedding.bluff_likelihood <= 1

    def test_embedding_caching(self):
        """Test that embeddings are cached"""
        fusion = SequentialOpponentFusion()

        # Add sufficient history
        for i in range(10):
            actions = [
                PlayerAction("p1", ActionType.RAISE, 50, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.0),
                PlayerAction("p1", ActionType.BET, 75, Street.FLOP,
                            2, 100, 950, time.time(), 3.0),
            ]
            hand = HandSequence(f"hand{i}", actions, {"p1": 100}, time.time())
            fusion.add_hand(hand)

        # First call should be cache miss
        fusion.get_player_embedding("p1")
        assert fusion.stats['cache_misses'] == 1
        assert fusion.stats['cache_hits'] == 0

        # Second call should be cache hit
        fusion.get_player_embedding("p1")
        assert fusion.stats['cache_hits'] == 1

        # Third call should also be cache hit
        fusion.get_player_embedding("p1")
        assert fusion.stats['cache_hits'] == 2

    def test_cache_invalidation_on_new_hand(self):
        """Test that cache is invalidated when new hands are added"""
        fusion = SequentialOpponentFusion()

        # Add sufficient history
        for i in range(10):
            actions = [
                PlayerAction("p1", ActionType.CALL, 25, Street.PREFLOP,
                            3, 15, 1000, time.time(), 1.5),
            ]
            hand = HandSequence(f"hand{i}", actions, {"p1": 0}, time.time())
            fusion.add_hand(hand)

        # Get embedding (cache miss)
        fusion.get_player_embedding("p1")
        assert fusion.stats['cache_misses'] == 1

        # Get again (cache hit)
        fusion.get_player_embedding("p1")
        assert fusion.stats['cache_hits'] == 1

        # Add new hand (should invalidate cache)
        actions = [
            PlayerAction("p1", ActionType.RAISE, 100, Street.PREFLOP,
                        2, 15, 1000, time.time(), 2.5),
        ]
        hand = HandSequence("new_hand", actions, {"p1": 50}, time.time())
        fusion.add_hand(hand)

        # Get embedding again (should be cache miss)
        fusion.get_player_embedding("p1")
        assert fusion.stats['cache_misses'] == 2

    def test_aggression_score_calculation(self):
        """Test aggression score computation"""
        fusion = SequentialOpponentFusion()

        # Add aggressive actions
        for i in range(10):
            actions = [
                PlayerAction("aggressive", ActionType.RAISE, 100, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.0),
                PlayerAction("aggressive", ActionType.BET, 150, Street.FLOP,
                            2, 100, 900, time.time(), 2.5),
            ]
            hand = HandSequence(f"hand{i}", actions, {"aggressive": 100}, time.time())
            fusion.add_hand(hand)

        features = fusion.get_player_embedding("aggressive")
        assert features.aggression_score > 0.8  # Should be very aggressive

        # Add passive player
        for i in range(10):
            actions = [
                PlayerAction("passive", ActionType.CALL, 25, Street.PREFLOP,
                            3, 15, 1000, time.time(), 1.0),
                PlayerAction("passive", ActionType.CHECK, 0, Street.FLOP,
                            3, 50, 975, time.time(), 0.5),
            ]
            hand = HandSequence(f"hand{i}", actions, {"passive": -25}, time.time())
            fusion.add_hand(hand)

        features = fusion.get_player_embedding("passive")
        assert features.aggression_score < 0.3  # Should be very passive

    def test_get_prediction_context_no_history(self):
        """Test prediction context with no history"""
        fusion = SequentialOpponentFusion()

        context = fusion.get_prediction_context("unknown", {})

        assert context['has_history'] is False
        assert 'recommendation' in context

    def test_get_prediction_context_with_history(self):
        """Test prediction context with sufficient history"""
        fusion = SequentialOpponentFusion()

        # Add history
        for i in range(10):
            actions = [
                PlayerAction("p1", ActionType.RAISE, 100, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.5),
                PlayerAction("p1", ActionType.BET, 150, Street.FLOP,
                            2, 100, 900, time.time(), 3.0),
            ]
            hand = HandSequence(f"hand{i}", actions, {"p1": 100}, time.time())
            fusion.add_hand(hand)

        context = fusion.get_prediction_context("p1", {})

        assert context['has_history'] is True
        assert 'temporal_features' in context
        assert 'aggression_score' in context['temporal_features']
        assert 'bluff_likelihood' in context['temporal_features']
        assert 'attention_summary' in context
        assert 'recommendations' in context
        assert isinstance(context['recommendations'], list)

    def test_recommendations_generation(self):
        """Test that appropriate recommendations are generated"""
        fusion = SequentialOpponentFusion()

        # Add very aggressive player
        for i in range(10):
            actions = [
                PlayerAction("aggro", ActionType.RAISE, 150, Street.PREFLOP,
                            2, 15, 1000, time.time(), 1.5),
                PlayerAction("aggro", ActionType.BET, 200, Street.FLOP,
                            2, 100, 850, time.time(), 1.8),
                PlayerAction("aggro", ActionType.RAISE, 300, Street.TURN,
                            2, 300, 650, time.time(), 2.0),
            ]
            hand = HandSequence(f"hand{i}", actions, {"aggro": 200}, time.time())
            fusion.add_hand(hand)

        context = fusion.get_prediction_context("aggro", {})

        # Should have aggression-related recommendation
        recommendations = context['recommendations']
        assert any("aggression" in r.lower() for r in recommendations)

    def test_cache_pruning(self):
        """Test that cache is pruned when it exceeds size limit"""
        fusion = SequentialOpponentFusion(cache_size=5)

        # Add history for 10 different players
        for player_num in range(10):
            player_id = f"player{player_num}"

            for i in range(10):
                actions = [
                    PlayerAction(player_id, ActionType.RAISE, 50, Street.PREFLOP,
                                2, 15, 1000, time.time(), 2.0),
                ]
                hand = HandSequence(f"hand{player_num}_{i}", actions,
                                  {player_id: 0}, time.time())
                fusion.add_hand(hand)

            # Get embedding to populate cache
            fusion.get_player_embedding(player_id)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Cache should be pruned to size limit
        assert len(fusion.embedding_cache) <= fusion.cache_size

    def test_get_statistics(self):
        """Test statistics reporting"""
        fusion = SequentialOpponentFusion()

        # Add some data
        for i in range(5):
            actions = [
                PlayerAction("p1", ActionType.RAISE, 50, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.0),
            ]
            hand = HandSequence(f"hand{i}", actions, {"p1": 0}, time.time())
            fusion.add_hand(hand)

        # Get embedding a few times
        for _ in range(3):
            fusion.get_player_embedding("p1")

        stats = fusion.get_statistics()

        assert stats['sequences_processed'] == 5
        assert stats['players_tracked'] == 1
        assert 'cache_hit_rate' in stats
        assert stats['window_size'] == fusion.window_size

    def test_save_and_load_state(self):
        """Test saving and loading system state"""
        fusion = SequentialOpponentFusion()

        # Add some history
        for i in range(5):
            actions = [
                PlayerAction("p1", ActionType.RAISE, 50 + i*10, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.0),
            ]
            hand = HandSequence(f"hand{i}", actions, {"p1": 100}, time.time())
            fusion.add_hand(hand)

        # Save state
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "fusion_state.json"
            fusion.save_state(filepath)

            # Create new system and load state
            fusion2 = SequentialOpponentFusion()
            fusion2.load_state(filepath)

            # Verify state was loaded correctly
            assert fusion2.window_size == fusion.window_size
            assert fusion2.stats['sequences_processed'] == fusion.stats['sequences_processed']
            assert len(fusion2.player_histories["p1"]) == 5

    def test_multiple_players_tracking(self):
        """Test tracking multiple players simultaneously"""
        fusion = SequentialOpponentFusion()

        # Add hands with multiple players
        for i in range(10):
            actions = [
                PlayerAction("p1", ActionType.RAISE, 50, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.0),
                PlayerAction("p2", ActionType.CALL, 50, Street.PREFLOP,
                            3, 100, 950, time.time(), 1.5),
                PlayerAction("p3", ActionType.FOLD, 0, Street.PREFLOP,
                            4, 100, 1000, time.time(), 0.5),
            ]
            hand = HandSequence(f"hand{i}", actions,
                              {"p1": 100, "p2": -50, "p3": -50}, time.time())
            fusion.add_hand(hand)

        # All players should have history
        assert len(fusion.player_histories["p1"]) == 10
        assert len(fusion.player_histories["p2"]) == 10
        assert len(fusion.player_histories["p3"]) == 10

        # All should have embeddings
        emb1 = fusion.get_player_embedding("p1")
        emb2 = fusion.get_player_embedding("p2")
        emb3 = fusion.get_player_embedding("p3")

        assert emb1 is not None
        assert emb2 is not None
        assert emb3 is not None

        # p1 should be most aggressive
        assert emb1.aggression_score > emb2.aggression_score
        assert emb1.aggression_score > emb3.aggression_score


class TestGlobalSingleton:
    """Test global singleton pattern"""

    def test_get_fusion_system(self):
        """Test getting global fusion system"""
        system1 = get_fusion_system()
        system2 = get_fusion_system()

        # Should return same instance
        assert system1 is system2

    def test_singleton_persistence(self):
        """Test that singleton persists data"""
        system = get_fusion_system()

        # Add some data
        actions = [
            PlayerAction("singleton_test", ActionType.RAISE, 50, Street.PREFLOP,
                        2, 15, 1000, time.time(), 2.0),
        ]
        hand = HandSequence("hand_singleton", actions, {"singleton_test": 0}, time.time())
        system.add_hand(hand)

        # Get system again and verify data persists
        system2 = get_fusion_system()
        assert len(system2.player_histories["singleton_test"]) > 0


class TestIntegration:
    """Integration tests"""

    def test_end_to_end_workflow(self):
        """Test complete workflow from hand to prediction context"""
        fusion = SequentialOpponentFusion()

        # Simulate a series of hands
        player_ids = ["hero", "villain1", "villain2"]

        for hand_num in range(15):
            actions = []

            # Preflop action
            actions.append(PlayerAction(
                "villain1", ActionType.RAISE, 50,
                Street.PREFLOP, 2, 15, 1000, time.time(), 2.5
            ))
            actions.append(PlayerAction(
                "hero", ActionType.CALL, 50,
                Street.PREFLOP, 3, 100, 975, time.time(), 1.8
            ))
            actions.append(PlayerAction(
                "villain2", ActionType.FOLD, 0,
                Street.PREFLOP, 4, 100, 1000, time.time(), 0.5
            ))

            # Flop action
            actions.append(PlayerAction(
                "villain1", ActionType.BET, 75,
                Street.FLOP, 2, 100, 925, time.time(), 3.0
            ))
            actions.append(PlayerAction(
                "hero", ActionType.CALL, 75,
                Street.FLOP, 3, 175, 900, time.time(), 2.5
            ))

            hand = HandSequence(
                f"hand{hand_num}",
                actions,
                {"villain1": 175, "hero": -175, "villain2": -10},
                time.time()
            )

            fusion.add_hand(hand)

        # Get predictions for all players
        contexts = {}
        for player_id in player_ids:
            contexts[player_id] = fusion.get_prediction_context(
                player_id, {"pot": 250, "stacks": {}}
            )

        # Hero and villain1 should have history
        assert contexts["hero"]['has_history'] is True
        assert contexts["villain1"]['has_history'] is True

        # Villain1 should show high aggression
        v1_features = contexts["villain1"]['temporal_features']
        assert v1_features['aggression_score'] > 0.7

        # Verify statistics
        stats = fusion.get_statistics()
        assert stats['sequences_processed'] == 15
        assert stats['players_tracked'] == 3

    def test_performance_with_large_history(self):
        """Test performance with large action history"""
        fusion = SequentialOpponentFusion(window_size=100)

        start_time = time.time()

        # Add 100 hands with multiple actions each
        for i in range(100):
            actions = [
                PlayerAction("perf_test", ActionType.RAISE, 50 + i, Street.PREFLOP,
                            2, 15, 1000, time.time(), 2.0),
                PlayerAction("perf_test", ActionType.BET, 75 + i, Street.FLOP,
                            2, 100, 950, time.time(), 2.5),
                PlayerAction("perf_test", ActionType.BET, 100 + i, Street.TURN,
                            2, 200, 850, time.time(), 3.0),
            ]
            hand = HandSequence(f"hand{i}", actions, {"perf_test": 0}, time.time())
            fusion.add_hand(hand)

        # Get embedding
        features = fusion.get_player_embedding("perf_test")

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 2 seconds)
        assert elapsed < 2.0
        assert features is not None

    def test_concurrent_player_tracking(self):
        """Test tracking many players concurrently"""
        fusion = SequentialOpponentFusion(window_size=20)

        # Create 50 players
        num_players = 50

        for hand_num in range(30):
            # Randomly select 6 players for this hand
            import random
            random.seed(hand_num)
            players = [f"player{i}" for i in random.sample(range(num_players), 6)]

            actions = []
            for i, player_id in enumerate(players):
                actions.append(PlayerAction(
                    player_id,
                    random.choice([ActionType.RAISE, ActionType.CALL, ActionType.FOLD]),
                    random.uniform(10, 100),
                    Street.PREFLOP,
                    i,
                    random.uniform(10, 200),
                    random.uniform(500, 1500),
                    time.time(),
                    random.uniform(0.5, 3.0)
                ))

            hand = HandSequence(
                f"hand{hand_num}",
                actions,
                {p: random.uniform(-50, 50) for p in players},
                time.time()
            )

            fusion.add_hand(hand)

        # Should track many players
        stats = fusion.get_statistics()
        assert stats['players_tracked'] > 20

        # Cache should be working efficiently
        assert 'cache_hit_rate' in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
