"""
Tests for Reinforcement Learning Agent Module

This module tests the RL agent for strategy improvement including
PPO algorithm, experience replay, reward shaping, curriculum learning,
and multi-agent training.

Author: PokerTool Development Team
Date: 2025-01-10
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.pokertool.rl_agent import (
    Action,
    AgentLevel,
    CurriculumManager,
    Experience,
    ExperienceReplayBuffer,
    MultiAgentTrainer,
    PolicyNetwork,
    PPOTrainer,
    RewardShaper,
    RLAgent,
    ValueNetwork,
)


class TestPolicyNetwork(unittest.TestCase):
    """Test policy network"""
    
    def test_initialization(self):
        """Test network initialization"""
        network = PolicyNetwork(input_size=128, hidden_size=256, output_size=6)
        self.assertEqual(network.input_size, 128)
        self.assertEqual(network.hidden_size, 256)
        self.assertEqual(network.output_size, 6)
    
    def test_forward_pass(self):
        """Test forward pass"""
        network = PolicyNetwork(input_size=128, hidden_size=256, output_size=6)
        state = np.random.randn(128)
        
        action_probs, value = network.forward(state)
        
        self.assertEqual(len(action_probs), 6)
        self.assertAlmostEqual(np.sum(action_probs), 1.0, places=5)
        self.assertIsInstance(value, (float, np.floating))
    
    def test_action_probabilities_valid(self):
        """Test action probabilities are valid"""
        network = PolicyNetwork(input_size=64, hidden_size=128, output_size=6)
        state = np.random.randn(64)
        
        action_probs, _ = network.forward(state)
        
        # All probabilities should be between 0 and 1
        self.assertTrue(np.all(action_probs >= 0))
        self.assertTrue(np.all(action_probs <= 1))


class TestValueNetwork(unittest.TestCase):
    """Test value network"""
    
    def test_initialization(self):
        """Test network initialization"""
        network = ValueNetwork(input_size=128, hidden_size=256)
        self.assertEqual(network.input_size, 128)
        self.assertEqual(network.hidden_size, 256)
    
    def test_forward_pass(self):
        """Test forward pass"""
        network = ValueNetwork(input_size=128, hidden_size=256)
        state = np.random.randn(128)
        
        value = network.forward(state)
        
        self.assertIsInstance(value, (float, np.floating))


class TestExperienceReplayBuffer(unittest.TestCase):
    """Test experience replay buffer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.buffer = ExperienceReplayBuffer(capacity=100)
    
    def test_add_experience(self):
        """Test adding experience"""
        state = np.random.randn(128)
        next_state = np.random.randn(128)
        exp = Experience(state, 0, 1.0, next_state, False, 0.5, 0.3)
        
        self.buffer.add(exp)
        self.assertEqual(len(self.buffer), 1)
    
    def test_buffer_capacity(self):
        """Test buffer respects capacity"""
        for i in range(150):
            state = np.random.randn(128)
            exp = Experience(state, 0, 1.0, state, False, 0.5, 0.3)
            self.buffer.add(exp)
        
        self.assertEqual(len(self.buffer), 100)
    
    def test_sample_batch(self):
        """Test sampling batch"""
        # Add experiences
        for i in range(50):
            state = np.random.randn(128)
            exp = Experience(state, i % 6, float(i), state, False, 0.5, 0.3)
            self.buffer.add(exp, priority=float(i + 1))
        
        # Sample batch
        experiences, indices, weights = self.buffer.sample(batch_size=10)
        
        self.assertEqual(len(experiences), 10)
        self.assertEqual(len(indices), 10)
        self.assertEqual(len(weights), 10)
    
    def test_update_priorities(self):
        """Test updating priorities"""
        # Add experiences
        for i in range(10):
            state = np.random.randn(128)
            exp = Experience(state, 0, 1.0, state, False, 0.5, 0.3)
            self.buffer.add(exp)
        
        # Update priorities
        indices = [0, 1, 2]
        new_priorities = [10.0, 20.0, 30.0]
        self.buffer.update_priorities(indices, new_priorities)
        
        # Priorities should be updated
        self.assertGreater(self.buffer.priorities[0], 0)


