"""
Solver-Based Preflop Charts (PREFLOP-001)

Comprehensive solver-approved preflop ranges for various situations.
Provides easy access to GTO ranges with multiple adjustment options.

ID: PREFLOP-001
Priority: MEDIUM
Expected Accuracy Gain: 8-10% improvement in preflop play
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from .range_generator import (
    RangeGenerator,
    RangeParameters,
    HandRange,
    Position,
    Action,
    HandParser
)


@dataclass
class ChartRecommendation:
    """Recommendation for a specific situation"""
    position: Position
    action: Action
    range: HandRange
    reasoning: str
    confidence: float  # 0-1


class PreflopChartManager:
    """Manage preflop charts and provide recommendations"""
    
    def __init__(self):
        self.generator = RangeGenerator()
        self.chart_cache = {}
    
    def get_chart(self, params: RangeParameters) -> Optional[HandRange]:
        """Get preflop chart for parameters (cached)"""
        # Create cache key
        cache_key = self._create_cache_key(params)
        
        # Check cache
        if cache_key in self.chart_cache:
            return self.chart_cache[cache_key]
        
        # Generate range
        chart = self.generator.generate_range(params)
        
        # Cache result
        if chart:
            self.chart_cache[cache_key] = chart
        
        return chart
    
    def _create_cache_key(self, params: RangeParameters) -> str:
        """Create cache key from parameters"""
        return f"{params.position.value}_{params.action.value}_{params.stack_depth}_{params.ante}_{params.straddle}_{params.num_players}_{params.icm_pressure}"
    
    def get_recommendation(self, situation: Dict) -> Optional[ChartRecommendation]:
        """Get recommendation for a specific situation"""
        # Extract parameters from situation
        position = Position(situation.get('position', 'btn'))
        action = Action(situation.get('action', 'open_raise'))
        stack_depth = situation.get('stack_depth', 100.0)
        ante = situation.get('ante', 0.0)
        straddle = situation.get('straddle', False)
        num_players = situation.get('num_players', 2)
        icm_pressure = situation.get('icm_pressure', 0.0)
        
        params = RangeParameters(
            position=position,
            action=action,
            stack_depth=stack_depth,
            ante=ante,
            straddle=straddle,
            num_players=num_players,
            icm_pressure=icm_pressure,
            facing_raise=situation.get('facing_raise', False),
            raise_size=situation.get('raise_size', 2.5)
        )
        
        chart = self.get_chart(params)
        if not chart:
            return None
        
        # Generate reasoning
        reasoning = self._generate_reasoning(params, chart)
        
        # Calculate confidence
        confidence = self._calculate_confidence(params)
        
        return ChartRecommendation(
            position=position,
            action=action,
            range=chart,
            reasoning=reasoning,
            confidence=confidence
        )
    
    def _generate_reasoning(self, params: RangeParameters, chart: HandRange) -> str:
        """Generate reasoning for recommendation"""
        reasons = []
        
        # Position reasoning
        if params.position in [Position.UTG, Position.UTG1, Position.UTG2]:
            reasons.append("Early position requires tighter range")
        elif params.position in [Position.BTN, Position.CO]:
            reasons.append("Late position allows wider range")
        
        # Ante reasoning
        if params.ante > 0:
            reasons.append(f"Ante ({params.ante} BB) widens range due to better pot odds")
        
        # Straddle reasoning
        if params.straddle:
            reasons.append("Straddle tightens range due to increased investment")
        
        # ICM reasoning
        if params.icm_pressure > 0.3:
            reasons.append(f"ICM pressure ({params.icm_pressure:.1%}) tightens range")
        
        # Multi-way reasoning
        if params.num_players > 2:
            reasons.append(f"{params.num_players} players in pot requires stronger holdings")
        
        return "; ".join(reasons) if reasons else "Standard range for this situation"
    
    def _calculate_confidence(self, params: RangeParameters) -> float:
        """Calculate confidence in recommendation"""
        confidence = 1.0
        
        # Reduce confidence for extreme situations
        if params.icm_pressure > 0.7:
            confidence *= 0.85
        
        if params.num_players > 4:
            confidence *= 0.9
        
        if params.straddle and params.ante > 0.5:
            confidence *= 0.95
        
        return confidence
    
    def should_play_hand(self, hand: str, params: RangeParameters) -> Tuple[bool, float]:
        """Check if hand should be played and with what frequency"""
        chart = self.get_chart(params)
        if not chart:
            return False, 0.0
        
        # Expand hand notation
        expanded = HandParser.expand_notation(hand)
        
        # Check if any expanded version is in range
        max_freq = 0.0
        for h in expanded:
            freq = chart.hands.get(h, 0.0)
            max_freq = max(max_freq, freq)
        
        return max_freq > 0.1, max_freq
    
    def export_all_charts(self, directory: str):
        """Export all charts to directory"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        # Export charts for common situations
        positions = [Position.UTG, Position.HJ, Position.CO, Position.BTN, Position.SB]
        actions = [Action.OPEN_RAISE]
        
        for position in positions:
            for action in actions:
                params = RangeParameters(
                    position=position,
                    action=action,
                    stack_depth=100.0,
                    ante=0.0,
                    straddle=False,
                    num_players=2,
                    icm_pressure=0.0,
                    facing_raise=False,
                    raise_size=2.5
                )
                
                chart = self.get_chart(params)
                if chart:
                    filename = f"{position.value}_{action.value}_100bb.json"
                    filepath = os.path.join(directory, filename)
                    self.generator.export_range(chart, filepath)
    
    def compare_ranges(self, params1: RangeParameters, params2: RangeParameters) -> Dict:
        """Compare two ranges"""
        range1 = self.get_chart(params1)
        range2 = self.get_chart(params2)
        
        if not range1 or not range2:
            return {}
        
        # Find common hands
        all_hands = set(range1.hands.keys()) | set(range2.hands.keys())
        common = set(range1.hands.keys()) & set(range2.hands.keys())
        only_range1 = set(range1.hands.keys()) - set(range2.hands.keys())
        only_range2 = set(range2.hands.keys()) - set(range1.hands.keys())
        
        return {
            'range1_vpip': range1.vpip,
            'range2_vpip': range2.vpip,
            'vpip_difference': abs(range1.vpip - range2.vpip),
            'common_hands': len(common),
            'only_in_range1': len(only_range1),
            'only_in_range2': len(only_range2),
            'overlap_percentage': len(common) / len(all_hands) * 100 if all_hands else 0
        }


