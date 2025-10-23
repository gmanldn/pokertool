"""
Comprehensive tests for AI-powered opponent profiling

Tests the OpponentProfiler class with LangChain integration,
including profile generation, fallback behavior, and API endpoints.
"""
import pytest
from unittest.mock import Mock, patch
from pokertool.opponent_profiler import (
    OpponentProfiler,
    OpponentStats,
    PlayerType,
    LANGCHAIN_AVAILABLE
)


class TestOpponentProfilerAI:
    """Test suite for AI-powered opponent profiling"""

    @pytest.fixture
    def profiler(self):
        """Create profiler instance"""
        return OpponentProfiler()

    @pytest.fixture
    def lag_stats(self):
        """LAG player stats"""
        return OpponentStats(
            vpip=45.0,
            pfr=32.0,
            threebet=12.0,
            fold_to_cbet=35.0,
            fold_to_threebet=45.0,
            aggression=2.8,
            hands_played=150
        )

    @pytest.fixture
    def tag_stats(self):
        """TAG player stats"""
        return OpponentStats(
            vpip=18.0,
            pfr=16.0,
            threebet=6.0,
            fold_to_cbet=45.0,
            fold_to_threebet=65.0,
            aggression=2.2,
            hands_played=200
        )

    @pytest.fixture
    def lp_stats(self):
        """Loose-Passive player stats"""
        return OpponentStats(
            vpip=42.0,
            pfr=8.0,
            threebet=2.0,
            fold_to_cbet=28.0,
            fold_to_threebet=35.0,
            aggression=0.8,
            hands_played=80
        )

    def test_generate_ai_profile_lag_with_mock(self, profiler, lag_stats):
        """Test AI profile generation for LAG player with mock LLM"""
        profile = profiler.generate_ai_profile(lag_stats, use_mock=True)

        assert profile is not None
        assert 'playing_style' in profile
        assert 'tendencies' in profile
        assert 'exploitation_strategy' in profile
        assert 'confidence' in profile
        assert 'player_type' in profile
        assert 'stats' in profile

        # Check player type
        assert profile['player_type'] == PlayerType.LAG.value

        # Check confidence based on sample size
        assert profile['confidence'] == 'HIGH'  # 150 hands

        # Check stats are included
        assert profile['stats']['vpip'] == 45.0
        assert profile['stats']['pfr'] == 32.0
        assert profile['stats']['hands_played'] == 150

    def test_generate_ai_profile_tag(self, profiler, tag_stats):
        """Test AI profile generation for TAG player"""
        profile = profiler.generate_ai_profile(tag_stats, use_mock=True)

        assert profile['player_type'] == PlayerType.TAG.value
        assert profile['confidence'] == 'HIGH'  # 200 hands
        assert len(profile['tendencies']) > 0
        assert len(profile['exploitation_strategy']) > 0

    def test_generate_ai_profile_lp(self, profiler, lp_stats):
        """Test AI profile generation for Loose-Passive player"""
        profile = profiler.generate_ai_profile(lp_stats, use_mock=True)

        assert profile['player_type'] == PlayerType.LP.value
        assert profile['confidence'] == 'MEDIUM'  # 80 hands
        assert 'passive' in profile['playing_style'].lower() or 'Loose-Passive' in profile['playing_style']

    def test_generate_ai_profile_with_hand_history(self, profiler, lag_stats):
        """Test profile generation with hand history context"""
        hand_history = [
            {'action': 'raise', 'cards': 'AsKh'},
            {'action': '3bet', 'cards': 'QsQd'},
            {'action': 'call', 'cards': '9s8s'},
            {'action': 'fold', 'cards': 'AcJc'},
            {'action': 'raise', 'cards': 'KdKc'}
        ]

        profile = profiler.generate_ai_profile(
            lag_stats,
            hand_history=hand_history,
            use_mock=True
        )

        assert profile is not None
        assert profile['player_type'] == PlayerType.LAG.value

    def test_confidence_levels(self, profiler):
        """Test confidence levels based on sample size"""
        # Low confidence - < 50 hands
        low_sample = OpponentStats(
            vpip=25.0, pfr=20.0, threebet=5.0,
            fold_to_cbet=40.0, fold_to_threebet=50.0,
            aggression=1.5, hands_played=30
        )
        profile_low = profiler.generate_ai_profile(low_sample, use_mock=True)
        assert profile_low['confidence'] == 'LOW'

        # Medium confidence - 50-99 hands
        medium_sample = OpponentStats(
            vpip=25.0, pfr=20.0, threebet=5.0,
            fold_to_cbet=40.0, fold_to_threebet=50.0,
            aggression=1.5, hands_played=75
        )
        profile_medium = profiler.generate_ai_profile(medium_sample, use_mock=True)
        assert profile_medium['confidence'] == 'MEDIUM'

        # High confidence - >= 100 hands
        high_sample = OpponentStats(
            vpip=25.0, pfr=20.0, threebet=5.0,
            fold_to_cbet=40.0, fold_to_threebet=50.0,
            aggression=1.5, hands_played=120
        )
        profile_high = profiler.generate_ai_profile(high_sample, use_mock=True)
        assert profile_high['confidence'] == 'HIGH'

    def test_fallback_profile_generation(self, profiler, lag_stats):
        """Test fallback profile generation when LangChain unavailable"""
        profile = profiler._generate_fallback_profile(lag_stats)

        assert profile is not None
        assert 'playing_style' in profile
        assert 'tendencies' in profile
        assert 'exploitation_strategy' in profile
        assert profile['player_type'] == PlayerType.LAG.value

        # Check tendencies are populated
        assert len(profile['tendencies']) >= 3

        # Check exploitation strategy
        assert len(profile['exploitation_strategy']) > 0

    def test_fallback_all_player_types(self, profiler):
        """Test fallback profiles for all player types"""
        player_types_stats = [
            (PlayerType.LAG, OpponentStats(45.0, 32.0, 12.0, 35.0, 45.0, 2.8, 100)),
            (PlayerType.TAG, OpponentStats(18.0, 16.0, 6.0, 45.0, 65.0, 2.2, 100)),
            (PlayerType.LP, OpponentStats(42.0, 8.0, 2.0, 28.0, 35.0, 0.8, 100)),
            (PlayerType.TP, OpponentStats(15.0, 10.0, 3.0, 55.0, 70.0, 1.2, 100)),
            (PlayerType.BALANCED, OpponentStats(28.0, 22.0, 8.0, 42.0, 55.0, 2.1, 100)),
        ]

        for expected_type, stats in player_types_stats:
            profile = profiler._generate_fallback_profile(stats)
            assert profile['player_type'] == expected_type.value
            assert len(profile['exploitation_strategy']) > 0

    def test_parse_profile_response(self, profiler, lag_stats):
        """Test parsing of LLM response"""
        response = """PLAYING STYLE:
Loose-Aggressive player who plays 45.0% of hands with 32.0% preflop raises.

KEY TENDENCIES:
- Moderate aggression with 2.8 aggression factor
- Folds to c-bets 35.0% of the time
- 3-bets 12.0% when facing raises

EXPLOITATION STRATEGY:
Value bet thinly when they show weakness. Be prepared to fold to their aggression.

CONFIDENCE:
HIGH (based on 150 hands)
"""

        profile = profiler._parse_profile_response(response, lag_stats)

        assert profile['playing_style'] == "Loose-Aggressive player who plays 45.0% of hands with 32.0% preflop raises."
        assert len(profile['tendencies']) == 3
        assert profile['confidence'] == 'HIGH'
        assert 'Value bet' in profile['exploitation_strategy']

    def test_parse_response_with_missing_sections(self, profiler, lag_stats):
        """Test parsing response with missing sections"""
        response = """PLAYING STYLE:
LAG player.

CONFIDENCE:
MEDIUM
"""

        profile = profiler._parse_profile_response(response, lag_stats)

        assert profile['playing_style'] == "LAG player."
        assert profile['tendencies'] == []  # Empty list for missing section
        assert profile['exploitation_strategy'] == ''  # Empty string
        assert profile['confidence'] == 'MEDIUM'

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not available")
    def test_langchain_integration(self, profiler, lag_stats):
        """Test actual LangChain integration if available"""
        # This test uses FakeListLLM which is always available if LangChain is
        profile = profiler.generate_ai_profile(lag_stats, use_mock=True)

        assert profile is not None
        assert profile['player_type'] == PlayerType.LAG.value

    def test_edge_case_extreme_stats(self, profiler):
        """Test with extreme statistics"""
        # Ultra-tight player
        ultra_tight = OpponentStats(
            vpip=5.0, pfr=4.0, threebet=1.0,
            fold_to_cbet=75.0, fold_to_threebet=85.0,
            aggression=0.5, hands_played=50
        )
        profile = profiler.generate_ai_profile(ultra_tight, use_mock=True)
        assert profile is not None

        # Ultra-loose player
        ultra_loose = OpponentStats(
            vpip=75.0, pfr=45.0, threebet=25.0,
            fold_to_cbet=15.0, fold_to_threebet=25.0,
            aggression=4.5, hands_played=50
        )
        profile = profiler.generate_ai_profile(ultra_loose, use_mock=True)
        assert profile is not None

    def test_empty_hand_history(self, profiler, lag_stats):
        """Test with empty hand history"""
        profile = profiler.generate_ai_profile(lag_stats, hand_history=[], use_mock=True)
        assert profile is not None

    def test_profile_structure(self, profiler, lag_stats):
        """Test that profile has all required fields"""
        profile = profiler.generate_ai_profile(lag_stats, use_mock=True)

        required_fields = [
            'playing_style',
            'tendencies',
            'exploitation_strategy',
            'confidence',
            'player_type',
            'stats'
        ]

        for field in required_fields:
            assert field in profile, f"Missing required field: {field}"

        # Check types
        assert isinstance(profile['playing_style'], str)
        assert isinstance(profile['tendencies'], list)
        assert isinstance(profile['exploitation_strategy'], str)
        assert isinstance(profile['confidence'], str)
        assert isinstance(profile['player_type'], str)
        assert isinstance(profile['stats'], dict)

    def test_stats_preservation(self, profiler, lag_stats):
        """Test that original stats are preserved in profile"""
        profile = profiler.generate_ai_profile(lag_stats, use_mock=True)

        stats = profile['stats']
        assert stats['vpip'] == lag_stats.vpip
        assert stats['pfr'] == lag_stats.pfr
        assert stats['threebet'] == lag_stats.threebet
        assert stats['fold_to_cbet'] == lag_stats.fold_to_cbet
        assert stats['fold_to_threebet'] == lag_stats.fold_to_threebet
        assert stats['aggression'] == lag_stats.aggression
        assert stats['hands_played'] == lag_stats.hands_played


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