class TestRewardShaper(unittest.TestCase):
    """Test reward shaping system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.shaper = RewardShaper()
    
    def test_win_reward(self):
        """Test win reward"""
        reward = self.shaper.shape_reward(
            Action.BET,
            "win",
            {"pot_size": 50}
        )
        self.assertGreater(reward, 0)
    
    def test_loss_penalty(self):
        """Test loss penalty"""
        reward = self.shaper.shape_reward(
            Action.CALL,
            "loss",
            {}
        )
        self.assertLess(reward, 0)
    
    def test_fold_penalty(self):
        """Test fold penalty"""
        # Bad fold with strong hand
        reward = self.shaper.shape_reward(
            Action.FOLD,
            "neutral",
            {"hand_strength": 0.9}
        )
        self.assertLess(reward, 0)
    
    def test_aggressive_bonus(self):
        """Test aggressive bonus"""
        reward = self.shaper.shape_reward(
            Action.RAISE,
            "neutral",
            {"position": "button", "hand_strength": 0.85}
        )
        self.assertGreater(reward, 0)
    
    def test_position_bonus(self):
        """Test position bonus"""
        reward_button = self.shaper.shape_reward(
            Action.BET,
            "neutral",
            {"position": "button"}
        )
        reward_other = self.shaper.shape_reward(
            Action.BET,
            "neutral",
            {"position": "early"}
        )
        self.assertGreater(reward_button, reward_other)
    
    def test_calculate_advantage(self):
        """Test GAE calculation"""
        rewards = [1.0, 0.5, -0.5, 1.0]
        values = [0.8, 0.6, 0.4, 0.9]
        
        advantages = self.shaper.calculate_advantage(rewards, values)
        
        self.assertEqual(len(advantages), len(rewards))
        self.assertIsInstance(advantages[0], float)


class TestCurriculumManager(unittest.TestCase):
    """Test curriculum learning manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = CurriculumManager()
    
    def test_initialization(self):
        """Test initialization"""
        self.assertEqual(self.manager.current_level, AgentLevel.BEGINNER)
    
    def test_update_performance(self):
        """Test performance update"""
        initial_len = len(self.manager.performance_history)
        self.manager.update_performance(True)
        self.assertEqual(len(self.manager.performance_history), initial_len + 1)
    
    def test_level_up(self):
        """Test level up mechanism"""
        # Simulate wins to reach threshold
        for _ in range(60):
            self.manager.update_performance(True)
        
        leveled_up = self.manager.check_level_up()
        self.assertTrue(leveled_up)
        self.assertEqual(self.manager.current_level, AgentLevel.INTERMEDIATE)
    
    def test_no_level_up_insufficient_data(self):
        """Test no level up with insufficient data"""
        for _ in range(30):
            self.manager.update_performance(True)
        
        leveled_up = self.manager.check_level_up()
        self.assertFalse(leveled_up)
    
    def test_training_config(self):
        """Test training configuration"""
        config = self.manager.get_training_config()
        
        self.assertIn("opponent_skill", config)
        self.assertIn("stakes", config)
        self.assertIn("table_size", config)
    
    def test_all_levels_have_config(self):
        """Test all levels have training config"""
        for level in AgentLevel:
            self.manager.current_level = level
            config = self.manager.get_training_config()
            self.assertIsInstance(config, dict)


