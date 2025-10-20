"""
Tests for Advanced Range Merging Algorithm (MERGE-001)

Tests minimum defense frequency, polarization optimization, removal effects,
blockers analysis, and range simplification.
"""

import pytest
import json
import tempfile
import os
from src.pokertool.range_merger import (
    MinimumDefenseFrequency,
    PolarizationOptimizer,
    RemovalEffectsCalculator,
    BlockerAnalyzer,
    RangeSimplifier,
    AdvancedRangeMerger,
    HandCombo,
    HandCategory,
    RangeStructure
)
from src.pokertool.blocker_effects import (
    BlockerType,
    BlockerStrength,
    BoardTextureAnalyzer,
    EquityAdjuster,
    BluffSelector,
    RangeBlockerAnalysis,
    quick_blocker_eval,
    get_best_bluff_combos
)


class TestMinimumDefenseFrequency:
    """Test MDF calculations"""
    
    def test_calculate_mdf_basic(self):
        """Test basic MDF calculation"""
        mdf_calc = MinimumDefenseFrequency()
        
        # Pot = 100, Bet = 50, MDF = 1 - (50 / 150) = 0.667
        mdf = mdf_calc.calculate_mdf(100, 50)
        assert abs(mdf - 0.667) < 0.01
    
    def test_calculate_mdf_pot_sized_bet(self):
        """Test MDF with pot-sized bet"""
        mdf_calc = MinimumDefenseFrequency()
        
        # Pot = 100, Bet = 100, MDF = 1 - (100 / 200) = 0.5
        mdf = mdf_calc.calculate_mdf(100, 100)
        assert abs(mdf - 0.5) < 0.01
    
    def test_calculate_mdf_overbet(self):
        """Test MDF with overbet"""
        mdf_calc = MinimumDefenseFrequency()
        
        # Pot = 100, Bet = 200, MDF = 1 - (200 / 300) = 0.333
        mdf = mdf_calc.calculate_mdf(100, 200)
        assert abs(mdf - 0.333) < 0.01
    
    def test_get_defense_combos(self):
        """Test defense combo calculation"""
        mdf_calc = MinimumDefenseFrequency()
        
        combos = mdf_calc.get_defense_combos(100, 0.667)
        assert combos == 66
    
    def test_validate_defense_range(self):
        """Test defense range validation"""
        mdf_calc = MinimumDefenseFrequency()
        
        defending_hands = [
            HandCombo("AhKs", weight=4),
            HandCombo("AhQs", weight=4),
            HandCombo("AhJs", weight=4),
        ]
        
        # Total 12 combos defending out of 100 needed
        result = mdf_calc.validate_defense_range(defending_hands, 100, 0.5)
        assert result is False  # Not enough combos
        
        # Add more combos
        defending_hands.extend([HandCombo(f"hand{i}", weight=10) for i in range(4)])
        result = mdf_calc.validate_defense_range(defending_hands, 100, 0.5)
        assert result is True  # Now enough combos


class TestPolarizationOptimizer:
    """Test polarization optimization"""
    
    def test_calculate_optimal_ratio(self):
        """Test optimal ratio calculation"""
        optimizer = PolarizationOptimizer()
        
        # River with 0.5 pot bet
        ratio = optimizer.calculate_optimal_ratio('river', 100, 50)
        assert ratio > 2.0  # Should be > base river ratio
        
        # Flop with pot bet
        ratio = optimizer.calculate_optimal_ratio('flop', 100, 100)
        assert ratio > 1.0
    
    def test_optimize_polarization(self):
        """Test polarization optimization"""
        optimizer = PolarizationOptimizer()
        
        value_hands = [
            HandCombo("AhAs", weight=6, category=HandCategory.PREMIUM),
            HandCombo("KhKs", weight=6, category=HandCategory.PREMIUM),
        ]
        
        bluff_hands = [
            HandCombo("Ah5h", weight=4, category=HandCategory.BLUFF),
            HandCombo("Kh6h", weight=4, category=HandCategory.BLUFF),
        ]
        
        target_ratio = 2.0  # Want 2:1 value to bluff
        result = optimizer.optimize_polarization(value_hands, bluff_hands, target_ratio)
        
        assert isinstance(result, RangeStructure)
        assert result.total_combos > 0
        assert abs(result.polarization_ratio - target_ratio) / target_ratio < 0.3
    
    def test_is_properly_polarized(self):
        """Test polarization validation"""
        optimizer = PolarizationOptimizer()
        
        range_struct = RangeStructure(
            value_combos=[HandCombo("AA", weight=12)],
            bluff_combos=[HandCombo("A5s", weight=6)],
            total_combos=18,
            polarization_ratio=2.0,
            mdf=0.5
        )
        
        assert optimizer.is_properly_polarized(range_struct, 2.0, tolerance=0.2)
        assert not optimizer.is_properly_polarized(range_struct, 3.0, tolerance=0.1)


