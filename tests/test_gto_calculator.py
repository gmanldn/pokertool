"""
Unit Tests for GTO Calculator

Tests GTO preflop ranges, action frequencies, and optimal bet sizing.

Author: PokerTool Team
Created: 2025-10-22
"""

import pytest
from pokertool.gto_calculator import GTOCalculator, Position, Street, GTOFrequencies, GTORange


class TestGTOCalculator:
    """Test suite for GTOCalculator"""

    @pytest.fixture
    def calc(self):
        """Create GTOCalculator instance"""
        return GTOCalculator()

    # Preflop Range Tests

    def test_preflop_range_utg(self, calc):
        """Test UTG opening range is tight (15%)"""
        range_data = calc.get_preflop_range(Position.UTG, "open_raise")
        assert range_data.percentage == 15.0
        assert 'AA' in range_data.hands
        assert 'KK' in range_data.hands
        assert 'AKs' in range_data.hands

    def test_preflop_range_btn(self, calc):
        """Test BTN opening range is wide (48%)"""
        range_data = calc.get_preflop_range(Position.BTN, "open_raise")
        assert range_data.percentage == 48.0
        assert len(range_data.hands) > 20
        assert 'AA' in range_data.hands
        assert '22' in range_data.hands
        assert 'A2s' in range_data.hands

    def test_preflop_range_co_wider_than_mp(self, calc):
        """Test CO range is wider than MP range"""
        co_range = calc.get_preflop_range(Position.CO, "open_raise")
        mp_range = calc.get_preflop_range(Position.MP, "open_raise")
        assert co_range.percentage > mp_range.percentage
        assert len(co_range.hands) > len(mp_range.hands)

    def test_preflop_range_btn_wider_than_co(self, calc):
        """Test BTN range is wider than CO range"""
        btn_range = calc.get_preflop_range(Position.BTN, "open_raise")
        co_range = calc.get_preflop_range(Position.CO, "open_raise")
        assert btn_range.percentage > co_range.percentage
        assert len(btn_range.hands) > len(co_range.hands)

    def test_preflop_range_bb_empty(self, calc):
        """Test BB has no open_raise range (defends based on odds)"""
        range_data = calc.get_preflop_range(Position.BB, "open_raise")
        assert range_data.percentage == 0.0
        assert len(range_data.hands) == 0

    def test_preflop_range_unknown_action(self, calc):
        """Test unknown action returns empty range"""
        range_data = calc.get_preflop_range(Position.BTN, "unknown_action")
        assert range_data.percentage == 0.0
        assert len(range_data.hands) == 0

    # Frequency Calculation Tests - Preflop

    def test_frequencies_preflop_unopened(self, calc):
        """Test preflop frequencies in unopened pot"""
        freq = calc.calculate_frequencies(
            street=Street.PREFLOP,
            pot_size=10,
            bet_to_call=0,
            stack_to_pot_ratio=10.0
        )
        assert freq.fold > 50.0  # Most hands fold
        assert freq.raise_ > 20.0  # Some hands raise
        assert abs((freq.fold + freq.call + freq.raise_) - 100.0) < 0.1

    def test_frequencies_preflop_small_raise(self, calc):
        """Test preflop frequencies facing small raise"""
        freq = calc.calculate_frequencies(
            street=Street.PREFLOP,
            pot_size=10,
            bet_to_call=4,  # 40% pot
            stack_to_pot_ratio=10.0
        )
        assert freq.fold > 30.0
        assert freq.call > 20.0
        assert freq.raise_ > 15.0
        assert abs((freq.fold + freq.call + freq.raise_) - 100.0) < 0.1

    def test_frequencies_preflop_large_raise(self, calc):
        """Test preflop frequencies facing large raise"""
        freq = calc.calculate_frequencies(
            street=Street.PREFLOP,
            pot_size=10,
            bet_to_call=8,  # 80% pot
            stack_to_pot_ratio=5.0
        )
        assert freq.fold > 50.0
        assert abs((freq.fold + freq.call + freq.raise_) - 100.0) < 0.1

    # Frequency Calculation Tests - Postflop

    def test_frequencies_postflop_first_to_act_deep(self, calc):
        """Test postflop frequencies first to act with deep stacks"""
        freq = calc.calculate_frequencies(
            street=Street.FLOP,
            pot_size=20,
            bet_to_call=0,
            stack_to_pot_ratio=5.0
        )
        assert freq.check > 30.0
        assert freq.bet > 30.0
        assert freq.all_in > 0.0
        assert abs((freq.check + freq.bet + freq.all_in) - 100.0) < 0.1

    def test_frequencies_postflop_first_to_act_shallow(self, calc):
        """Test postflop frequencies first to act with shallow stacks"""
        freq = calc.calculate_frequencies(
            street=Street.FLOP,
            pot_size=20,
            bet_to_call=0,
            stack_to_pot_ratio=1.0
        )
        assert freq.check > 30.0
        assert freq.all_in > 20.0  # Higher all-in frequency
        assert abs((freq.check + freq.bet + freq.all_in) - 100.0) < 0.1

    def test_frequencies_facing_bet_strong_equity(self, calc):
        """Test frequencies facing bet with strong equity"""
        freq = calc.calculate_frequencies(
            street=Street.FLOP,
            pot_size=20,
            bet_to_call=10,
            stack_to_pot_ratio=3.0,
            equity=70.0  # Strong equity
        )
        assert freq.fold < 20.0  # Low fold frequency
        assert freq.raise_ > 40.0  # High raise frequency
        assert abs((freq.fold + freq.call + freq.raise_ + freq.all_in) - 100.0) < 0.1

    def test_frequencies_facing_bet_marginal_equity(self, calc):
        """Test frequencies facing bet with marginal equity"""
        freq = calc.calculate_frequencies(
            street=Street.FLOP,
            pot_size=20,
            bet_to_call=10,
            stack_to_pot_ratio=3.0,
            equity=40.0  # Marginal equity (pot odds ~33%)
        )
        assert freq.fold < 40.0
        assert freq.call > 50.0  # High call frequency
        assert abs((freq.fold + freq.call + freq.raise_) - 100.0) < 0.1

    def test_frequencies_facing_bet_weak_equity(self, calc):
        """Test frequencies facing bet with weak equity"""
        freq = calc.calculate_frequencies(
            street=Street.FLOP,
            pot_size=20,
            bet_to_call=10,
            stack_to_pot_ratio=3.0,
            equity=20.0  # Weak equity
        )
        assert freq.fold > 65.0  # High fold frequency
        assert abs((freq.fold + freq.call + freq.raise_) - 100.0) < 0.1

    def test_frequencies_facing_bet_no_equity(self, calc):
        """Test frequencies facing bet with no equity info"""
        freq = calc.calculate_frequencies(
            street=Street.TURN,
            pot_size=30,
            bet_to_call=20,
            stack_to_pot_ratio=2.0,
            equity=None
        )
        assert freq.fold == 50.0  # Default mixed strategy
        assert freq.call == 35.0
        assert freq.raise_ == 15.0

    def test_frequencies_sum_to_100(self, calc):
        """Test all frequencies sum to 100%"""
        freq = calc.calculate_frequencies(
            street=Street.RIVER,
            pot_size=50,
            bet_to_call=30,
            stack_to_pot_ratio=1.5,
            equity=55.0
        )
        total = freq.fold + freq.check + freq.call + freq.bet + freq.raise_ + freq.all_in
        assert abs(total - 100.0) < 0.1

    # Range vs Range GTO Tests

    def test_range_gto_strong_vs_weak(self, calc):
        """Test GTO frequencies for strong range vs weak range"""
        result = calc.calculate_range_gto(
            hero_range=['AA', 'KK', 'QQ', 'JJ'],
            villain_range=['88', '77', '66'],
            board=['Ah', 'Kd', '9c'],
            pot_size=20
        )
        assert result['bet'] > result['check']
        assert result['fold'] < 20.0

    def test_range_gto_weak_vs_strong(self, calc):
        """Test GTO frequencies for weak range vs strong range"""
        result = calc.calculate_range_gto(
            hero_range=['88', '77', '66'],
            villain_range=['AA', 'KK', 'QQ', 'JJ'],
            board=['Ah', 'Kd', '9c'],
            pot_size=20
        )
        assert result['check'] > result['bet']
        assert result['fold'] > 20.0

    def test_range_gto_equal_ranges(self, calc):
        """Test GTO frequencies for equal ranges"""
        same_range = ['AA', 'KK', 'QQ', 'JJ', 'TT']
        result = calc.calculate_range_gto(
            hero_range=same_range,
            villain_range=same_range,
            board=['9h', '7d', '2c'],
            pot_size=20
        )
        assert 35.0 < result['bet'] < 55.0  # Balanced strategy
        assert 30.0 < result['check'] < 50.0

    # BB Defense Range Tests

    def test_bb_defense_bad_pot_odds(self, calc):
        """Test BB defends tight with bad pot odds"""
        range_data = calc.get_bb_defense_range(pot_odds=0.20)
        assert range_data.percentage == 30.0
        assert 'AA' in range_data.hands
        assert 'KK' in range_data.hands
        assert '22' not in range_data.hands

    def test_bb_defense_medium_pot_odds(self, calc):
        """Test BB defends wider with medium pot odds"""
        range_data = calc.get_bb_defense_range(pot_odds=0.30)
        assert range_data.percentage == 45.0
        assert len(range_data.hands) > 10

    def test_bb_defense_good_pot_odds(self, calc):
        """Test BB defends wide with good pot odds"""
        range_data = calc.get_bb_defense_range(pot_odds=0.40)
        assert range_data.percentage == 65.0
        assert '22' in range_data.hands
        assert 'A5s' in range_data.hands
        assert len(range_data.hands) > 20

    def test_bb_defense_wider_with_better_odds(self, calc):
        """Test BB defense range widens as pot odds improve"""
        bad_odds = calc.get_bb_defense_range(pot_odds=0.20)
        good_odds = calc.get_bb_defense_range(pot_odds=0.40)
        assert good_odds.percentage > bad_odds.percentage
        assert len(good_odds.hands) > len(bad_odds.hands)

    # Optimal Bet Size Tests

    def test_bet_size_flop(self, calc):
        """Test optimal bet size on flop is 2/3 pot"""
        size, desc = calc.get_optimal_bet_size(
            pot_size=30,
            street=Street.FLOP,
            stack_remaining=200
        )
        assert abs(size - 19.8) < 0.1  # 0.66 * 30 = 19.8
        assert desc == "2/3 pot"

    def test_bet_size_turn(self, calc):
        """Test optimal bet size on turn is 3/4 pot"""
        size, desc = calc.get_optimal_bet_size(
            pot_size=40,
            street=Street.TURN,
            stack_remaining=200
        )
        assert abs(size - 30.0) < 0.1  # 3/4 of 40
        assert desc == "3/4 pot"

    def test_bet_size_river(self, calc):
        """Test optimal bet size on river is 3/4 pot"""
        size, desc = calc.get_optimal_bet_size(
            pot_size=60,
            street=Street.RIVER,
            stack_remaining=200
        )
        assert abs(size - 45.0) < 0.1  # 3/4 of 60
        assert desc == "3/4 pot"

    def test_bet_size_preflop(self, calc):
        """Test optimal bet size preflop is 1/2 pot"""
        size, desc = calc.get_optimal_bet_size(
            pot_size=10,
            street=Street.PREFLOP,
            stack_remaining=200
        )
        assert abs(size - 5.0) < 0.1  # 1/2 of 10
        assert desc == "1/2 pot"

    def test_bet_size_capped_at_stack(self, calc):
        """Test bet size is capped at remaining stack"""
        size, desc = calc.get_optimal_bet_size(
            pot_size=100,
            street=Street.RIVER,
            stack_remaining=50
        )
        assert size == 50.0
        assert desc == "all-in"

    def test_bet_size_all_in_exactly_at_stack(self, calc):
        """Test bet size returns stack when GTO size equals stack"""
        size, desc = calc.get_optimal_bet_size(
            pot_size=60,
            street=Street.RIVER,
            stack_remaining=45
        )
        assert size == 45.0
        assert desc == "all-in"

    # Edge Cases and Validation

    def test_frequencies_never_negative(self, calc):
        """Test frequencies are never negative"""
        freq = calc.calculate_frequencies(
            street=Street.FLOP,
            pot_size=20,
            bet_to_call=50,  # Overbet
            stack_to_pot_ratio=0.5,
            equity=10.0
        )
        assert freq.fold >= 0.0
        assert freq.check >= 0.0
        assert freq.call >= 0.0
        assert freq.bet >= 0.0
        assert freq.raise_ >= 0.0
        assert freq.all_in >= 0.0

    def test_frequencies_never_exceed_100(self, calc):
        """Test individual frequencies never exceed 100%"""
        freq = calc.calculate_frequencies(
            street=Street.TURN,
            pot_size=100,
            bet_to_call=0,
            stack_to_pot_ratio=10.0,
            equity=95.0
        )
        assert freq.fold <= 100.0
        assert freq.check <= 100.0
        assert freq.call <= 100.0
        assert freq.bet <= 100.0
        assert freq.raise_ <= 100.0
        assert freq.all_in <= 100.0

    def test_bet_size_zero_pot(self, calc):
        """Test bet size with zero pot returns zero"""
        size, desc = calc.get_optimal_bet_size(
            pot_size=0,
            street=Street.FLOP,
            stack_remaining=100
        )
        assert size == 0.0

    def test_preflop_ranges_contain_premium_hands(self, calc):
        """Test all positions include premium hands in range"""
        for position in [Position.UTG, Position.MP, Position.CO, Position.BTN, Position.SB]:
            range_data = calc.get_preflop_range(position, "open_raise")
            if range_data.percentage > 0:  # Skip BB
                assert 'AA' in range_data.hands
                assert 'KK' in range_data.hands
                assert 'QQ' in range_data.hands

    # Performance Tests

    def test_calculate_frequencies_performance(self, calc):
        """Test frequency calculation is fast"""
        import time

        start = time.time()
        for _ in range(100):
            calc.calculate_frequencies(
                street=Street.FLOP,
                pot_size=30,
                bet_to_call=20,
                stack_to_pot_ratio=3.0,
                equity=55.0
            )
        duration = time.time() - start

        assert duration < 0.1  # 100 calculations in < 100ms

    def test_get_preflop_range_performance(self, calc):
        """Test preflop range retrieval is fast"""
        import time

        start = time.time()
        for _ in range(1000):
            calc.get_preflop_range(Position.BTN, "open_raise")
        duration = time.time() - start

        assert duration < 0.1  # 1000 retrievals in < 100ms

    def test_bet_size_calculation_performance(self, calc):
        """Test bet size calculation is fast"""
        import time

        start = time.time()
        for _ in range(1000):
            calc.get_optimal_bet_size(50, Street.FLOP, 200)
        duration = time.time() - start

        assert duration < 0.05  # 1000 calculations in < 50ms


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