class QuickCharts:
    """Quick access to common preflop charts"""
    
    def __init__(self):
        self.manager = PreflopChartManager()
    
    def utg_open_100bb(self) -> HandRange:
        """UTG open raise at 100bb"""
        params = RangeParameters(
            position=Position.UTG,
            action=Action.OPEN_RAISE,
            stack_depth=100.0,
            ante=0.0,
            straddle=False,
            num_players=2,
            icm_pressure=0.0,
            facing_raise=False,
            raise_size=2.5
        )
        return self.manager.get_chart(params)
    
    def btn_open_100bb(self) -> HandRange:
        """BTN open raise at 100bb"""
        params = RangeParameters(
            position=Position.BTN,
            action=Action.OPEN_RAISE,
            stack_depth=100.0,
            ante=0.0,
            straddle=False,
            num_players=2,
            icm_pressure=0.0,
            facing_raise=False,
            raise_size=2.5
        )
        return self.manager.get_chart(params)
    
    def co_open_100bb(self) -> HandRange:
        """CO open raise at 100bb"""
        params = RangeParameters(
            position=Position.CO,
            action=Action.OPEN_RAISE,
            stack_depth=100.0,
            ante=0.0,
            straddle=False,
            num_players=2,
            icm_pressure=0.0,
            facing_raise=False,
            raise_size=2.5
        )
        return self.manager.get_chart(params)
    
    def sb_open_100bb(self) -> HandRange:
        """SB open raise at 100bb"""
        params = RangeParameters(
            position=Position.SB,
            action=Action.OPEN_RAISE,
            stack_depth=100.0,
            ante=0.0,
            straddle=False,
            num_players=2,
            icm_pressure=0.0,
            facing_raise=False,
            raise_size=2.5
        )
        return self.manager.get_chart(params)
    
    def btn_open_with_ante(self, ante: float = 0.125) -> HandRange:
        """BTN open raise with ante"""
        params = RangeParameters(
            position=Position.BTN,
            action=Action.OPEN_RAISE,
            stack_depth=100.0,
            ante=ante,
            straddle=False,
            num_players=9,
            icm_pressure=0.0,
            facing_raise=False,
            raise_size=2.5
        )
        return self.manager.get_chart(params)
    
    def utg_open_with_straddle(self) -> HandRange:
        """UTG open raise with straddle"""
        params = RangeParameters(
            position=Position.UTG,
            action=Action.OPEN_RAISE,
            stack_depth=100.0,
            ante=0.0,
            straddle=True,
            num_players=2,
            icm_pressure=0.0,
            facing_raise=False,
            raise_size=4.0
        )
        return self.manager.get_chart(params)
    
    def btn_open_bubble(self, icm_pressure: float = 0.7) -> HandRange:
        """BTN open raise on bubble"""
        params = RangeParameters(
            position=Position.BTN,
            action=Action.OPEN_RAISE,
            stack_depth=100.0,
            ante=0.125,
            straddle=False,
            num_players=9,
            icm_pressure=icm_pressure,
            facing_raise=False,
            raise_size=2.5
        )
        return self.manager.get_chart(params)