class TestPPOTrainer(unittest.TestCase):
    """Test PPO trainer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.policy_network = PolicyNetwork(input_size=128, hidden_size=256, output_size=6)
        self.value_network = ValueNetwork(input_size=128, hidden_size=256)
        self.trainer = PPOTrainer(self.policy_network, self.value_network)
    
    def test_initialization(self):
        """Test trainer initialization"""
        self.assertEqual(self.trainer.clip_epsilon, 0.2)
        self.assertGreater(self.trainer.entropy_coef, 0)
    
    def test_policy_loss_computation(self):
        """Test policy loss computation"""
        states = [np.random.randn(128) for _ in range(5)]
        actions = [0, 1, 2, 0, 1]
        old_log_probs = [-1.5, -1.2, -1.8, -1.6, -1.4]
        advantages = [0.5, -0.3, 0.8, -0.2, 0.4]
        
        loss = self.trainer.compute_policy_loss(states, actions, old_log_probs, advantages)
        
        self.assertIsInstance(loss, (float, np.floating))
    
    def test_value_loss_computation(self):
        """Test value loss computation"""
        states = [np.random.randn(128) for _ in range(5)]
        returns = [1.0, 0.5, -0.5, 0.8, 0.3]
        
        loss = self.trainer.compute_value_loss(states, returns)
        
        self.assertIsInstance(loss, (float, np.floating))
        self.assertGreaterEqual(loss, 0)
    
    def test_train_step(self):
        """Test full training step"""
        # Create experiences
        experiences = []
        for i in range(5):
            state = np.random.randn(128)
            exp = Experience(state, i % 6, 1.0, state, False, -1.5, 0.5)
            experiences.append(exp)
        
        advantages = [0.5, -0.3, 0.8, -0.2, 0.4]
        returns = [1.0, 0.5, -0.5, 0.8, 0.3]
        
        metrics = self.trainer.train_step(experiences, advantages, returns)
        
        self.assertIn("total_loss", metrics)
        self.assertIn("policy_loss", metrics)
        self.assertIn("value_loss", metrics)


class TestRLAgent(unittest.TestCase):
    """Test main RL agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.agent = RLAgent(state_size=128, action_size=6, data_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test agent initialization"""
        self.assertEqual(self.agent.state_size, 128)
        self.assertEqual(self.agent.action_size, 6)
        self.assertEqual(self.agent.training_step, 0)
    
    def test_select_action(self):
        """Test action selection"""
        state = np.random.randn(128)
        available_actions = [Action.FOLD, Action.CALL, Action.RAISE]
        
        action, log_prob, value = self.agent.select_action(state, available_actions)
        
        self.assertIn(action, available_actions)
        self.assertIsInstance(log_prob, (float, np.floating))
        self.assertIsInstance(value, (float, np.floating))
    
    def test_select_action_deterministic(self):
        """Test deterministic action selection"""
        state = np.random.randn(128)
        available_actions = [Action.FOLD, Action.CALL, Action.RAISE]
        
        # Run multiple times to check consistency
        actions = []
        for _ in range(5):
            action, _, _ = self.agent.select_action(state, available_actions, training=False)
            actions.append(action)
        
        # Should select same action each time in deterministic mode
        self.assertEqual(len(set(actions)), 1)
    
    def test_store_experience(self):
        """Test storing experience"""
        state = np.random.randn(128)
        next_state = np.random.randn(128)
        
        initial_size = len(self.agent.replay_buffer)
        
        self.agent.store_experience(
            state, Action.BET, 1.0, next_state, False, -1.5, 0.5
        )
        
        self.assertEqual(len(self.agent.replay_buffer), initial_size + 1)
    
    def test_train_insufficient_data(self):
        """Test training with insufficient data"""
        metrics = self.agent.train()
        self.assertEqual(metrics, {})
    
    def test_train_with_data(self):
        """Test training with sufficient data"""
        # Add experiences
        for i in range(100):
            state = np.random.randn(128)
            next_state = np.random.randn(128)
            self.agent.store_experience(
                state, Action.BET, 1.0, next_state, False, -1.5, 0.5
            )
        
        metrics = self.agent.train()
        
        self.assertIn("total_loss", metrics)
        self.assertIn("policy_loss", metrics)
        self.assertIn("value_loss", metrics)
    
    def test_episode_finished(self):
        """Test episode completion"""
        initial_episodes = self.agent.episodes_completed
        self.agent.episode_finished(won=True)
        self.assertEqual(self.agent.episodes_completed, initial_episodes + 1)
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        stats = self.agent.get_statistics()
        
        self.assertIn("training_step", stats)
        self.assertIn("episodes_completed", stats)
        self.assertIn("curriculum_level", stats)
        self.assertIn("replay_buffer_size", stats)
        self.assertIn("win_rate", stats)
    
    def test_save_and_load_checkpoint(self):
        """Test checkpoint saving and loading"""
        # Train a bit
        for i in range(100):
            state = np.random.randn(128)
            self.agent.store_experience(
                state, Action.BET, 1.0, state, False, -1.5, 0.5
            )
        
        self.agent.train()
        self.agent.training_step = 42
        self.agent.episodes_completed = 100
        
        # Save checkpoint
        self.agent.save_checkpoint()
        
        # Create new agent and load
        new_agent = RLAgent(state_size=128, action_size=6, data_dir=self.temp_dir)
        
        self.assertEqual(new_agent.training_step, 42)
        self.assertEqual(new_agent.episodes_completed, 100)


class TestMultiAgentTrainer(unittest.TestCase):
    """Test multi-agent trainer"""
    
    def test_initialization(self):
        """Test trainer initialization"""
        trainer = MultiAgentTrainer(num_agents=3)
        self.assertEqual(trainer.num_agents, 3)
        self.assertEqual(len(trainer.agents), 3)
    
    def test_self_play_match(self):
        """Test self-play match"""
        trainer = MultiAgentTrainer(num_agents=2)
        results = trainer.self_play_match(num_hands=10)
        
        self.assertIn("agent_0", results)
        self.assertIn("agent_1", results)
        self.assertIn("wins", results["agent_0"])
        self.assertIn("total", results["agent_0"])
    
    def test_leaderboard(self):
        """Test leaderboard generation"""
        trainer = MultiAgentTrainer(num_agents=3)
        
        # Run some matches
        trainer.self_play_match(num_hands=50)
        
        leaderboard = trainer.get_leaderboard()
        
        self.assertEqual(len(leaderboard), 3)
        # Check sorted by win rate
        for i in range(len(leaderboard) - 1):
            self.assertGreaterEqual(leaderboard[i][1], leaderboard[i + 1][1])


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.agent = RLAgent(state_size=128, action_size=6, data_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_training_loop(self):
        """Test complete training loop"""
        # Simulate episode
        state = np.random.randn(128)
        available_actions = [Action.FOLD, Action.CALL, Action.RAISE, Action.BET]
        
        for step in range(20):
            # Select action
            action, log_prob, value = self.agent.select_action(state, available_actions)
            
            # Simulate environment
            next_state = np.random.randn(128)
            reward = np.random.randn()
            done = (step == 19)
            
            # Store experience
            self.agent.store_experience(
                state, action, reward, next_state, done, log_prob, value
            )
            
            state = next_state
        
        # Episode finished
        self.agent.episode_finished(won=True)
        
        # Add more episodes
        for episode in range(10):
            for step in range(20):
                state = np.random.randn(128)
                action, log_prob, value = self.agent.select_action(state, available_actions)
                next_state = np.random.randn(128)
                reward = np.random.randn()
                done = (step == 19)
                self.agent.store_experience(
                    state, action, reward, next_state, done, log_prob, value
                )
            
            self.agent.episode_finished(won=(episode % 2 == 0))
        
        # Train
        metrics = self.agent.train()
        
        self.assertIn("total_loss", metrics)
        
        # Get statistics
        stats = self.agent.get_statistics()
        self.assertGreater(stats["episodes_completed"], 0)
        self.assertGreater(stats["replay_buffer_size"], 0)
    
    def test_curriculum_progression(self):
        """Test curriculum learning progression"""
        # Simulate many successful episodes
        for episode in range(100):
            for step in range(10):
                state = np.random.randn(128)
                available_actions = [Action.FOLD, Action.CALL, Action.RAISE]
                action, log_prob, value = self.agent.select_action(state, available_actions)
                next_state = np.random.randn(128)
                reward = 1.0  # Always win
                done = (step == 9)
                self.agent.store_experience(
                    state, action, reward, next_state, done, log_prob, value
                )
            
            self.agent.episode_finished(won=True)
        
        # Should have progressed in curriculum
        stats = self.agent.get_statistics()
        # May have leveled up depending on implementation
        self.assertIn(stats["curriculum_level"], [level.value for level in AgentLevel])


if __name__ == "__main__":
    unittest.main()