class TestRemovalEffectsCalculator:
    """Test removal effects calculations"""
    
    def test_get_removed_cards(self):
        """Test card parsing"""
        calc = RemovalEffectsCalculator()
        
        removed = calc.get_removed_cards("AhKsQd")
        assert "Ah" in removed
        assert "Ks" in removed
        assert "Qd" in removed
        assert len(removed) == 3
    
    def test_calculate_combo_count_pair(self):
        """Test combo count for pairs"""
        calc = RemovalEffectsCalculator()
        
        # AA with no removals = 6 combos
        count = calc.calculate_combo_count("AA", set())
        assert count == 6
        
        # AA with Ah removed = 3 combos
        count = calc.calculate_combo_count("AA", {"Ah"})
        assert count == 3
        
        # AA with Ah and As removed = 1 combo (Ad-Ac)
        count = calc.calculate_combo_count("AA", {"Ah", "As"})
        assert count == 1
    
    def test_calculate_combo_count_suited(self):
        """Test combo count for suited hands"""
        calc = RemovalEffectsCalculator()
        
        # AKs with no removals = 4 combos
        count = calc.calculate_combo_count("AKs", set())
        assert count == 4
        
        # AKs with Ah removed = 3 combos
        count = calc.calculate_combo_count("AKs", {"Ah"})
        assert count == 3
    
    def test_calculate_combo_count_offsuit(self):
        """Test combo count for offsuit hands"""
        calc = RemovalEffectsCalculator()
        
        # AKo with no removals = 12 combos
        count = calc.calculate_combo_count("AKo", set())
        assert count == 12
        
        # AKo with Ah removed = 9 combos
        count = calc.calculate_combo_count("AKo", {"Ah"})
        assert count == 9
    
    def test_apply_removal_effects(self):
        """Test removal effects on range"""
        calc = RemovalEffectsCalculator()
        
        range_hands = ["AA", "KK", "AK"]
        board = "AhKsQd"
        
        counts = calc.apply_removal_effects(range_hands, board)
        
        # AA should have fewer combos (Ah removed)
        assert counts["AA"] < 6
        # KK should have fewer combos (Ks removed)
        assert counts["KK"] < 6
        # AK should have fewer combos (both removed)
        assert counts["AK"] < 16
    
    def test_calculate_removal_impact(self):
        """Test removal impact calculation"""
        calc = RemovalEffectsCalculator()
        
        # Hand with premium cards
        impact = calc.calculate_removal_impact("AhKs", "QdJdTd")
        assert impact > 0.5  # High impact (2 premium cards)
        
        # Hand without premium cards
        impact = calc.calculate_removal_impact("5h4h", "QdJdTd")
        assert impact == 0.0  # No premium cards


class TestBlockerAnalyzer:
    """Test blocker analysis"""
    
    def test_analyze_blockers(self):
        """Test blocker analysis"""
        analyzer = BlockerAnalyzer()
        
        hand = "AhKh"
        villain_range = ["AA", "KK", "AK", "QQ"]
        board = "Qh9h2d"
        
        effects = analyzer.analyze_blockers(hand, villain_range, board)
        
        assert 'value_blocked' in effects
        assert 'bluff_blocked' in effects
        assert effects['total_combos_blocked'] > 0
    
    def test_rank_blocker_hands(self):
        """Test blocker hand ranking"""
        analyzer = BlockerAnalyzer()
        
        hands = [
            HandCombo("AhKh", weight=4),
            HandCombo("7h6h", weight=4),
        ]
        villain_range = ["AA", "KK"]
        board = "Qh9h2d"
        
        ranked = analyzer.rank_blocker_hands(hands, villain_range, board)
        
        assert len(ranked) == 2
        # AhKh should rank higher (blocks AA and KK)
        assert ranked[0][0].cards == "AhKh"
    
    def test_select_bluff_combos(self):
        """Test bluff combo selection"""
        analyzer = BlockerAnalyzer()
        
        candidates = [
            HandCombo("AhKh", weight=1),
            HandCombo("7h6h", weight=1),
            HandCombo("Ah5h", weight=1),
        ]
        villain_range = ["AA", "KK", "AK"]
        board = "Qh9h2d"
        
        selected = analyzer.select_bluff_combos(candidates, villain_range, board, 2)
        
        assert len(selected) <= 2
        assert all(isinstance(h, HandCombo) for h in selected)