class PreflopAnalyzer:
    """Analyze preflop situations"""
    
    def __init__(self):
        self.manager = PreflopChartManager()
    
    def analyze_situation(self, situation: Dict) -> Dict:
        """Analyze a preflop situation"""
        recommendation = self.manager.get_recommendation(situation)
        
        if not recommendation:
            return {
                'error': 'Could not generate recommendation for situation'
            }
        
        return {
            'position': recommendation.position.value,
            'action': recommendation.action.value,
            'range_vpip': recommendation.range.vpip,
            'total_combos': recommendation.range.total_combos,
            'reasoning': recommendation.reasoning,
            'confidence': recommendation.confidence,
            'top_hands': list(recommendation.range.hands.keys())[:20]
        }
    
    def get_position_ranges(self, stack_depth: float = 100.0) -> Dict:
        """Get ranges for all positions"""
        positions = [Position.UTG, Position.HJ, Position.CO, Position.BTN, Position.SB]
        ranges = {}
        
        for position in positions:
            params = RangeParameters(
                position=position,
                action=Action.OPEN_RAISE,
                stack_depth=stack_depth,
                ante=0.0,
                straddle=False,
                num_players=2,
                icm_pressure=0.0,
                facing_raise=False,
                raise_size=2.5
            )
            
            chart = self.manager.get_chart(params)
            if chart:
                ranges[position.value] = {
                    'vpip': chart.vpip,
                    'combos': chart.total_combos,
                    'description': chart.description
                }
        
        return ranges
    
    def calculate_range_width_trend(self) -> List[Tuple[str, float]]:
        """Calculate how ranges widen by position"""
        positions = [
            Position.UTG,
            Position.HJ,
            Position.CO,
            Position.BTN,
            Position.SB
        ]
        
        trend = []
        for position in positions:
            params = RangeParameters(
                position=position,
                action=Action.OPEN_RAISE,
                stack_depth=100.0,
                ante=0.0,
                straddle=False,
                num_players=2,
                icm_pressure=0.0,
                facing_raise=False,
                raise_size=2.5
            )
            
            chart = self.manager.get_chart(params)
            if chart:
                trend.append((position.value, chart.vpip))
        
        return trend
