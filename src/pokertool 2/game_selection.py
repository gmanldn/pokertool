#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Game Selection Module
=================================

This module provides functionality for game selection operations
within the PokerTool application ecosystem.

Module: pokertool.game_selection
Version: 20.0.0
Last Modified: 2025-09-29
Author: PokerTool Development Team
License: MIT

Dependencies:
    - See module imports for specific dependencies
    - Python 3.10+ required

Change Log:
    - v28.0.0 (2025-09-29): Enhanced documentation
    - v19.0.0 (2025-09-18): Bug fixes and improvements
    - v18.0.0 (2025-09-15): Initial implementation
"""

__version__ = '20.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

import logging
import statistics
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import math

logger = logging.getLogger(__name__)

class GameType(Enum):
    """Supported game types."""
    CASH_NLHE = "cash_nlhe"
    CASH_PLO = "cash_plo"
    TOURNAMENT = "tournament"
    SIT_N_GO = "sit_n_go"
    SPIN_N_GO = "spin_n_go"

class TablePosition(Enum):
    """Table positions for seat selection."""
    BUTTON = "button"
    CUTOFF = "cutoff"
    HIJACK = "hijack"
    LOJACK = "lojack"
    UTG = "utg"
    SMALL_BLIND = "small_blind"
    BIG_BLIND = "big_blind"

@dataclass
class PlayerProfile:
    """Individual player profile for table analysis."""
    player_id: str
    name: str
    vpip: float  # Voluntarily Put In Pot %
    pfr: float   # Pre-flop Raise %
    aggression_factor: float
    hands_played: int
    win_rate: float  # bb/100
    is_regular: bool
    skill_level: str  # "fish", "recreational", "regular", "pro"
    tilt_factor: float = 0.0
    stack_size: float = 0.0
    position: Optional[TablePosition] = None
    notes: str = ""

@dataclass
class TableInfo:
    """Table information and statistics."""
    table_id: str
    site: str
    game_type: GameType
    stakes: str  # e.g., "2/4", "0.25/0.50"
    max_players: int
    current_players: int
    average_pot: float
    hands_per_hour: float
    players: List[PlayerProfile] = field(default_factory=list)
    waiting_list: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class GameRating:
    """Comprehensive game rating."""
    table_id: str
    overall_rating: float  # 0-100
    profitability_score: float
    player_pool_score: float
    position_score: float
    volume_score: float
    expected_hourly: float
    fish_count: int
    regular_count: int
    average_stack_depth: float
    recommended_seat: Optional[TablePosition] = None
    reasons: List[str] = field(default_factory=list)

class TableScanner:
    """Scans and analyzes available poker tables."""
    
    def __init__(self, player_database: Dict[str, PlayerProfile] = None):
        self.player_database = player_database or {}
        self.table_history: Dict[str, List[TableInfo]] = {}
        
    def add_player_to_database(self, player: PlayerProfile) -> None:
        """Add or update player in database."""
        self.player_database[player.player_id] = player
        
    def scan_table(self, table_info: TableInfo) -> None:
        """Scan and record table information."""
        # Enrich table with player data from database
        enriched_players = []
        for player in table_info.players:
            if player.player_id in self.player_database:
                enriched_player = self.player_database[player.player_id]
                enriched_player.stack_size = player.stack_size
                enriched_player.position = player.position
                enriched_players.append(enriched_player)
            else:
                enriched_players.append(player)
        
        table_info.players = enriched_players
        
        # Store table history
        if table_info.table_id not in self.table_history:
            self.table_history[table_info.table_id] = []
        self.table_history[table_info.table_id].append(table_info)
        
        logger.info(f"Scanned table {table_info.table_id} with {len(enriched_players)} players")
    
    def get_active_tables(self, min_players: int = 4) -> List[TableInfo]:
        """Get list of active tables with minimum player count."""
        active_tables = []
        
        for table_id, history in self.table_history.items():
            if history:
                latest_table = history[-1]
                if (latest_table.current_players >= min_players and 
                    (datetime.utcnow() - latest_table.last_updated).seconds < 300):  # 5 min old max
                    active_tables.append(latest_table)
                    
        return active_tables
    
    def get_table_trends(self, table_id: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze table trends over time."""
        if table_id not in self.table_history:
            return {}
            
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_snapshots = [
            snapshot for snapshot in self.table_history[table_id]
            if snapshot.last_updated >= cutoff_time
        ]
        
        if not recent_snapshots:
            return {}
        
        player_counts = [s.current_players for s in recent_snapshots]
        pot_sizes = [s.average_pot for s in recent_snapshots if s.average_pot > 0]
        
        return {
            'snapshots_analyzed': len(recent_snapshots),
            'avg_player_count': statistics.mean(player_counts),
            'min_players': min(player_counts),
            'max_players': max(player_counts),
            'avg_pot_size': statistics.mean(pot_sizes) if pot_sizes else 0,
            'stability_score': self._calculate_stability_score(player_counts),
            'growth_trend': self._calculate_trend(player_counts)
        }
    
    def _calculate_stability_score(self, values: List[float]) -> float:
        """Calculate stability score (0-100, higher = more stable)."""
        if len(values) < 2:
            return 50.0
            
        std_dev = statistics.stdev(values)
        mean_val = statistics.mean(values)
        
        if mean_val == 0:
            return 0.0
            
        coefficient_of_variation = std_dev / mean_val
        stability = max(0, 100 - (coefficient_of_variation * 100))
        
        return min(100, stability)
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction."""
        if len(values) < 3:
            return "stable"
            
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg * 1.1:
            return "growing"
        elif second_avg < first_avg * 0.9:
            return "declining"
        else:
            return "stable"

class ProfitabilityCalculator:
    """Calculates expected profitability for different games."""
    
    def __init__(self, hero_stats: Dict[str, float] = None):
        self.hero_stats = hero_stats or {
            'vpip': 23.0,
            'pfr': 18.0,
            'win_rate_vs_fish': 15.0,      # bb/100
            'win_rate_vs_recreational': 8.0,
            'win_rate_vs_regular': -2.0,
            'win_rate_vs_pro': -8.0,
            'hands_per_hour': 80
        }
    
    def calculate_table_profitability(self, table: TableInfo) -> Dict[str, Any]:
        """Calculate expected profitability for a table."""
        if not table.players:
            return {'expected_hourly': 0.0, 'confidence': 'low'}
        
        # Analyze player pool
        fish_count = len([p for p in table.players if p.skill_level == "fish"])
        recreational_count = len([p for p in table.players if p.skill_level == "recreational"])
        regular_count = len([p for p in table.players if p.skill_level == "regular"])
        pro_count = len([p for p in table.players if p.skill_level == "pro"])
        
        total_players = len(table.players)
        
        # Calculate weighted win rate
        fish_weight = fish_count / total_players
        recreational_weight = recreational_count / total_players
        regular_weight = regular_count / total_players
        pro_weight = pro_count / total_players
        
        expected_bb_per_100 = (
            fish_weight * self.hero_stats['win_rate_vs_fish'] +
            recreational_weight * self.hero_stats['win_rate_vs_recreational'] +
            regular_weight * self.hero_stats['win_rate_vs_regular'] +
            pro_weight * self.hero_stats['win_rate_vs_pro']
        )
        
        # Calculate hourly expected value
        stakes_parts = table.stakes.split('/')
        big_blind = float(stakes_parts[1]) if len(stakes_parts) == 2 else 1.0
        
        hands_per_hour = table.hands_per_hour or self.hero_stats['hands_per_hour']
        expected_hourly = (expected_bb_per_100 / 100) * hands_per_hour * big_blind
        
        # Calculate confidence level
        confidence = self._calculate_confidence(table.players)
        
        # Adjust for table dynamics
        dynamic_adjustment = self._calculate_dynamic_adjustment(table)
        adjusted_hourly = expected_hourly * dynamic_adjustment
        
        return {
            'expected_bb_per_100': expected_bb_per_100,
            'expected_hourly': adjusted_hourly,
            'confidence': confidence,
            'fish_count': fish_count,
            'recreational_count': recreational_count,
            'regular_count': regular_count,
            'pro_count': pro_count,
            'dynamic_adjustment': dynamic_adjustment,
            'hands_per_hour': hands_per_hour
        }
    
    def _calculate_confidence(self, players: List[PlayerProfile]) -> str:
        """Calculate confidence level based on data quality."""
        total_hands = sum([p.hands_played for p in players if p.hands_played > 0])
        known_players = len([p for p in players if p.hands_played > 100])
        
        if total_hands > 10000 and known_players >= len(players) * 0.7:
            return "high"
        elif total_hands > 5000 and known_players >= len(players) * 0.5:
            return "medium"
        else:
            return "low"
    
    def _calculate_dynamic_adjustment(self, table: TableInfo) -> float:
        """Calculate adjustment factor based on table dynamics."""
        adjustment = 1.0
        
        # Adjust for table fullness
        fullness_ratio = table.current_players / table.max_players
        if fullness_ratio < 0.5:
            adjustment *= 0.85  # Short-handed penalty
        elif fullness_ratio > 0.8:
            adjustment *= 1.1   # Full table bonus
        
        # Adjust for average pot size (if available)
        if table.average_pot > 0:
            stakes_parts = table.stakes.split('/')
            big_blind = float(stakes_parts[1]) if len(stakes_parts) == 2 else 1.0
            pot_to_bb_ratio = table.average_pot / big_blind
            
            if pot_to_bb_ratio > 15:  # Large pots = more action
                adjustment *= 1.15
            elif pot_to_bb_ratio < 8:  # Small pots = tight play
                adjustment *= 0.9
        
        # Adjust for waiting list
        if table.waiting_list > 3:
            adjustment *= 1.05  # Popular table bonus
        
        return max(0.5, min(1.5, adjustment))  # Cap adjustments

class PlayerPoolAnalyzer:
    """Analyzes player pools for game selection."""
    
    def __init__(self):
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
    
    def analyze_player_pool(self, players: List[PlayerProfile]) -> Dict[str, Any]:
        """Comprehensive player pool analysis."""
        if not players:
            return {'error': 'No players to analyze'}
        
        # Basic statistics
        vpips = [p.vpip for p in players if p.vpip > 0]
        pfrs = [p.pfr for p in players if p.pfr > 0]
        win_rates = [p.win_rate for p in players if p.win_rate != 0]
        
        # Skill distribution
        skill_distribution = {
            'fish': len([p for p in players if p.skill_level == "fish"]),
            'recreational': len([p for p in players if p.skill_level == "recreational"]),
            'regular': len([p for p in players if p.skill_level == "regular"]),
            'pro': len([p for p in players if p.skill_level == "pro"])
        }
        
        # Calculate pool characteristics
        avg_vpip = statistics.mean(vpips) if vpips else 0
        avg_pfr = statistics.mean(pfrs) if pfrs else 0
        avg_win_rate = statistics.mean(win_rates) if win_rates else 0
        
        # Pool type classification
        pool_type = self._classify_pool_type(avg_vpip, avg_pfr, skill_distribution)
        
        # Exploitability score
        exploitability = self._calculate_exploitability(players)
        
        return {
            'total_players': len(players),
            'avg_vpip': avg_vpip,
            'avg_pfr': avg_pfr,
            'avg_win_rate': avg_win_rate,
            'skill_distribution': skill_distribution,
            'pool_type': pool_type,
            'exploitability_score': exploitability,
            'fish_percentage': skill_distribution['fish'] / len(players) * 100,
            'weak_player_percentage': (skill_distribution['fish'] + skill_distribution['recreational']) / len(players) * 100,
            'recommendation': self._generate_pool_recommendation(pool_type, exploitability, skill_distribution)
        }
    
    def _classify_pool_type(self, avg_vpip: float, avg_pfr: float, 
                          skill_distribution: Dict[str, int]) -> str:
        """Classify the type of player pool."""
        total_players = sum(skill_distribution.values())
        fish_percentage = skill_distribution['fish'] / total_players
        weak_percentage = (skill_distribution['fish'] + skill_distribution['recreational']) / total_players
        
        if fish_percentage > 0.4:
            return "very_soft"
        elif weak_percentage > 0.6:
            return "soft"
        elif avg_vpip > 30 and avg_pfr < 15:
            return "loose_passive"
        elif avg_vpip < 20 and avg_pfr > 15:
            return "tight_aggressive"
        elif skill_distribution['regular'] + skill_distribution['pro'] > total_players * 0.7:
            return "tough"
        else:
            return "standard"
    
    def _calculate_exploitability(self, players: List[PlayerProfile]) -> float:
        """Calculate how exploitable the player pool is (0-100)."""
        if not players:
            return 0.0
        
        exploitability_factors = []
        
        for player in players:
            player_exploitability = 50.0  # Base score
            
            # VPIP analysis
            if player.vpip > 40:
                player_exploitability += 20  # Very loose
            elif player.vpip < 15:
                player_exploitability += 10  # Very tight
            
            # PFR analysis
            if player.vpip > 0 and player.pfr > 0:
                pfr_vpip_ratio = player.pfr / player.vpip
                if pfr_vpip_ratio < 0.4:
                    player_exploitability += 15  # Too passive
                elif pfr_vpip_ratio > 0.9:
                    player_exploitability += 5   # Overly aggressive
            
            # Aggression factor
            if player.aggression_factor < 1.5:
                player_exploitability += 10  # Too passive
            elif player.aggression_factor > 4.0:
                player_exploitability += 5   # Too aggressive
            
            # Skill level adjustment
            skill_adjustments = {
                'fish': 30,
                'recreational': 15,
                'regular': -10,
                'pro': -25
            }
            player_exploitability += skill_adjustments.get(player.skill_level, 0)
            
            exploitability_factors.append(max(0, min(100, player_exploitability)))
        
        return statistics.mean(exploitability_factors)
    
    def _generate_pool_recommendation(self, pool_type: str, exploitability: float,
                                    skill_distribution: Dict[str, int]) -> str:
        """Generate recommendation based on pool analysis."""
        total_players = sum(skill_distribution.values())
        
        if pool_type in ["very_soft", "soft"] and exploitability > 70:
            return "Excellent table - high profit potential"
        elif pool_type == "loose_passive" and exploitability > 60:
            return "Good table - value bet heavily"
        elif pool_type == "tight_aggressive":
            return "Standard table - play solid fundamentals"
        elif pool_type == "tough":
            if skill_distribution['fish'] + skill_distribution['recreational'] >= 2:
                return "Tough but playable - target weak players"
            else:
                return "Avoid - too many strong players"
        else:
            return "Standard table - moderate profit potential"

class SeatSelector:
    """Provides seat selection advice."""
    
    def __init__(self):
        self.position_values = {
            TablePosition.BUTTON: 100,
            TablePosition.CUTOFF: 85,
            TablePosition.HIJACK: 70,
            TablePosition.LOJACK: 55,
            TablePosition.UTG: 40,
            TablePosition.SMALL_BLIND: 25,
            TablePosition.BIG_BLIND: 35
        }
    
    def analyze_seat_selection(self, table: TableInfo, available_seats: List[TablePosition]) -> Dict[str, Any]:
        """Analyze and recommend best available seat."""
        if not available_seats or not table.players:
            return {'recommended_seat': None, 'reason': 'No available seats or players'}
        
        seat_scores = {}
        
        for seat in available_seats:
            score = self._calculate_seat_score(seat, table.players)
            seat_scores[seat] = score
        
        # Find best seat
        best_seat = max(seat_scores.keys(), key=lambda s: seat_scores[s])
        best_score = seat_scores[best_seat]
        
        # Generate reasoning
        reasoning = self._generate_seat_reasoning(best_seat, table.players, seat_scores)
        
        return {
            'recommended_seat': best_seat,
            'seat_scores': {seat.value: score for seat, score in seat_scores.items()},
            'best_score': best_score,
            'reasoning': reasoning,
            'weak_players_to_left': self._count_weak_players_to_left(best_seat, table.players),
            'strong_players_to_right': self._count_strong_players_to_right(best_seat, table.players)
        }
    
    def _calculate_seat_score(self, seat: TablePosition, players: List[PlayerProfile]) -> float:
        """Calculate score for a specific seat based on opponents."""
        base_score = self.position_values[seat]
        
        # Find players to the left and right
        left_players = self._get_players_to_left(seat, players)
        right_players = self._get_players_to_right(seat, players)
        
        # Bonus for weak players to the left (they act after us)
        weak_left_bonus = sum([20 for p in left_players if p.skill_level in ['fish', 'recreational']])
        
        # Penalty for strong players to the right (they act after us)
        strong_right_penalty = sum([15 for p in right_players if p.skill_level in ['regular', 'pro']])
        
        # Adjust for aggressive players
        aggressive_left = sum([10 for p in left_players if p.aggression_factor > 3.0])
        passive_right = sum([5 for p in right_players if p.aggression_factor < 2.0])
        
        total_score = base_score + weak_left_bonus - strong_right_penalty + aggressive_left + passive_right
        
        return max(0, total_score)
    
    def _get_players_to_left(self, seat: TablePosition, players: List[PlayerProfile]) -> List[PlayerProfile]:
        """Get players sitting to the left of the given seat."""
        # Simplified - in real implementation would use actual table layout
        return [p for p in players if p.skill_level in ['fish', 'recreational']][:2]
    
    def _get_players_to_right(self, seat: TablePosition, players: List[PlayerProfile]) -> List[PlayerProfile]:
        """Get players sitting to the right of the given seat."""
        # Simplified - in real implementation would use actual table layout  
        return [p for p in players if p.skill_level in ['regular', 'pro']][:2]
    
    def _count_weak_players_to_left(self, seat: TablePosition, players: List[PlayerProfile]) -> int:
        """Count weak players to the left of seat."""
        left_players = self._get_players_to_left(seat, players)
        return len([p for p in left_players if p.skill_level in ['fish', 'recreational']])
    
    def _count_strong_players_to_right(self, seat: TablePosition, players: List[PlayerProfile]) -> int:
        """Count strong players to the right of seat."""
        right_players = self._get_players_to_right(seat, players)
        return len([p for p in right_players if p.skill_level in ['regular', 'pro']])
    
    def _generate_seat_reasoning(self, seat: TablePosition, players: List[PlayerProfile],
                               seat_scores: Dict[TablePosition, float]) -> str:
        """Generate reasoning for seat recommendation."""
        reasoning_parts = []
        
        # Position value
        if self.position_values[seat] >= 85:
            reasoning_parts.append(f"{seat.value} is a strong positional seat")
        elif self.position_values[seat] <= 40:
            reasoning_parts.append(f"{seat.value} has positional challenges")
        
        # Player analysis
        weak_left = self._count_weak_players_to_left(seat, players)
        strong_right = self._count_strong_players_to_right(seat, players)
        
        if weak_left > 0:
            reasoning_parts.append(f"{weak_left} weak player(s) to your left")
        if strong_right > 0:
            reasoning_parts.append(f"{strong_right} strong player(s) to your right")
        
        return "; ".join(reasoning_parts) if reasoning_parts else "Standard seat selection"

class GameSelectionEngine:
    """Main game selection engine combining all components."""
    
    def __init__(self, hero_stats: Dict[str, float] = None):
        self.table_scanner = TableScanner()
        self.profitability_calculator = ProfitabilityCalculator(hero_stats)
        self.player_pool_analyzer = PlayerPoolAnalyzer()
        self.seat_selector = SeatSelector()
        
    def rate_all_tables(self, tables: List[TableInfo], available_seats: Dict[str, List[TablePosition]] = None) -> List[GameRating]:
        """Rate all available tables and return sorted by rating."""
        ratings = []
        
        for table in tables:
            rating = self.rate_table(table, available_seats.get(table.table_id, []) if available_seats else [])
            ratings.append(rating)
        
        # Sort by overall rating (highest first)
        ratings.sort(key=lambda r: r.overall_rating, reverse=True)
        
        return ratings
    
    def rate_table(self, table: TableInfo, available_seats: List[TablePosition] = None) -> GameRating:
        """Provide comprehensive rating for a single table."""
        # Calculate profitability
        profitability = self.profitability_calculator.calculate_table_profitability(table)
        
        # Analyze player pool
        pool_analysis = self.player_pool_analyzer.analyze_player_pool(table.players)
        
        # Analyze seat selection
        seat_analysis = None
        if available_seats:
            seat_analysis = self.seat_selector.analyze_seat_selection(table, available_seats)
        
        # Calculate component scores
        profitability_score = self._calculate_profitability_score(profitability)
        player_pool_score = pool_analysis.get('exploitability_score', 50)
        position_score = self._calculate_position_score(seat_analysis) if seat_analysis else 50
        volume_score = self._calculate_volume_score(table)
        
        # Calculate overall rating (weighted average)
        weights = {
            'profitability': 0.4,
            'player_pool': 0.3,
            'position': 0.2,
            'volume': 0.1
        }
        
        overall_rating = (
            profitability_score * weights['profitability'] +
            player_pool_score * weights['player_pool'] +
            position_score * weights['position'] +
            volume_score * weights['volume']
        )
        
        # Generate reasons
        reasons = self._generate_rating_reasons(profitability, pool_analysis, seat_analysis, table)
        
        return GameRating(
            table_id=table.table_id,
            overall_rating=overall_rating,
            profitability_score=profitability_score,
            player_pool_score=player_pool_score,
            position_score=position_score,
            volume_score=volume_score,
            expected_hourly=profitability.get('expected_hourly', 0),
            fish_count=profitability.get('fish_count', 0),
            regular_count=profitability.get('regular_count', 0),
            average_stack_depth=self._calculate_average_stack_depth(table),
            recommended_seat=seat_analysis.get('recommended_seat') if seat_analysis else None,
            reasons=reasons
        )
    
    def _calculate_profitability_score(self, profitability: Dict[str, Any]) -> float:
        """Convert profitability metrics to 0-100 score."""
        expected_hourly = profitability.get('expected_hourly', 0)
        
        # Normalize to 0-100 scale (assuming $50/hour is excellent)
        if expected_hourly <= 0:
            return 0
        elif expected_hourly >= 50:
            return 100
        else:
            return (expected_hourly / 50) * 100
    
    def _calculate_position_score(self, seat_analysis: Dict[str, Any]) -> float:
        """Convert seat analysis to 0-100 score."""
        if not seat_analysis or not seat_analysis.get('recommended_seat'):
            return 50
            
        best_score = seat_analysis.get('best_score', 50)
        return min(100, best_score)
    
    def _calculate_volume_score(self, table: TableInfo) -> float:
        """Calculate volume score based on table activity."""
        base_score = 50
        
        # Player count bonus/penalty
        fullness_ratio = table.current_players / table.max_players
        if fullness_ratio >= 0.8:
            base_score += 30  # Full table
        elif fullness_ratio <= 0.4:
            base_score -= 20  # Short-handed
        
        # Hands per hour
        if table.hands_per_hour > 100:
            base_score += 20
        elif table.hands_per_hour < 60:
            base_score -= 10
        
        # Waiting list
        if table.waiting_list > 0:
            base_score += 10  # Popular table
        
        return max(0, min(100, base_score))
    
    def _calculate_average_stack_depth(self, table: TableInfo) -> float:
        """Calculate average stack depth in big blinds."""
        if not table.players:
            return 100.0  # Default assumption
        
        stakes_parts = table.stakes.split('/')
        big_blind = float(stakes_parts[1]) if len(stakes_parts) == 2 else 1.0
        
        stacks = [p.stack_size for p in table.players if p.stack_size > 0]
        if not stacks:
            return 100.0
            
        average_stack = statistics.mean(stacks)
        return average_stack / big_blind
    
    def _generate_rating_reasons(self, profitability: Dict[str, Any], pool_analysis: Dict[str, Any],
                                seat_analysis: Dict[str, Any], table: TableInfo) -> List[str]:
        """Generate human-readable reasons for the rating."""
        reasons = []
        
        # Profitability reasons
        expected_hourly = profitability.get('expected_hourly', 0)
        if expected_hourly > 20:
            reasons.append(f"High expected hourly rate: ${expected_hourly:.2f}")
        elif expected_hourly < 5:
            reasons.append(f"Low expected hourly rate: ${expected_hourly:.2f}")
        
        # Player pool reasons
        fish_count = profitability.get('fish_count', 0)
        if fish_count > 2:
            reasons.append(f"Good fish count: {fish_count} recreational players")
        elif fish_count == 0:
            reasons.append("No obvious recreational players")
        
        # Pool type
        pool_type = pool_analysis.get('pool_type', 'unknown')
        if pool_type in ['very_soft', 'soft']:
            reasons.append("Soft player pool detected")
        elif pool_type == 'tough':
            reasons.append("Tough player pool - proceed with caution")
        
        # Position reasons
        if seat_analysis:
            recommended_seat = seat_analysis.get('recommended_seat')
            if recommended_seat:
                reasons.append(f"Recommended seat: {recommended_seat.value}")
        
        # Volume reasons
        fullness = table.current_players / table.max_players
        if fullness >= 0.8:
            reasons.append("Full table - good action")
        elif fullness <= 0.5:
            reasons.append("Short-handed table")
        
        if table.waiting_list > 0:
            reasons.append(f"Popular table ({table.waiting_list} waiting)")
            
        return reasons

# Utility functions for standalone use
def analyze_single_table(table: TableInfo, hero_stats: Dict[str, float] = None) -> GameRating:
    """Analyze a single table without full engine setup."""
    engine = GameSelectionEngine(hero_stats)
    return engine.rate_table(table)

def find_best_tables(tables: List[TableInfo], count: int = 3, 
                    hero_stats: Dict[str, float] = None) -> List[GameRating]:
    """Find the best tables from a list."""
    engine = GameSelectionEngine(hero_stats)
    all_ratings = engine.rate_all_tables(tables)
    return all_ratings[:count]

def create_sample_player(player_id: str, vpip: float, pfr: float, 
                        skill_level: str = "recreational") -> PlayerProfile:
    """Create a sample player for testing."""
    aggression_factor = 2.5 if skill_level in ['regular', 'pro'] else 1.5
    win_rate = {
        'fish': -5.0,
        'recreational': -2.0,
        'regular': 3.0,
        'pro': 8.0
    }.get(skill_level, 0.0)
    
    return PlayerProfile(
        player_id=player_id,
        name=f"Player_{player_id}",
        vpip=vpip,
        pfr=pfr,
        aggression_factor=aggression_factor,
        hands_played=random.randint(100, 5000),
        win_rate=win_rate,
        is_regular=(skill_level in ['regular', 'pro']),
        skill_level=skill_level,
        stack_size=random.uniform(80, 200)
    )

if __name__ == '__main__':
    # Test game selection system
    print("Game Selection Tool Test")
    
    # Create sample tables
    tables = []
    
    # Table 1: Soft game
    soft_players = [
        create_sample_player("fish1", 45, 8, "fish"),
        create_sample_player("fish2", 50, 10, "fish"),
        create_sample_player("rec1", 35, 15, "recreational"),
        create_sample_player("rec2", 40, 18, "recreational"),
        create_sample_player("reg1", 22, 16, "regular"),
        create_sample_player("hero", 23, 18, "regular")
    ]
    
    table1 = TableInfo(
        table_id="Table_001",
        site="PokerStars",
        game_type=GameType.CASH_NLHE,
        stakes="0.25/0.50",
        max_players=6,
        current_players=6,
        average_pot=15.50,
        hands_per_hour=85,
        players=soft_players
    )
    tables.append(table1)
    
    # Table 2: Tough game
    tough_players = [
        create_sample_player("pro1", 21, 17, "pro"),
        create_sample_player("pro2", 19, 16, "pro"),
        create_sample_player("reg1", 22, 18, "regular"),
        create_sample_player("reg2", 20, 17, "regular"),
        create_sample_player("rec1", 28, 12, "recreational"),
        create_sample_player("hero", 23, 18, "regular")
    ]
    
    table2 = TableInfo(
        table_id="Table_002",
        site="PokerStars", 
        game_type=GameType.CASH_NLHE,
        stakes="0.25/0.50",
        max_players=6,
        current_players=6,
        average_pot=12.75,
        hands_per_hour=75,
        players=tough_players
    )
    tables.append(table2)
    
    # Test game selection engine
    engine = GameSelectionEngine()
    
    print(f"\nAnalyzing {len(tables)} tables...")
    
    # Rate all tables
    ratings = engine.rate_all_tables(tables)
    
    print(f"\nTable Rankings:")
    for i, rating in enumerate(ratings, 1):
        print(f"\n{i}. {rating.table_id}")
        print(f"   Overall Rating: {rating.overall_rating:.1f}/100")
        print(f"   Expected Hourly: ${rating.expected_hourly:.2f}")
        print(f"   Fish Count: {rating.fish_count}")
        print(f"   Profitability Score: {rating.profitability_score:.1f}")
        print(f"   Player Pool Score: {rating.player_pool_score:.1f}")
        print(f"   Reasons:")
        for reason in rating.reasons:
            print(f"     - {reason}")
    
    # Test individual components
    print(f"\n--- Component Tests ---")
    
    # Test player pool analyzer
    analyzer = PlayerPoolAnalyzer()
    pool_analysis = analyzer.analyze_player_pool(soft_players)
    print(f"\nSoft Table Pool Analysis:")
    print(f"Pool Type: {pool_analysis['pool_type']}")
    print(f"Exploitability Score: {pool_analysis['exploitability_score']:.1f}")
    print(f"Fish Percentage: {pool_analysis['fish_percentage']:.1f}%")
    print(f"Recommendation: {pool_analysis['recommendation']}")
    
    # Test seat selector
    selector = SeatSelector()
    available_seats = [TablePosition.BUTTON, TablePosition.CUTOFF, TablePosition.BIG_BLIND]
    seat_analysis = selector.analyze_seat_selection(table1, available_seats)
    print(f"\nSeat Selection Analysis:")
    print(f"Recommended Seat: {seat_analysis['recommended_seat'].value if seat_analysis['recommended_seat'] else 'None'}")
    print(f"Reasoning: {seat_analysis['reasoning']}")
    
    print(f"\nGame selection tool test completed!")