class TestRangeSimplifier:
    """Test range simplification"""
    
    def test_simplify_range(self):
        """Test range simplification"""
        simplifier = RangeSimplifier()
        
        hands = [
            HandCombo("AA", weight=6),
            HandCombo("KK", weight=6),
            HandCombo("JTs", weight=4),
            HandCombo("55", weight=6),
        ]
        
        simplified = simplifier.simplify_range(hands)
        
        assert 'premium_pairs' in simplified
        assert 'suited_connectors' in simplified
        assert 'small_pairs' in simplified
    
    def test_merge_similar_hands(self):
        """Test merging similar hands"""
        simplifier = RangeSimplifier()
        
        hands = [
            HandCombo("AA", weight=6, equity=0.85),
            HandCombo("KK", weight=6, equity=0.83),
            HandCombo("QQ", weight=6, equity=0.80),
        ]
        
        merged = simplifier.merge_similar_hands(hands, equity_threshold=0.03)
        
        # AA and KK should merge (within 0.03)
        assert len(merged) < len(hands)
    
    def test_get_range_summary(self):
        """Test range summary"""
        simplifier = RangeSimplifier()
        
        hands = [
            HandCombo("AA", weight=6, equity=0.85),
            HandCombo("KK", weight=6, equity=0.82),
        ]
        
        summary = simplifier.get_range_summary(hands)
        
        assert summary['total_combos'] == 12
        assert 0.8 < summary['avg_equity'] < 0.9
        assert summary['num_unique_hands'] == 2


class TestAdvancedRangeMerger:
    """Test main range merger"""
    
    def test_construct_optimal_range(self):
        """Test optimal range construction"""
        merger = AdvancedRangeMerger()
        
        situation = {
            'street': 'river',
            'pot_size': 100,
            'bet_size': 75,
            'action': 'bet',
            'board': 'AhKsQd9h2c',
            'value_hands': [
                HandCombo("AhAs", weight=3),
                HandCombo("KhKs", weight=3),
            ],
            'bluff_hands': [
                HandCombo("7h8h", weight=4),
            ],
            'villain_range': ["AA", "KK", "QQ"]
        }
        
        result = merger.construct_optimal_range(situation)
        
        assert isinstance(result, RangeStructure)
        assert result.total_combos > 0
        assert result.polarization_ratio > 0
    
    def test_merge_ranges(self):
        """Test range merging"""
        merger = AdvancedRangeMerger()
        
        range1 = RangeStructure(
            value_combos=[HandCombo("AA", weight=6)],
            bluff_combos=[HandCombo("A5s", weight=4)],
            total_combos=10,
            polarization_ratio=1.5,
            mdf=0.6
        )
        
        range2 = RangeStructure(
            value_combos=[HandCombo("KK", weight=6)],
            bluff_combos=[HandCombo("K6s", weight=4)],
            total_combos=10,
            polarization_ratio=1.5,
            mdf=0.5
        )
        
        merged = merger.merge_ranges(range1, range2, 0.5, 0.5)
        
        assert isinstance(merged, RangeStructure)
        assert len(merged.value_combos) == 2
        assert len(merged.bluff_combos) == 2
    
    def test_export_import_range(self):
        """Test range export and import"""
        merger = AdvancedRangeMerger()
        
        original = RangeStructure(
            value_combos=[HandCombo("AA", weight=6, equity=0.85)],
            bluff_combos=[HandCombo("A5s", weight=4, equity=0.35)],
            total_combos=10,
            polarization_ratio=1.5,
            mdf=0.5
        )
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name
        
        try:
            merger.export_range(original, filepath)
            imported = merger.import_range(filepath)
            
            assert len(imported.value_combos) == len(original.value_combos)
            assert len(imported.bluff_combos) == len(original.bluff_combos)
            assert imported.total_combos == original.total_combos
            assert abs(imported.polarization_ratio - original.polarization_ratio) < 0.01
        finally:
            os.unlink(filepath)


