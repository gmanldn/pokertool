"""
Comprehensive tests for HUD suggestions module

Tests real-time hand analysis suggestion generation for HUD overlay.
"""
import pytest
from pokertool.hud_suggestions import (
    HUDSuggestionEngine,
    Suggestion,
    SuggestionType,
    SuggestionPriority
)


class TestHUDSuggestions:
    """Test suite for HUD suggestions"""

    @pytest.fixture
    def engine(self):
        """Create suggestion engine"""
        return HUDSuggestionEngine()

    def test_preflop_strong_position(self, engine):
        """Test preflop suggestion in strong position"""
        suggestions = engine.analyze_situation(
            hole_cards=['As', 'Kh'],
            board_cards=[],
            position='BTN',
            pot_size=10.0,
            to_call=2.0,
            stack_size=100.0
        )

        assert len(suggestions) > 0
        # Should include position-based suggestion
        position_suggestions = [s for s in suggestions if s.type == SuggestionType.POSITION]
        assert len(position_suggestions) > 0

    def test_preflop_3bet_opportunity(self, engine):
        """Test 3-bet suggestion based on opponent stats"""
        opponent_stats = {
            'fold_to_3bet': 70.0,  # High fold rate
            'vpip': 25.0,
            'pfr': 20.0
        }

        suggestions = engine.analyze_situation(
            hole_cards=['Qs', 'Jh'],
            board_cards=[],
            position='BTN',
            pot_size=10.0,
            to_call=3.0,
            stack_size=100.0,
            opponent_stats=opponent_stats
        )

        # Should suggest 3-bet bluff
        bluff_suggestions = [s for s in suggestions if s.type == SuggestionType.BLUFF]
        assert len(bluff_suggestions) > 0
        assert bluff_suggestions[0].priority in [SuggestionPriority.HIGH, SuggestionPriority.CRITICAL]

    def test_low_spr_all_in_suggestion(self, engine):
        """Test all-in suggestion with low SPR"""
        suggestions = engine.analyze_situation(
            hole_cards=['Ah', 'As'],  # Pocket aces
            board_cards=[],
            position='BTN',
            pot_size=50.0,
            to_call=10.0,
            stack_size=100.0  # SPR = 100/(50+10) = 1.67
        )

        # Should suggest all-in with low SPR and strong hand
        value_suggestions = [s for s in suggestions if s.type == SuggestionType.VALUE]
        assert any('SPR' in s.message or 'all-in' in s.message.lower() for s in value_suggestions)

    def test_pot_odds_calculation(self, engine):
        """Test pot odds suggestion"""
        suggestions = engine.analyze_situation(
            hole_cards=['9s', '8s'],
            board_cards=['7h', '6c', '2d'],  # Straight draw
            position='BTN',
            pot_size=50.0,
            to_call=15.0,  # 15/(50+15) = 23% equity needed
            stack_size=100.0
        )

        pot_odds_suggestions = [s for s in suggestions if s.type == SuggestionType.POT_ODDS]
        assert len(pot_odds_suggestions) > 0
        assert 'odds' in pot_odds_suggestions[0].message.lower()

    def test_fold_equity_suggestion(self, engine):
        """Test fold equity suggestion on flop"""
        opponent_stats = {
            'fold_to_cbet': 55.0,  # High fold rate
            'vpip': 30.0
        }

        suggestions = engine.analyze_situation(
            hole_cards=['As', 'Kh'],
            board_cards=['9s', '8c', '2d'],  # Flop
            position='BTN',
            pot_size=20.0,
            to_call=0.0,
            stack_size=100.0,
            opponent_stats=opponent_stats
        )

        fold_equity_suggestions = [s for s in suggestions if s.type == SuggestionType.FOLD_EQUITY]
        assert len(fold_equity_suggestions) > 0

    def test_draw_heavy_board(self, engine):
        """Test suggestion on draw-heavy board"""
        suggestions = engine.analyze_situation(
            hole_cards=['As', 'Ah'],
            board_cards=['Ks', 'Qs', 'Js'],  # Flush draw + straight possibilities
            position='BTN',
            pot_size=30.0,
            to_call=0.0,
            stack_size=100.0
        )

        # Should identify draw-heavy board
        postflop_suggestions = [s for s in suggestions if s.type == SuggestionType.POSTFLOP]
        draw_suggestions = [s for s in postflop_suggestions if 'draw' in s.message.lower()]
        assert len(draw_suggestions) > 0

    def test_suggestion_confidence_filtering(self, engine):
        """Test that low confidence suggestions are filtered"""
        engine.min_confidence = 0.8  # High threshold

        suggestions = engine.analyze_situation(
            hole_cards=['7s', '2h'],  # Weak hand
            board_cards=[],
            position='UTG',  # Early position
            pot_size=5.0,
            to_call=0.0,
            stack_size=100.0
        )

        # All suggestions should meet confidence threshold
        for suggestion in suggestions:
            assert suggestion.confidence >= engine.min_confidence

    def test_max_suggestions_limit(self, engine):
        """Test that suggestion count is limited"""
        engine.max_suggestions = 2

        suggestions = engine.analyze_situation(
            hole_cards=['As', 'Kh'],
            board_cards=['Qs', 'Jh', '9s'],
            position='BTN',
            pot_size=30.0,
            to_call=10.0,
            stack_size=100.0,
            opponent_stats={'fold_to_cbet': 60.0, 'vpip': 35.0}
        )

        assert len(suggestions) <= engine.max_suggestions

    def test_suggestion_priority_sorting(self, engine):
        """Test that suggestions are sorted by priority"""
        suggestions = engine.analyze_situation(
            hole_cards=['As', 'Ah'],
            board_cards=['Ks', 'Qh', 'Jd'],
            position='BTN',
            pot_size=50.0,
            to_call=20.0,
            stack_size=100.0,
            opponent_stats={'fold_to_cbet': 65.0, 'vpip': 40.0}
        )

        if len(suggestions) > 1:
            # Check that priorities are in descending order
            priority_scores = [engine._priority_score(s.priority) for s in suggestions]
            assert priority_scores == sorted(priority_scores, reverse=True) or \
                   all(suggestions[i].confidence >= suggestions[i+1].confidence
                       for i in range(len(suggestions)-1)
                       if priority_scores[i] == priority_scores[i+1])

    def test_preflop_hand_strength_evaluation(self, engine):
        """Test preflop hand strength calculation"""
        # Premium pairs
        assert engine._evaluate_preflop_strength(['As', 'Ah']) > 0.8

        # Strong broadway
        assert engine._evaluate_preflop_strength(['As', 'Ks']) > 0.7

        # Medium pairs (pair bonus makes this stronger)
        assert engine._evaluate_preflop_strength(['9s', '9h']) > 0.7

        # Weak hands
        assert engine._evaluate_preflop_strength(['7s', '2h']) < 0.4

        # Suited connectors get bonus
        suited_strength = engine._evaluate_preflop_strength(['9s', '8s'])
        offsuit_strength = engine._evaluate_preflop_strength(['9h', '8c'])
        assert suited_strength > offsuit_strength

    def test_board_texture_analysis(self, engine):
        """Test board texture analysis"""
        # Flush draw board
        flush_board = engine._analyze_board_texture(['As', 'Ks', 'Qs'])
        assert flush_board['flush_draw'] is True
        assert flush_board['is_draw_heavy'] is True

        # Straight draw board
        straight_board = engine._analyze_board_texture(['9h', '8c', '6d'])
        assert straight_board['straight_draw'] is True

        # Rainbow board
        rainbow_board = engine._analyze_board_texture(['Ah', '7c', '2d'])
        assert rainbow_board['flush_draw'] is False

    def test_suggestion_formatting(self, engine):
        """Test HUD formatting of suggestions"""
        suggestion = Suggestion(
            type=SuggestionType.BLUFF,
            priority=SuggestionPriority.HIGH,
            message="Consider bluffing here",
            confidence=0.85,
            reasoning="Opponent shows weakness",
            metadata={'fold_rate': 65.0}
        )

        formatted = engine.format_suggestion_for_hud(suggestion)

        assert 'message' in formatted
        assert 'reasoning' in formatted
        assert 'priority' in formatted
        assert 'color' in formatted
        assert 'confidence' in formatted
        assert formatted['confidence'] == "85%"
        assert formatted['priority'] == 'high'

    def test_empty_board_cards(self, engine):
        """Test handling of empty board (preflop)"""
        suggestions = engine.analyze_situation(
            hole_cards=['As', 'Kh'],
            board_cards=[],
            position='BTN',
            pot_size=10.0,
            to_call=2.0,
            stack_size=100.0
        )

        assert suggestions is not None
        assert isinstance(suggestions, list)

    def test_invalid_hole_cards(self, engine):
        """Test handling of invalid hole cards"""
        # Should not crash with invalid cards
        strength = engine._evaluate_preflop_strength(['XX', 'YY'])
        assert strength >= 0.0  # Returns small non-zero value due to calculation

        strength = engine._evaluate_preflop_strength([])
        assert strength == 0.0

    def test_similar_situation_analysis(self, engine):
        """Test finding similar situations"""
        action_history = [
            {'action': 'bet', 'amount': 10},
            {'action': 'call', 'amount': 10}
        ]

        similar = engine._find_similar_situations(
            ['As', 'Kh'],
            ['Qs', 'Jh', '9s'],
            action_history
        )

        # Mock implementation should return data with history
        assert similar is not None
        assert 'action' in similar
        assert 'confidence' in similar

    def test_no_opponent_stats(self, engine):
        """Test suggestions without opponent stats"""
        suggestions = engine.analyze_situation(
            hole_cards=['As', 'Kh'],
            board_cards=['Qs', 'Jh', '9s'],
            position='BTN',
            pot_size=20.0,
            to_call=5.0,
            stack_size=100.0,
            opponent_stats=None
        )

        # Should still generate some suggestions
        assert len(suggestions) > 0

    def test_action_history_integration(self, engine):
        """Test integration with action history"""
        action_history = [
            {'player': 'villain', 'action': 'bet', 'amount': 10},
            {'player': 'hero', 'action': 'call', 'amount': 10}
        ]

        suggestions = engine.analyze_situation(
            hole_cards=['As', 'Ah'],
            board_cards=['Ks', 'Qh', 'Jd'],
            position='BTN',
            pot_size=30.0,
            to_call=0.0,
            stack_size=100.0,
            action_history=action_history
        )

        assert suggestions is not None

    def test_turn_and_river_suggestions(self, engine):
        """Test suggestions on turn and river"""
        # Turn (4 board cards)
        turn_suggestions = engine.analyze_situation(
            hole_cards=['As', 'Ah'],
            board_cards=['Ks', 'Qh', 'Jd', '9c'],
            position='BTN',
            pot_size=40.0,
            to_call=15.0,
            stack_size=100.0
        )
        assert turn_suggestions is not None

        # River (5 board cards)
        river_suggestions = engine.analyze_situation(
            hole_cards=['As', 'Ah'],
            board_cards=['Ks', 'Qh', 'Jd', '9c', '2h'],
            position='BTN',
            pot_size=50.0,
            to_call=20.0,
            stack_size=100.0
        )
        assert river_suggestions is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
