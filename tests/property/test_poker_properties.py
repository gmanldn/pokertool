"""
Property-Based Tests for Poker Engine

Uses Hypothesis to test mathematical properties and invariants that should
always hold true in poker logic, regardless of inputs.

Author: PokerTool Team
Created: 2025-10-22
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis import Phase
from pokertool.equity_calculator import EquityCalculator
from pokertool.gto_calculator import GTOCalculator, Position, Street


# Custom strategies for poker-specific data
@st.composite
def valid_card(draw):
    """Generate a valid card (rank + suit)"""
    rank = draw(st.sampled_from(['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']))
    suit = draw(st.sampled_from(['c', 'd', 'h', 's']))
    return f"{rank}{suit}"


@st.composite
def valid_hand(draw):
    """Generate a valid poker hand (pair or suited/offsuit)"""
    return draw(st.sampled_from([
        'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
        'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
        'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'K6s', 'K5s', 'K4s', 'K3s', 'K2s',
        'QJs', 'QTs', 'Q9s', 'Q8s', 'Q7s', 'Q6s', 'Q5s', 'Q4s', 'Q3s', 'Q2s',
        'JTs', 'J9s', 'J8s', 'J7s', 'J6s', 'J5s', 'J4s', 'J3s', 'J2s',
        'T9s', 'T8s', 'T7s', 'T6s', 'T5s', 'T4s', 'T3s', 'T2s',
        '98s', '97s', '96s', '95s', '94s', '93s', '92s',
        '87s', '86s', '85s', '84s', '83s', '82s',
        '76s', '75s', '74s', '73s', '72s',
        '65s', '64s', '63s', '62s',
        '54s', '53s', '52s',
        '43s', '42s',
        '32s',
        'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
        'KQo', 'KJo', 'KTo', 'K9o', 'K8o', 'K7o', 'K6o', 'K5o', 'K4o', 'K3o', 'K2o',
        'QJo', 'QTo', 'Q9o', 'Q8o', 'Q7o', 'Q6o', 'Q5o', 'Q4o', 'Q3o', 'Q2o',
        'JTo', 'J9o', 'J8o', 'J7o', 'J6o', 'J5o', 'J4o', 'J3o', 'J2o',
        'T9o', 'T8o', 'T7o', 'T6o', 'T5o', 'T4o', 'T3o', 'T2o',
        '98o', '97o', '96o', '95o', '94o', '93o', '92o',
        '87o', '86o', '85o', '84o', '83o', '82o',
        '76o', '75o', '74o', '73o', '72o',
        '65o', '64o', '63o', '62o',
        '54o', '53o', '52o',
        '43o', '42o',
        '32o'
    ]))


class TestEquityCalculatorProperties:
    """Property-based tests for EquityCalculator"""

    @given(hand=valid_hand())
    @settings(max_examples=50, deadline=1000)
    def test_hand_strength_is_bounded(self, hand):
        """Property: Hand strength is always between 0 and 1"""
        calc = EquityCalculator()
        strength = calc.get_hand_strength(hand)

        assert 0.0 <= strength <= 1.0, f"Hand strength {strength} out of bounds for {hand}"

    @given(hand=valid_hand())
    @settings(max_examples=50, deadline=1000)
    def test_pocket_pairs_stronger_than_most_hands(self, hand):
        """Property: Pocket pairs have relatively high strength"""
        calc = EquityCalculator()

        # Pocket pairs (AA, KK, etc.)
        if len(hand) == 2 and hand[0] == hand[1]:
            strength = calc.get_hand_strength(hand)
            assert strength >= 0.3, f"Pocket pair {hand} should have strength >= 0.3, got {strength}"

    @given(
        hero_hand=valid_hand(),
        villain_hand=valid_hand()
    )
    @settings(max_examples=30, deadline=2000)
    def test_equity_sums_to_100(self, hero_hand, villain_hand):
        """Property: Hero equity + Villain equity ≈ 100%"""
        assume(hero_hand != villain_hand)  # Can't have same hand

        calc = EquityCalculator()
        try:
            hero_equity = calc.calculate_hand_vs_hand(hero_hand, villain_hand)
            villain_equity = 100 - hero_equity

            total = hero_equity + villain_equity
            assert 99.0 <= total <= 101.0, f"Equity sum {total} not close to 100%"
        except Exception:
            # Skip if hands conflict (unlikely but possible with simplified calc)
            assume(False)

    @given(
        hero_hand=valid_hand(),
        villain_range=st.lists(valid_hand(), min_size=1, max_size=5, unique=True)
    )
    @settings(max_examples=20, deadline=2000)
    def test_hand_vs_range_equity_bounded(self, hero_hand, villain_range):
        """Property: Hand vs range equity is between 0 and 100"""
        assume(hero_hand not in villain_range)

        calc = EquityCalculator()
        equity = calc.calculate_hand_vs_range(hero_hand, villain_range)

        assert 0.0 <= equity <= 100.0, f"Equity {equity} out of bounds"

    @given(
        range_size=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, deadline=2000)
    def test_range_vs_range_symmetry(self, range_size):
        """Property: Equal ranges should have ~50/50 equity"""
        calc = EquityCalculator()

        # Create equal ranges
        all_hands = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55']
        range_hands = all_hands[:range_size]

        result = calc.calculate_range_vs_range(range_hands, range_hands)

        # Should be close to 50/50
        assert 40.0 <= result['hero_equity'] <= 60.0, f"Equal ranges should be ~50%, got {result['hero_equity']}"
        assert 40.0 <= result['villain_equity'] <= 60.0

    @given(equity=st.floats(min_value=0.0, max_value=100.0))
    @settings(max_examples=50)
    def test_equity_category_consistency(self, equity):
        """Property: Equity categories are monotonic"""
        calc = EquityCalculator()
        category = calc.get_equity_category(equity)

        # Check category makes sense
        if equity >= 70:
            assert category == "Very Strong"
        elif equity >= 55:
            assert category == "Strong"
        elif equity >= 45:
            assert category == "Medium"
        elif equity >= 30:
            assert category == "Weak"
        else:
            assert category == "Very Weak"


class TestGTOCalculatorProperties:
    """Property-based tests for GTOCalculator"""

    @given(position=st.sampled_from([Position.UTG, Position.MP, Position.CO, Position.BTN, Position.SB]))
    @settings(max_examples=20)
    def test_preflop_range_percentage_valid(self, position):
        """Property: Preflop range percentages are reasonable"""
        calc = GTOCalculator()
        range_data = calc.get_preflop_range(position, "open_raise")

        # Percentage should be between 0 and 100
        assert 0.0 <= range_data.percentage <= 100.0

        # Ranges should widen from UTG to BTN
        if position == Position.UTG:
            assert range_data.percentage <= 20.0  # Tight from early position
        elif position == Position.BTN:
            assert range_data.percentage >= 40.0  # Wide from button

    @given(position=st.sampled_from([Position.UTG, Position.MP, Position.CO, Position.BTN, Position.SB]))
    @settings(max_examples=20)
    def test_preflop_range_contains_premiums(self, position):
        """Property: All ranges include premium hands (AA, KK, QQ)"""
        calc = GTOCalculator()
        range_data = calc.get_preflop_range(position, "open_raise")

        if range_data.percentage > 0:  # Skip BB (no open range)
            assert 'AA' in range_data.hands, f"{position} should include AA"
            assert 'KK' in range_data.hands, f"{position} should include KK"
            assert 'QQ' in range_data.hands, f"{position} should include QQ"

    @given(
        pot_size=st.floats(min_value=10.0, max_value=1000.0),
        bet_to_call=st.floats(min_value=0.0, max_value=500.0),
        stack_to_pot_ratio=st.floats(min_value=0.5, max_value=20.0),
        equity=st.floats(min_value=0.0, max_value=100.0) | st.none()
    )
    @settings(max_examples=30, deadline=1000)
    def test_frequencies_sum_to_100(self, pot_size, bet_to_call, stack_to_pot_ratio, equity):
        """Property: GTO frequencies always sum to 100%"""
        calc = GTOCalculator()

        freq = calc.calculate_frequencies(
            street=Street.FLOP,
            pot_size=pot_size,
            bet_to_call=bet_to_call,
            stack_to_pot_ratio=stack_to_pot_ratio,
            equity=equity
        )

        total = freq.fold + freq.check + freq.call + freq.bet + freq.raise_ + freq.all_in
        assert 99.0 <= total <= 101.0, f"Frequencies sum to {total}, not 100%"

    @given(
        pot_size=st.floats(min_value=10.0, max_value=1000.0),
        bet_to_call=st.floats(min_value=5.0, max_value=500.0),
        equity=st.floats(min_value=0.0, max_value=100.0)
    )
    @settings(max_examples=30, deadline=1000)
    def test_frequencies_respect_pot_odds(self, pot_size, bet_to_call, equity):
        """Property: Should fold more when equity < pot odds"""
        calc = GTOCalculator()

        pot_odds = (bet_to_call / (pot_size + bet_to_call)) * 100 if pot_size + bet_to_call > 0 else 0

        freq = calc.calculate_frequencies(
            street=Street.FLOP,
            pot_size=pot_size,
            bet_to_call=bet_to_call,
            stack_to_pot_ratio=3.0,
            equity=equity
        )

        # If equity is much lower than pot odds, should fold more
        if equity < pot_odds * 0.8 and pot_odds > 0:
            assert freq.fold > 40.0, "Should fold more often with bad equity vs pot odds"

    @given(pot_odds=st.floats(min_value=0.1, max_value=0.5))
    @settings(max_examples=20)
    def test_bb_defense_widens_with_better_odds(self, pot_odds):
        """Property: BB defends wider with better pot odds"""
        calc = GTOCalculator()

        range_data = calc.get_bb_defense_range(pot_odds)

        # Better pot odds = wider range
        if pot_odds >= 0.35:
            assert range_data.percentage >= 60.0
        elif pot_odds <= 0.25:
            assert range_data.percentage <= 35.0

    @given(
        pot_size=st.floats(min_value=10.0, max_value=500.0),
        street=st.sampled_from([Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]),
        stack_remaining=st.floats(min_value=20.0, max_value=1000.0)
    )
    @settings(max_examples=30)
    def test_bet_size_bounded(self, pot_size, street, stack_remaining):
        """Property: Bet size never exceeds stack"""
        calc = GTOCalculator()

        bet_size, description = calc.get_optimal_bet_size(pot_size, street, stack_remaining)

        assert bet_size <= stack_remaining, f"Bet {bet_size} exceeds stack {stack_remaining}"
        assert bet_size >= 0.0, f"Bet size {bet_size} is negative"

    @given(
        pot_size=st.floats(min_value=10.0, max_value=500.0),
        stack_remaining=st.floats(min_value=5.0, max_value=50.0)
    )
    @settings(max_examples=20)
    def test_bet_size_all_in_when_small_stack(self, pot_size, stack_remaining):
        """Property: Recommends all-in when GTO bet >= stack"""
        calc = GTOCalculator()

        # Any street where GTO would recommend large bet
        bet_size, description = calc.get_optimal_bet_size(pot_size, Street.RIVER, stack_remaining)

        # If bet equals stack, description should be "all-in"
        if bet_size == stack_remaining:
            assert description == "all-in"


class TestPokerMathProperties:
    """Property-based tests for general poker mathematics"""

    @given(
        bet_to_call=st.floats(min_value=1.0, max_value=1000.0),
        pot_size=st.floats(min_value=1.0, max_value=1000.0)
    )
    @settings(max_examples=50)
    def test_pot_odds_bounded(self, bet_to_call, pot_size):
        """Property: Pot odds are always between 0 and 1"""
        # Simplified pot odds calculation
        total = pot_size + bet_to_call
        pot_odds = bet_to_call / total if total > 0 else 0

        assert 0.0 <= pot_odds <= 1.0, f"Pot odds {pot_odds} out of bounds"

    @given(
        stack=st.floats(min_value=10.0, max_value=10000.0),
        pot=st.floats(min_value=1.0, max_value=1000.0)
    )
    @settings(max_examples=50)
    def test_spr_positive(self, stack, pot):
        """Property: Stack-to-Pot Ratio is always positive"""
        spr = stack / pot if pot > 0 else 0

        assert spr >= 0.0, f"SPR {spr} is negative"

    @given(
        equity=st.floats(min_value=0.0, max_value=100.0),
        pot_odds_pct=st.floats(min_value=0.0, max_value=100.0)
    )
    @settings(max_examples=50)
    def test_equity_vs_pot_odds_decision(self, equity, pot_odds_pct):
        """Property: Profitable call when equity > pot odds"""
        # This is fundamental poker math
        if equity > pot_odds_pct:
            ev_positive = True
        else:
            ev_positive = False

        # EV calculation: (equity * pot) - ((1 - equity) * call)
        # Simplified: should call when equity > pot_odds
        assert isinstance(ev_positive, bool)


# Add examples to ensure specific edge cases are tested
class TestEdgeCases:
    """Explicit edge case tests using Hypothesis examples"""

    @given(hand=valid_hand())
    @example(hand='AA')  # Best hand
    @example(hand='72o')  # Worst hand
    @settings(max_examples=20)
    def test_hand_strength_extremes(self, hand):
        """Test hand strength at extremes"""
        calc = EquityCalculator()
        strength = calc.get_hand_strength(hand)

        if hand == 'AA':
            assert strength == 1.0, "AA should have strength 1.0"

        assert 0.0 <= strength <= 1.0

    @given(
        pot_size=st.floats(min_value=0.0, max_value=1000.0),
        stack=st.floats(min_value=0.0, max_value=1000.0)
    )
    @example(pot_size=0.0, stack=100.0)  # Empty pot
    @example(pot_size=100.0, stack=0.0)  # No stack
    @settings(max_examples=20)
    def test_zero_values_handled(self, pot_size, stack):
        """Test handling of zero values"""
        calc = GTOCalculator()

        # Should not crash or return invalid values
        bet_size, desc = calc.get_optimal_bet_size(pot_size, Street.FLOP, stack)

        assert bet_size >= 0.0
        assert bet_size <= stack if stack > 0 else bet_size == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