class TestBlockerEffects:
    """Test blocker effects module"""
    
    def test_board_texture_analyzer(self):
        """Test board texture analysis"""
        analyzer = BoardTextureAnalyzer()
        
        # Test flush draw detection
        flush_present, suit = analyzer.get_flush_draw_present("AhKhQh")
        assert flush_present is True
        assert suit == 'h'
        
        # Test straight draw detection
        straight_present = analyzer.get_straight_draw_present("Ah9s8d")
        assert straight_present is True
        
        # Test nut identification
        nuts = analyzer.identify_potential_nuts("AhKhQh")
        assert len(nuts) > 0
    
    def test_equity_adjuster(self):
        """Test equity adjustments"""
        adjuster = EquityAdjuster()
        
        # Test with value blocker
        adjusted = adjuster.calculate_equity_adjustment(
            [BlockerType.VALUE_BLOCKER],
            0.5
        )
        assert adjusted > 0.5  # Should increase equity
        
        # Test with bluff blocker
        adjusted = adjuster.calculate_equity_adjustment(
            [BlockerType.BLUFF_BLOCKER],
            0.5
        )
        assert adjusted < 0.5  # Should decrease equity
    
    def test_bluff_selector(self):
        """Test bluff selection"""
        selector = BluffSelector()
        
        hand = "AhKh"
        board = "QhJh2d"
        villain_range = ["AA", "KK", "QQ"]
        
        strength = selector.evaluate_bluff_candidate(hand, board, villain_range)
        
        assert isinstance(strength, BlockerStrength)
        assert 0 <= strength.blocker_score <= 1
        assert strength.recommended_action in ['bluff', 'call', 'fold', 'value']
    
    def test_rank_bluff_candidates(self):
        """Test bluff candidate ranking"""
        selector = BluffSelector()
        
        hands = ["AhKh", "7h6h", "Ah5h"]
        board = "QhJh2d"
        villain_range = ["AA", "KK"]
        
        ranked = selector.rank_bluff_candidates(hands, board, villain_range)
        
        assert len(ranked) == 3
        assert all(isinstance(r[1], BlockerStrength) for r in ranked)
    
    def test_select_optimal_bluffs(self):
        """Test optimal bluff selection"""
        selector = BluffSelector()
        
        hands = ["AhKh", "7h6h", "Ah5h", "9h8h"]
        board = "QhJh2d"
        villain_range = ["AA", "KK", "QQ"]
        
        selected = selector.select_optimal_bluffs(hands, board, villain_range, 2)
        
        assert len(selected) <= 2
        assert all(h in hands for h in selected)
    
    def test_range_blocker_analysis(self):
        """Test range blocker analysis"""
        analyzer = RangeBlockerAnalysis()
        
        hero_range = ["AhKh", "7h6h", "Ah5h"]
        villain_range = ["AA", "KK", "QQ"]
        board = "QhJh2d"
        
        results = analyzer.analyze_range_blockers(hero_range, villain_range, board)
        
        assert 'total_hands_analyzed' in results
        assert 'avg_blocker_score' in results
        assert 'recommended_bluffs' in results
        assert results['total_hands_analyzed'] == 3
    
    def test_compare_blocker_strategies(self):
        """Test strategy comparison"""
        analyzer = RangeBlockerAnalysis()
        
        strategy1 = ["AhKh", "Ah5h"]
        strategy2 = ["7h6h", "9h8h"]
        villain_range = ["AA", "KK"]
        board = "QhJh2d"
        
        comparison = analyzer.compare_blocker_strategies(
            strategy1, strategy2, villain_range, board
        )
        
        assert 'strategy1' in comparison
        assert 'strategy2' in comparison
        assert 'winner' in comparison
        assert comparison['winner'] in ['strategy1', 'strategy2']
    
    def test_quick_blocker_eval(self):
        """Test quick blocker evaluation"""
        score = quick_blocker_eval("AhKh", "QhJh2d", ["AA", "KK"])
        
        assert 0 <= score <= 1
    
    def test_get_best_bluff_combos(self):
        """Test best bluff combo selection"""
        candidates = ["AhKh", "7h6h", "Ah5h", "9h8h", "Kh3h"]
        board = "QhJh2d"
        villain_range = ["AA", "KK", "QQ"]
        
        best = get_best_bluff_combos(candidates, board, villain_range, 3)
        
        assert len(best) <= 3
        assert all(h in candidates for h in best)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
