"""
Advanced feature tests for TODO items: Hand Replay, Bankroll Management, 
Tournament Support, Range Construction, and Statistics Dashboard.
"""

import unittest
import tempfile
import shutil
import time
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pokertool.core import Card, Rank, Suit, parse_card, analyse_hand


class HandReplaySystem:
    """Hand replay system for visual hand replay (REPLAY-001)."""
    
    def __init__(self):
        self.replays = {}
        self.animations = {}
        
    def create_replay(self, hand_id, hand_history, metadata=None):
        """Create a new hand replay."""
        replay = {
            'hand_id': hand_id,
            'history': hand_history,
            'metadata': metadata or {},
            'created_at': time.time(),
            'frames': [],
            'annotations': [],
            'sharing_enabled': False
        }
        
        # Generate animation frames
        frames = self._generate_animation_frames(hand_history)
        replay['frames'] = frames
        
        self.replays[hand_id] = replay
        return hand_id
    
    def _generate_animation_frames(self, hand_history):
        """Generate animation frames from hand history."""
        frames = []
        
        # Starting frame
        frames.append({
            'type': 'deal',
            'cards': hand_history.get('hole_cards', []),
            'pot': 0,
            'timestamp': 0,
            'action': 'Deal hole cards'
        })
        
        # Action frames
        actions = hand_history.get('actions', [])
        for i, (street, action, amount) in enumerate(actions):
            frame = {
                'type': 'action',
                'street': street,
                'action': action,
                'amount': amount,
                'pot': hand_history.get('pot_progression', [0] * (i + 1))[min(i, len(hand_history.get('pot_progression', [])) - 1)],
                'timestamp': (i + 1) * 1000,  # 1 second per action
                'board_cards': self._get_board_for_street(street, hand_history)
            }
            frames.append(frame)
        
        # Showdown frame if applicable
        if hand_history.get('showdown'):
            frames.append({
                'type': 'showdown',
                'revealed_cards': hand_history.get('opponent_cards', []),
                'winner': hand_history.get('winner'),
                'pot': hand_history.get('final_pot', 0),
                'timestamp': len(actions) * 1000 + 2000
            })
        
        return frames
    
    def _get_board_for_street(self, street, hand_history):
        """Get board cards for a given street."""
        board = hand_history.get('board_cards', [])
        if street == 'preflop':
            return []
        elif street == 'flop':
            return board[:3]
        elif street == 'turn':
            return board[:4]
        elif street == 'river':
            return board[:5]
        return board
    
    def add_annotation(self, hand_id, frame_index, annotation):
        """Add annotation to a specific frame."""
        if hand_id in self.replays:
            annotation_data = {
                'frame_index': frame_index,
                'text': annotation,
                'timestamp': time.time(),
                'type': 'user'
            }
            self.replays[hand_id]['annotations'].append(annotation_data)
            return True
        return False
    
    def enable_sharing(self, hand_id):
        """Enable sharing for a replay."""
        if hand_id in self.replays:
            self.replays[hand_id]['sharing_enabled'] = True
            # Generate shareable link
            share_code = f"replay_{hand_id}_{int(time.time())}"
            self.replays[hand_id]['share_code'] = share_code
            return share_code
        return None
    
    def get_replay(self, hand_id):
        """Get replay data."""
        return self.replays.get(hand_id)
    
    def get_replay_interface_data(self, hand_id):
        """Get data formatted for replay interface."""
        replay = self.get_replay(hand_id)
        if not replay:
            return None
            
        return {
            'hand_id': hand_id,
            'frames': replay['frames'],
            'annotations': replay['annotations'],
            'metadata': replay['metadata'],
            'duration': max(frame['timestamp'] for frame in replay['frames']) if replay['frames'] else 0,
            'sharing_enabled': replay['sharing_enabled']
        }


class BankrollManager:
    """Bankroll management system (BANK-001)."""
    
    def __init__(self):
        self.transactions = []
        self.bankroll_history = []
        self.current_bankroll = 0.0
        self.risk_settings = {
            'max_buy_in_percent': 5.0,  # 5% of bankroll max
            'stop_loss_percent': 50.0,   # Stop at 50% loss
            'kelly_multiplier': 0.25     # Conservative Kelly
        }
    
    def add_transaction(self, amount, transaction_type, description="", game_type="", stakes=""):
        """Add a bankroll transaction."""
        transaction = {
            'id': len(self.transactions) + 1,
            'amount': float(amount),
            'type': transaction_type,
            'description': description,
            'game_type': game_type,
            'stakes': stakes,
            'timestamp': time.time(),
            'balance_after': self.current_bankroll + amount
        }
        
        self.transactions.append(transaction)
        self.current_bankroll += amount
        
        # Record bankroll history point
        self.bankroll_history.append({
            'timestamp': transaction['timestamp'],
            'balance': self.current_bankroll,
            'change': amount,
            'transaction_id': transaction['id']
        })
        
        return transaction['id']
    
    def calculate_kelly_criterion(self, win_rate, average_win, average_loss):
        """Calculate Kelly Criterion for optimal bet sizing."""
        if average_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
            
        b = average_win / average_loss  # Ratio of win to loss
        p = win_rate                     # Probability of winning
        q = 1 - p                       # Probability of losing
        
        kelly_fraction = (b * p - q) / b
        
        # Apply conservative multiplier
        kelly_fraction *= self.risk_settings['kelly_multiplier']
        
        return max(0.0, kelly_fraction)
    
    def get_recommended_buy_in(self, stakes_level):
        """Get recommended buy-in for stakes level."""
        max_buy_in = self.current_bankroll * (self.risk_settings['max_buy_in_percent'] / 100)
        
        # Standard buy-in recommendations by stakes
        standard_multipliers = {
            'micro': 20,    # 20x big blind
            'low': 40,      # 40x big blind  
            'mid': 60,      # 60x big blind
            'high': 80,     # 80x big blind
            'nosebleed': 100  # 100x big blind
        }
        
        # Parse stakes (e.g., "0.01/0.02" -> 0.02 big blind)
        if '/' in stakes_level:
            bb = float(stakes_level.split('/')[1])
            multiplier = standard_multipliers.get('mid', 40)  # Default
            recommended = bb * multiplier
        else:
            recommended = max_buy_in * 0.1  # Fallback
        
        return min(recommended, max_buy_in)
    
    def calculate_risk_of_ruin(self, win_rate_bb_per_100, std_dev_bb_per_100, num_hands=10000):
        """Calculate risk of ruin using Monte Carlo simulation."""
        if self.current_bankroll <= 0:
            return 1.0
            
        bankroll_bb = self.current_bankroll / 2.0  # Assume $2 BB for calculation
        win_rate = win_rate_bb_per_100 / 100.0
        std_dev = std_dev_bb_per_100 / 100.0
        
        # Simple approximation for risk of ruin
        if win_rate <= 0:
            return 1.0
            
        # Use normal approximation for large sample
        z_score = bankroll_bb / (std_dev * np.sqrt(num_hands))
        risk = 1.0 / (1.0 + np.exp(2 * win_rate * z_score))
        
        return min(1.0, max(0.0, risk))
    
    def get_variance_analysis(self, days=30):
        """Get variance analysis for recent period."""
        cutoff_time = time.time() - (days * 24 * 3600)
        recent_transactions = [t for t in self.transactions if t['timestamp'] > cutoff_time]
        
        if len(recent_transactions) < 2:
            return {
                'variance': 0.0,
                'standard_deviation': 0.0,
                'confidence_interval': (0.0, 0.0),
                'sample_size': len(recent_transactions)
            }
        
        amounts = [t['amount'] for t in recent_transactions]
        mean = np.mean(amounts)
        variance = np.var(amounts, ddof=1)
        std_dev = np.sqrt(variance)
        
        # 95% confidence interval
        ci_range = 1.96 * std_dev / np.sqrt(len(amounts))
        confidence_interval = (mean - ci_range, mean + ci_range)
        
        return {
            'variance': variance,
            'standard_deviation': std_dev,
            'confidence_interval': confidence_interval,
            'mean_result': mean,
            'sample_size': len(recent_transactions)
        }
    
    def get_bankroll_alerts(self):
        """Get bankroll-related alerts."""
        alerts = []
        
        # Check for significant losses
        if len(self.bankroll_history) >= 2:
            recent_change = self.current_bankroll - self.bankroll_history[-2]['balance']
            loss_percent = abs(recent_change) / self.current_bankroll * 100
            
            if recent_change < 0 and loss_percent > 10:
                alerts.append({
                    'type': 'warning',
                    'message': f'Significant loss detected: {loss_percent:.1f}%',
                    'severity': 'medium'
                })
        
        # Check bankroll minimum
        if self.current_bankroll < 1000:  # Arbitrary minimum
            alerts.append({
                'type': 'danger',
                'message': 'Bankroll below recommended minimum',
                'severity': 'high'
            })
        
        return alerts


class TournamentSupport:
    """Tournament-specific features (TOUR-001)."""
    
    def __init__(self):
        self.icm_cache = {}
    
    def calculate_icm(self, stacks, payouts):
        """Calculate Independent Chip Model equity."""
        cache_key = f"{tuple(stacks)}_{tuple(payouts)}"
        if cache_key in self.icm_cache:
            return self.icm_cache[cache_key]
        
        n_players = len(stacks)
        total_chips = sum(stacks)
        
        if n_players != len(payouts):
            raise ValueError("Number of players must match number of payouts")
        
        # Simple ICM calculation (approximation for small fields)
        equities = []
        for i, stack in enumerate(stacks):
            equity = 0.0
            chip_percentage = stack / total_chips
            
            # Weight by payout structure
            for j, payout in enumerate(payouts):
                if j < n_players:
                    # Probability of finishing in position j+1
                    prob = self._calculate_finish_probability(i, j, stacks)
                    equity += prob * payout
            
            equities.append(equity)
        
        self.icm_cache[cache_key] = equities
        return equities
    
    def _calculate_finish_probability(self, player_idx, finish_pos, stacks):
        """Calculate probability of player finishing in given position."""
        total_chips = sum(stacks)
        player_chips = stacks[player_idx]
        
        # Simplified calculation - in reality this requires complex combinatorics
        base_prob = player_chips / total_chips
        
        # Adjust for finishing position
        if finish_pos == 0:  # First place
            return base_prob * 1.2
        elif finish_pos == len(stacks) - 1:  # Last place
            return (1 - base_prob) * 0.8
        else:
            return base_prob
    
    def calculate_bubble_factor(self, stacks, payouts, players_paid):
        """Calculate bubble factor for tournament decisions."""
        if len(stacks) <= players_paid:
            return 1.0  # Already in the money
        
        # Calculate how much equity is at stake
        min_payout = min(payouts[:players_paid])
        current_icm = self.calculate_icm(stacks, payouts + [0] * (len(stacks) - len(payouts)))
        
        player_idx = 0  # Assume we're calculating for first player
        current_equity = current_icm[player_idx]
        
        # Bubble factor is the ratio of chip EV to $ EV
        chip_percentage = stacks[player_idx] / sum(stacks)
        bubble_factor = chip_percentage / (current_equity / sum(payouts[:players_paid]))
        
        return max(0.1, min(10.0, bubble_factor))  # Reasonable bounds
    
    def generate_push_fold_chart(self, position, num_players, ante_structure):
        """Generate push/fold chart for tournament play."""
        chart = {}
        
        # Simplified hand rankings
        hand_rankings = [
            'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55',
            'AKs', 'AQs', 'AJs', 'ATs', 'AKo', 'AQo', 'AJo', 'ATo',
            '44', '33', '22', 'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs'
        ]
        
        # Calculate push ranges based on stack size (in BBs)
        for bb_stack in range(1, 21):  # 1-20 BB stacks
            push_range = []
            fold_range = []
            
            # More aggressive with shorter stacks
            push_threshold = min(len(hand_rankings), int(len(hand_rankings) * (21 - bb_stack) / 20))
            
            for i, hand in enumerate(hand_rankings):
                if i < push_threshold:
                    push_range.append(hand)
                else:
                    fold_range.append(hand)
            
            chart[bb_stack] = {
                'push': push_range,
                'fold': fold_range,
                'push_percentage': len(push_range) / len(hand_rankings) * 100
            }
        
        return chart
    
    def analyze_final_table_icm(self, stacks, payouts, position):
        """Analyze ICM considerations for final table play."""
        icm_equity = self.calculate_icm(stacks, payouts)
        player_equity = icm_equity[position]
        
        # Calculate ICM pressure
        total_prize_pool = sum(payouts)
        chip_equity = stacks[position] / sum(stacks) * total_prize_pool
        icm_pressure = (chip_equity - player_equity) / chip_equity if chip_equity > 0 else 0
        
        # Calculate optimal strategy adjustments
        strategy_adjustments = {
            'tighten_calling_range': icm_pressure > 0.1,
            'avoid_marginal_spots': icm_pressure > 0.2,
            'ladder_considerations': len(stacks) <= 5,
            'icm_pressure_level': icm_pressure
        }
        
        return {
            'icm_equity': player_equity,
            'chip_equity': chip_equity,
            'icm_pressure': icm_pressure,
            'strategy_adjustments': strategy_adjustments,
            'position': position,
            'players_remaining': len(stacks)
        }


class RangeConstructionTool:
    """Visual range construction interface (RANGE-001)."""
    
    def __init__(self):
        self.ranges = {}
        self.templates = self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default range templates."""
        return {
            'tight': {
                'pairs': ['AA', 'KK', 'QQ', 'JJ', 'TT'],
                'suited': ['AKs', 'AQs', 'AJs', 'KQs'],
                'offsuit': ['AKo', 'AQo']
            },
            'loose': {
                'pairs': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66'],
                'suited': ['AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'KQs', 'KJs', 'KTs', 'QJs'],
                'offsuit': ['AKo', 'AQo', 'AJo', 'KQo']
            },
            'utg': {
                'pairs': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99'],
                'suited': ['AKs', 'AQs', 'AJs', 'ATs', 'KQs', 'KJs'],
                'offsuit': ['AKo', 'AQo', 'AJo']
            },
            'button': {
                'pairs': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22'],
                'suited': ['AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
                          'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'QJs', 'QTs', 'Q9s', 'JTs', 'J9s', 'T9s', '98s'],
                'offsuit': ['AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'KQo', 'KJo', 'KTo', 'QJo', 'QTo', 'JTo']
            }
        }
    
    def create_range(self, name, hands=None, template=None):
        """Create a new range."""
        if template and template in self.templates:
            range_data = self.templates[template].copy()
        else:
            range_data = {'pairs': [], 'suited': [], 'offsuit': []}
        
        if hands:
            self._add_hands_to_range_data(range_data, hands)
        
        self.ranges[name] = {
            'data': range_data,
            'created_at': time.time(),
            'frequency': self._calculate_range_frequency(range_data)
        }
        
        return name
    
    def _add_hands_to_range_data(self, range_data, hands):
        """Add hands to range data structure."""
        for hand in hands:
            if self._is_pair(hand):
                if hand not in range_data['pairs']:
                    range_data['pairs'].append(hand)
            elif self._is_suited(hand):
                if hand not in range_data['suited']:
                    range_data['suited'].append(hand)
            else:
                if hand not in range_data['offsuit']:
                    range_data['offsuit'].append(hand)
    
    def _is_pair(self, hand):
        """Check if hand is a pair."""
        return len(hand) == 2 and hand[0] == hand[1]
    
    def _is_suited(self, hand):
        """Check if hand is suited."""
        return hand.endswith('s')
    
    def _calculate_range_frequency(self, range_data):
        """Calculate the frequency percentage of a range."""
        total_combos = 0
        
        # Count pair combinations (6 each)
        total_combos += len(range_data['pairs']) * 6
        
        # Count suited combinations (4 each)
        total_combos += len(range_data['suited']) * 4
        
        # Count offsuit combinations (12 each)
        total_combos += len(range_data['offsuit']) * 12
        
        # Total possible combinations is 1326
        return (total_combos / 1326) * 100
    
    def add_hand_to_range(self, range_name, hand):
        """Add a hand to an existing range."""
        if range_name not in self.ranges:
            return False
        
        range_data = self.ranges[range_name]['data']
        self._add_hands_to_range_data(range_data, [hand])
        
        # Recalculate frequency
        self.ranges[range_name]['frequency'] = self._calculate_range_frequency(range_data)
        return True
    
    def remove_hand_from_range(self, range_name, hand):
        """Remove a hand from an existing range."""
        if range_name not in self.ranges:
            return False
        
        range_data = self.ranges[range_name]['data']
        
        for category in ['pairs', 'suited', 'offsuit']:
            if hand in range_data[category]:
                range_data[category].remove(hand)
                break
        
        # Recalculate frequency
        self.ranges[range_name]['frequency'] = self._calculate_range_frequency(range_data)
        return True
    
    def compare_ranges(self, range1_name, range2_name):
        """Compare two ranges and return overlap/differences."""
        if range1_name not in self.ranges or range2_name not in self.ranges:
            return None
        
        range1 = self.ranges[range1_name]['data']
        range2 = self.ranges[range2_name]['data']
        
        # Flatten ranges to sets
        range1_hands = set(range1['pairs'] + range1['suited'] + range1['offsuit'])
        range2_hands = set(range2['pairs'] + range2['suited'] + range2['offsuit'])
        
        overlap = range1_hands & range2_hands
        only_in_range1 = range1_hands - range2_hands
        only_in_range2 = range2_hands - range1_hands
        
        return {
            'overlap': list(overlap),
            'overlap_percentage': len(overlap) / len(range1_hands | range2_hands) * 100 if range1_hands | range2_hands else 0,
            'only_in_range1': list(only_in_range1),
            'only_in_range2': list(only_in_range2),
            'range1_frequency': self.ranges[range1_name]['frequency'],
            'range2_frequency': self.ranges[range2_name]['frequency']
        }
    
    def export_range(self, range_name, format_type='pokerstove'):
        """Export range in specified format."""
        if range_name not in self.ranges:
            return None
        
        range_data = self.ranges[range_name]['data']
        all_hands = range_data['pairs'] + range_data['suited'] + range_data['offsuit']
        
        if format_type == 'pokerstove':
            return ', '.join(all_hands)
        elif format_type == 'json':
            return json.dumps(range_data)
        elif format_type == 'list':
            return all_hands
        else:
            return ', '.join(all_hands)  # Default to pokerstove format


class StatsDashboard:
    """Comprehensive statistics dashboard (STATS-001)."""
    
    def __init__(self):
        self.sessions = []
        self.custom_reports = {}
    
    def add_session(self, session_data):
        """Add a poker session to the database."""
        session = {
            'id': len(self.sessions) + 1,
            'timestamp': session_data.get('timestamp', time.time()),
            'duration': session_data.get('duration', 0),
            'hands_played': session_data.get('hands_played', 0),
            'profit_loss': session_data.get('profit_loss', 0.0),
            'game_type': session_data.get('game_type', 'Unknown'),
            'stakes': session_data.get('stakes', 'Unknown'),
            'location': session_data.get('location', 'Online'),
            'notes': session_data.get('notes', ''),
            'vpip': session_data.get('vpip', 0.0),
            'pfr': session_data.get('pfr', 0.0),
            'aggression_factor': session_data.get('aggression_factor', 0.0)
        }
        
        self.sessions.append(session)
        return session['id']
    
    def get_dashboard_data(self, days=30):
        """Get dashboard data for specified time period."""
        cutoff_time = time.time() - (days * 24 * 3600)
        recent_sessions = [s for s in self.sessions if s['timestamp'] > cutoff_time]
        
        if not recent_sessions:
            return self._empty_dashboard()
        
        # Calculate basic stats
        total_profit = sum(s['profit_loss'] for s in recent_sessions)
        total_hands = sum(s['hands_played'] for s in recent_sessions)
        total_time = sum(s['duration'] for s in recent_sessions)
        
        # Calculate rates
        profit_per_hour = (total_profit / (total_time / 3600)) if total_time > 0 else 0
        bb_per_100 = self._calculate_bb_per_100(recent_sessions)
        
        # Calculate averages
        avg_vpip = np.mean([s['vpip'] for s in recent_sessions if s['vpip'] > 0])
        avg_pfr = np.mean([s['pfr'] for s in recent_sessions if s['pfr'] > 0])
        avg_aggression = np.mean([s['aggression_factor'] for s in recent_sessions if s['aggression_factor'] > 0])
        
        # Win rate calculation
        winning_sessions = len([s for s in recent_sessions if s['profit_loss'] > 0])
        win_rate = (winning_sessions / len(recent_sessions)) * 100
        
        # Variance calculation
        profit_variance = np.var([s['profit_loss'] for s in recent_sessions]) if len(recent_sessions) > 1 else 0
        
        return {
            'period_days': days,
            'sessions_played': len(recent_sessions),
            'total_hands': total_hands,
            'total_time_hours': total_time / 3600,
            'total_profit': total_profit,
            'profit_per_hour': profit_per_hour,
            'bb_per_100_hands': bb_per_100,
            'session_win_rate': win_rate,
            'avg_vpip': avg_vpip,
            'avg_pfr': avg_pfr,
            'avg_aggression_factor': avg_aggression,
            'profit_variance': profit_variance,
            'best_session': max(recent_sessions, key=lambda s: s['profit_loss'])['profit_loss'],
            'worst_session': min(recent_sessions, key=lambda s: s['profit_loss'])['profit_loss'],
            'graph_data': self._generate_graph_data(recent_sessions)
        }
    
    def _empty_dashboard(self):
        """Return empty dashboard data."""
        return {
            'sessions_played': 0,
            'total_hands': 0,
            'total_time_hours': 0,
            'total_profit': 0,
            'profit_per_hour': 0,
            'bb_per_100_hands': 0,
            'session_win_rate': 0,
            'avg_vpip': 0,
            'avg_pfr': 0,
            'avg_aggression_factor': 0,
            'graph_data': {'x': [], 'y': []}
        }
    
    def _calculate_bb_per_100(self, sessions):
        """Calculate big blinds per 100 hands."""
        total_profit = sum(s['profit_loss'] for s in sessions)
        total_hands = sum(s['hands_played'] for s in sessions)
        
        if total_hands == 0:
            return 0
        
        # Estimate big blind size from stakes
        avg_bb = self._estimate_big_blind(sessions)
        
        return (total_profit / avg_bb) * (100 / total_hands) if avg_bb > 0 else 0
    
    def _estimate_big_blind(self, sessions):
        """Estimate average big blind from session data."""
        # Simple estimation - in practice this would be more sophisticated
        stakes_examples = {
            '0.01/0.02': 0.02,
            '0.02/0.05': 0.05,
            '0.05/0.10': 0.10,
            '0.10/0.25': 0.25,
            '0.25/0.50': 0.50,
            '0.50/1.00': 1.00,
            '1.00/2.00': 2.00
        }
        
        # Find most common stakes format
        stakes_counter = {}
        for session in sessions:
            stakes = session.get('stakes', 'Unknown')
            stakes_counter[stakes] = stakes_counter.get(stakes, 0) + 1
        
        if not stakes_counter:
            return 1.0  # Default fallback
        
        most_common_stakes = max(stakes_counter, key=stakes_counter.get)
        return stakes_examples.get(most_common_stakes, 1.0)
    
    def _generate_graph_data(self, sessions):
        """Generate graph data for profit/loss over time."""
        if not sessions:
            return {'x': [], 'y': []}
        
        # Sort by timestamp
        sorted_sessions = sorted(sessions, key=lambda s: s['timestamp'])
        
        cumulative_profit = 0
        x_data = []
        y_data = []
        
        for session in sorted_sessions:
            cumulative_profit += session['profit_loss']
            x_data.append(session['timestamp'])
            y_data.append(cumulative_profit)
        
        return {'x': x_data, 'y': y_data}
    
    def create_custom_report(self, name, filters, metrics):
        """Create a custom report with filters and metrics."""
        self.custom_reports[name] = {
            'filters': filters,
            'metrics': metrics,
            'created_at': time.time()
        }
        return name
    
    def generate_custom_report(self, report_name):
        """Generate data for a custom report."""
        if report_name not in self.custom_reports:
            return None
        
        report_config = self.custom_reports[report_name]
        filters = report_config['filters']
        metrics = report_config['metrics']
        
        # Apply filters
        filtered_sessions = self.sessions
        
        if 'date_range' in filters:
            start_time, end_time = filters['date_range']
            filtered_sessions = [s for s in filtered_sessions 
                               if start_time <= s['timestamp'] <= end_time]
        
        if 'game_type' in filters:
            game_type = filters['game_type']
            filtered_sessions = [s for s in filtered_sessions 
                               if s['game_type'] == game_type]
        
        if 'stakes' in filters:
            stakes = filters['stakes']
            filtered_sessions = [s for s in filtered_sessions 
                               if s['stakes'] == stakes]
        
        if 'min_profit' in filters:
            min_profit = filters['min_profit']
            filtered_sessions = [s for s in filtered_sessions 
                               if s['profit_loss'] >= min_profit]
        
        # Calculate metrics
        results = {}
        
        if 'total_profit' in metrics and filtered_sessions:
            results['total_profit'] = sum(s['profit_loss'] for s in filtered_sessions)
        
        if 'session_count' in metrics:
            results['session_count'] = len(filtered_sessions)
        
        if 'avg_profit_per_session' in metrics and filtered_sessions:
            results['avg_profit_per_session'] = sum(s['profit_loss'] for s in filtered_sessions) / len(filtered_sessions)
        
        if 'total_hands' in metrics and filtered_sessions:
            results['total_hands'] = sum(s['hands_played'] for s in filtered_sessions)
        
        if 'win_rate' in metrics and filtered_sessions:
            winning_sessions = len([s for s in filtered_sessions if s['profit_loss'] > 0])
            results['win_rate'] = (winning_sessions / len(filtered_sessions)) * 100
        
        return {
            'report_name': report_name,
            'filters_applied': filters,
            'session_count': len(filtered_sessions),
            'results': results,
            'generated_at': time.time()
        }


# Test Classes

class TestHandReplaySystem(unittest.TestCase):
    """Test hand replay functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.replay_system = HandReplaySystem()
        self.sample_history = {
            'hole_cards': ['As', 'Kh'],
            'board_cards': ['7d', '8d', '9c', 'Th', 'Js'],
            'actions': [
                ('preflop', 'raise', 3),
                ('flop', 'bet', 5),
                ('turn', 'check', 0),
                ('river', 'bet', 10)
            ],
            'pot_progression': [6, 16, 16, 36],
            'showdown': True,
            'opponent_cards': ['Qc', 'Td'],
            'winner': 'hero',
            'final_pot': 36
        }
    
    def test_create_replay(self):
        """Test replay creation."""
        replay_id = self.replay_system.create_replay('test_hand_1', self.sample_history)
        
        self.assertEqual(replay_id, 'test_hand_1')
        self.assertIn('test_hand_1', self.replay_system.replays)
        
        replay = self.replay_system.get_replay('test_hand_1')
        self.assertIsNotNone(replay)
        self.assertEqual(replay['hand_id'], 'test_hand_1')
        self.assertGreater(len(replay['frames']), 0)
    
    def test_animation_frame_generation(self):
        """Test animation frame generation."""
        replay_id = self.replay_system.create_replay('test_hand_2', self.sample_history)
        replay = self.replay_system.get_replay(replay_id)
        
        frames = replay['frames']
        
        # Should have deal frame + action frames + showdown frame
        expected_frame_count = 1 + len(self.sample_history['actions']) + 1
        self.assertEqual(len(frames), expected_frame_count)
        
        # Check first frame (deal)
        self.assertEqual(frames[0]['type'], 'deal')
        self.assertEqual(frames[0]['cards'], ['As', 'Kh'])
        
        # Check action frames
        for i, (street, action, amount) in enumerate(self.sample_history['actions']):
            frame = frames[i + 1]
            self.assertEqual(frame['type'], 'action')
            self.assertEqual(frame['street'], street)
            self.assertEqual(frame['action'], action)
            self.assertEqual(frame['amount'], amount)
        
        # Check showdown frame
        showdown_frame = frames[-1]
        self.assertEqual(showdown_frame['type'], 'showdown')
        self.assertEqual(showdown_frame['revealed_cards'], ['Qc', 'Td'])
        self.assertEqual(showdown_frame['winner'], 'hero')
    
    def test_add_annotation(self):
        """Test adding annotations to replays."""
        replay_id = self.replay_system.create_replay('test_hand_3', self.sample_history)
        
        result = self.replay_system.add_annotation(replay_id, 2, 'Good bet sizing here')
        self.assertTrue(result)
        
        replay = self.replay_system.get_replay(replay_id)
        annotations = replay['annotations']
        
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0]['frame_index'], 2)
        self.assertEqual(annotations[0]['text'], 'Good bet sizing here')
        self.assertEqual(annotations[0]['type'], 'user')
    
    def test_sharing_functionality(self):
        """Test replay sharing functionality."""
        replay_id = self.replay_system.create_replay('test_hand_4', self.sample_history)
        
        share_code = self.replay_system.enable_sharing(replay_id)
        self.assertIsNotNone(share_code)
        self.assertTrue(share_code.startswith('replay_'))
        
        replay = self.replay_system.get_replay(replay_id)
        self.assertTrue(replay['sharing_enabled'])
        self.assertEqual(replay['share_code'], share_code)
    
    def test_replay_interface_data(self):
        """Test replay interface data formatting."""
        replay_id = self.replay_system.create_replay('test_hand_5', self.sample_history)
        self.replay_system.add_annotation(replay_id, 1, 'Test annotation')
        
        interface_data = self.replay_system.get_replay_interface_data(replay_id)
        
        self.assertIsNotNone(interface_data)
        self.assertEqual(interface_data['hand_id'], replay_id)
        self.assertIn('frames', interface_data)
        self.assertIn('annotations', interface_data)
        self.assertIn('duration', interface_data)
        self.assertGreater(interface_data['duration'], 0)


class TestBankrollManager(unittest.TestCase):
    """Test bankroll management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = BankrollManager()
        # Add some initial bankroll
        self.manager.add_transaction(5000, 'deposit', 'Initial deposit')
    
    def test_transaction_management(self):
        """Test transaction addition and tracking."""
        initial_balance = self.manager.current_bankroll
        
        transaction_id = self.manager.add_transaction(100, 'win', 'Good session', 'NLHE', '0.05/0.10')
        
        self.assertIsInstance(transaction_id, int)
        self.assertEqual(self.manager.current_bankroll, initial_balance + 100)
        self.assertEqual(len(self.manager.transactions), 2)  # Initial + new
        
        # Check transaction data
        transaction = self.manager.transactions[-1]
        self.assertEqual(transaction['amount'], 100)
        self.assertEqual(transaction['type'], 'win')
        self.assertEqual(transaction['game_type'], 'NLHE')
        self.assertEqual(transaction['stakes'], '0.05/0.10')
    
    def test_kelly_criterion_calculation(self):
        """Test Kelly Criterion calculation."""
        # Test valid inputs
        kelly = self.manager.calculate_kelly_criterion(0.6, 100, 80)
        self.assertGreater(kelly, 0)
        self.assertLess(kelly, 1)
        
        # Test edge cases
        kelly_zero_win_rate = self.manager.calculate_kelly_criterion(0, 100, 80)
        self.assertEqual(kelly_zero_win_rate, 0)
        
        kelly_100_win_rate = self.manager.calculate_kelly_criterion(1.0, 100, 80)
        self.assertEqual(kelly_100_win_rate, 0)
        
        kelly_negative_loss = self.manager.calculate_kelly_criterion(0.6, 100, 0)
        self.assertEqual(kelly_negative_loss, 0)
    
    def test_recommended_buy_in(self):
        """Test buy-in recommendations."""
        # Test with stakes format
        buy_in = self.manager.get_recommended_buy_in('0.05/0.10')
        self.assertGreater(buy_in, 0)
        self.assertLessEqual(buy_in, self.manager.current_bankroll * 0.05)  # Max 5%
        
        # Test fallback
        buy_in_fallback = self.manager.get_recommended_buy_in('unknown_format')
        self.assertGreater(buy_in_fallback, 0)
    
    def test_risk_of_ruin_calculation(self):
        """Test risk of ruin calculation."""
        # Positive win rate
        risk_positive = self.manager.calculate_risk_of_ruin(5.0, 100.0, 10000)
        self.assertGreaterEqual(risk_positive, 0)
        self.assertLessEqual(risk_positive, 1)
        
        # Negative win rate (should be high risk)
        risk_negative = self.manager.calculate_risk_of_ruin(-5.0, 100.0, 10000)
        self.assertEqual(risk_negative, 1.0)
        
        # Zero bankroll
        self.manager.current_bankroll = 0
        risk_zero = self.manager.calculate_risk_of_ruin(5.0, 100.0, 10000)
        self.assertEqual(risk_zero, 1.0)
    
    def test_variance_analysis(self):
        """Test variance analysis."""
        # Add some transactions with variance
        self.manager.add_transaction(100, 'win')
        self.manager.add_transaction(-50, 'loss')
        self.manager.add_transaction(200, 'win')
        self.manager.add_transaction(-75, 'loss')
        
        analysis = self.manager.get_variance_analysis(days=30)
        
        self.assertIn('variance', analysis)
        self.assertIn('standard_deviation', analysis)
        self.assertIn('confidence_interval', analysis)
        self.assertGreater(analysis['sample_size'], 0)
        
        # Confidence interval should be a tuple
        ci = analysis['confidence_interval']
        self.assertIsInstance(ci, tuple)
        self.assertEqual(len(ci), 2)
    
    def test_bankroll_alerts(self):
        """Test bankroll alert system."""
        # Add a large loss to trigger alert
        self.manager.add_transaction(-600, 'loss', 'Bad session')
        
        alerts = self.manager.get_bankroll_alerts()
        self.assertIsInstance(alerts, list)
        
        # Should have a warning for significant loss
        warning_alerts = [a for a in alerts if a['type'] == 'warning']
        self.assertGreater(len(warning_alerts), 0)
    
    def test_low_bankroll_alert(self):
        """Test low bankroll alert."""
        # Set very low bankroll
        self.manager.current_bankroll = 500
        
        alerts = self.manager.get_bankroll_alerts()
        danger_alerts = [a for a in alerts if a['type'] == 'danger']
        self.assertGreater(len(danger_alerts), 0)


class TestTournamentSupport(unittest.TestCase):
    """Test tournament-specific functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tournament = TournamentSupport()
        self.sample_stacks = [10000, 8000, 6000, 4000, 2000]
        self.sample_payouts = [5000, 3000, 2000, 1000, 500]
    
    def test_icm_calculation(self):
        """Test ICM equity calculation."""
        equities = self.tournament.calculate_icm(self.sample_stacks, self.sample_payouts)
        
        self.assertEqual(len(equities), len(self.sample_stacks))
        self.assertTrue(all(eq >= 0 for eq in equities))
        
        # Largest stack should have highest equity
        max_equity_idx = equities.index(max(equities))
        max_stack_idx = self.sample_stacks.index(max(self.sample_stacks))
        self.assertEqual(max_equity_idx, max_stack_idx)
        
        # Test caching
        equities_cached = self.tournament.calculate_icm(self.sample_stacks, self.sample_payouts)
        self.assertEqual(equities, equities_cached)
    
    def test_icm_validation(self):
        """Test ICM calculation validation."""
        with self.assertRaises(ValueError):
            # Mismatched stacks and payouts
            self.tournament.calculate_icm([1000, 2000], [500])
    
    def test_bubble_factor(self):
        """Test bubble factor calculation."""
        bubble_factor = self.tournament.calculate_bubble_factor(
            self.sample_stacks, self.sample_payouts, 3
        )
        
        self.assertGreater(bubble_factor, 0)
        self.assertLess(bubble_factor, 10)  # Should be within reasonable bounds
        
        # Test already in the money
        itm_factor = self.tournament.calculate_bubble_factor(
            self.sample_stacks[:3], self.sample_payouts[:3], 3
        )
        self.assertEqual(itm_factor, 1.0)
    
    def test_push_fold_chart(self):
        """Test push/fold chart generation."""
        chart = self.tournament.generate_push_fold_chart('BTN', 6, {'ante': 0.1})
        
        self.assertIsInstance(chart, dict)
        self.assertGreater(len(chart), 0)
        
        # Check structure for different stack sizes
        for bb_stack in range(1, 11):
            if bb_stack in chart:
                stack_data = chart[bb_stack]
                self.assertIn('push', stack_data)
                self.assertIn('fold', stack_data)
                self.assertIn('push_percentage', stack_data)
                
                # Shorter stacks should push more
                if bb_stack < 10 and (bb_stack + 1) in chart:
                    current_percentage = stack_data['push_percentage']
                    next_percentage = chart[bb_stack + 1]['push_percentage']
                    self.assertGreaterEqual(current_percentage, next_percentage)
    
    def test_final_table_icm_analysis(self):
        """Test final table ICM analysis."""
        analysis = self.tournament.analyze_final_table_icm(
            self.sample_stacks, self.sample_payouts, 0
        )
        
        self.assertIn('icm_equity', analysis)
        self.assertIn('chip_equity', analysis)
        self.assertIn('icm_pressure', analysis)
        self.assertIn('strategy_adjustments', analysis)
        self.assertIn('position', analysis)
        self.assertIn('players_remaining', analysis)
        
        # Check strategy adjustments structure
        adjustments = analysis['strategy_adjustments']
        self.assertIn('tighten_calling_range', adjustments)
        self.assertIn('avoid_marginal_spots', adjustments)
        self.assertIn('ladder_considerations', adjustments)
        self.assertIn('icm_pressure_level', adjustments)
        
        self.assertEqual(analysis['position'], 0)
        self.assertEqual(analysis['players_remaining'], len(self.sample_stacks))


class TestRangeConstructionTool(unittest.TestCase):
    """Test range construction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.range_tool = RangeConstructionTool()
    
    def test_template_creation(self):
        """Test default template creation."""
        templates = self.range_tool.templates
        
        self.assertIn('tight', templates)
        self.assertIn('loose', templates)
        self.assertIn('utg', templates)
        self.assertIn('button', templates)
        
        # Check template structure
        tight_template = templates['tight']
        self.assertIn('pairs', tight_template)
        self.assertIn('suited', tight_template)
        self.assertIn('offsuit', tight_template)
    
    def test_range_creation(self):
        """Test range creation."""
        # Create from template
        range_name = self.range_tool.create_range('test_tight', template='tight')
        self.assertEqual(range_name, 'test_tight')
        self.assertIn('test_tight', self.range_tool.ranges)
        
        range_data = self.range_tool.ranges['test_tight']
        self.assertIn('data', range_data)
        self.assertIn('frequency', range_data)
        self.assertIn('created_at', range_data)
        self.assertGreater(range_data['frequency'], 0)
        
        # Create with custom hands
        custom_hands = ['AA', 'KKs', 'AKo']  # Note: KKs is invalid, should be handled
        custom_range = self.range_tool.create_range('custom', hands=custom_hands)
        self.assertIn('custom', self.range_tool.ranges)
    
    def test_hand_categorization(self):
        """Test hand categorization logic."""
        # Test pair detection
        self.assertTrue(self.range_tool._is_pair('AA'))
        self.assertFalse(self.range_tool._is_pair('AK'))
        
        # Test suited detection
        self.assertTrue(self.range_tool._is_suited('AKs'))
        self.assertFalse(self.range_tool._is_suited('AKo'))
        self.assertFalse(self.range_tool._is_suited('AA'))
    
    def test_frequency_calculation(self):
        """Test range frequency calculation."""
        # Create range with known hands
        self.range_tool.create_range('freq_test', hands=['AA', 'AKs', 'AKo'])
        
        freq = self.range_tool.ranges['freq_test']['frequency']
        
        # AA = 6 combos, AKs = 4 combos, AKo = 12 combos = 22 total
        # 22/1326 * 100 ≈ 1.66%
        expected_freq = (6 + 4 + 12) / 1326 * 100
        self.assertAlmostEqual(freq, expected_freq, places=2)
    
    def test_hand_manipulation(self):
        """Test adding/removing hands from ranges."""
        range_name = self.range_tool.create_range('manipulation_test', template='tight')
        initial_freq = self.range_tool.ranges[range_name]['frequency']
        
        # Add hand
        result = self.range_tool.add_hand_to_range(range_name, '99')
        self.assertTrue(result)
        
        new_freq = self.range_tool.ranges[range_name]['frequency']
        self.assertGreater(new_freq, initial_freq)
        
        # Remove hand
        result = self.range_tool.remove_hand_from_range(range_name, '99')
        self.assertTrue(result)
        
        final_freq = self.range_tool.ranges[range_name]['frequency']
        self.assertAlmostEqual(final_freq, initial_freq, places=2)
        
        # Test invalid range
        result = self.range_tool.add_hand_to_range('nonexistent', 'AA')
        self.assertFalse(result)
    
    def test_range_comparison(self):
        """Test range comparison functionality."""
        self.range_tool.create_range('range1', template='tight')
        self.range_tool.create_range('range2', template='loose')
        
        comparison = self.range_tool.compare_ranges('range1', 'range2')
        
        self.assertIsNotNone(comparison)
        self.assertIn('overlap', comparison)
        self.assertIn('overlap_percentage', comparison)
        self.assertIn('only_in_range1', comparison)
        self.assertIn('only_in_range2', comparison)
        self.assertIn('range1_frequency', comparison)
        self.assertIn('range2_frequency', comparison)
        
        # Overlap should exist (tight is subset of loose)
        self.assertGreater(len(comparison['overlap']), 0)
        self.assertGreater(comparison['overlap_percentage'], 0)
        
        # Test invalid ranges
        invalid_comparison = self.range_tool.compare_ranges('nonexistent1', 'nonexistent2')
        self.assertIsNone(invalid_comparison)
    
    def test_range_export(self):
        """Test range export functionality."""
        self.range_tool.create_range('export_test', hands=['AA', 'KK', 'AKs', 'AKo'])
        
        # Test different export formats
        pokerstove_export = self.range_tool.export_range('export_test', 'pokerstove')
        self.assertIn('AA', pokerstove_export)
        self.assertIn('KK', pokerstove_export)
        self.assertIn(',', pokerstove_export)
        
        json_export = self.range_tool.export_range('export_test', 'json')
        self.assertIsInstance(json_export, str)
        parsed_json = json.loads(json_export)
        self.assertIn('pairs', parsed_json)
        
        list_export = self.range_tool.export_range('export_test', 'list')
        self.assertIsInstance(list_export, list)
        self.assertIn('AA', list_export)
        
        # Test invalid range
        invalid_export = self.range_tool.export_range('nonexistent', 'pokerstove')
        self.assertIsNone(invalid_export)


class TestStatsDashboard(unittest.TestCase):
    """Test statistics dashboard functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.dashboard = StatsDashboard()
        
        # Add sample sessions
        base_time = time.time() - (29 * 24 * 3600)  # 29 days ago
        for i in range(10):
            self.dashboard.add_session({
                'timestamp': base_time + (i * 24 * 3600),  # One session per day
                'duration': 7200 + (i * 600),  # 2-3 hours
                'hands_played': 200 + (i * 20),
                'profit_loss': (-50 + i * 25),  # Progression from -50 to +175
                'game_type': 'NLHE',
                'stakes': '0.05/0.10',
                'vpip': 0.2 + (i * 0.01),
                'pfr': 0.15 + (i * 0.005),
                'aggression_factor': 2.0 + (i * 0.1)
            })
    
    def test_session_management(self):
        """Test session addition and management."""
        initial_count = len(self.dashboard.sessions)
        
        session_id = self.dashboard.add_session({
            'duration': 3600,
            'hands_played': 150,
            'profit_loss': 100,
            'game_type': 'PLO',
            'stakes': '0.10/0.25'
        })
        
        self.assertIsInstance(session_id, int)
        self.assertEqual(len(self.dashboard.sessions), initial_count + 1)
        
        # Check session data
        session = self.dashboard.sessions[-1]
        self.assertEqual(session['id'], session_id)
        self.assertEqual(session['game_type'], 'PLO')
        self.assertEqual(session['profit_loss'], 100)
    
    def test_dashboard_data_generation(self):
        """Test dashboard data generation."""
        dashboard_data = self.dashboard.get_dashboard_data(days=30)
        
        # Check required fields
        required_fields = [
            'period_days', 'sessions_played', 'total_hands', 'total_time_hours',
            'total_profit', 'profit_per_hour', 'bb_per_100_hands', 'session_win_rate',
            'avg_vpip', 'avg_pfr', 'avg_aggression_factor', 'profit_variance',
            'best_session', 'worst_session', 'graph_data'
        ]
        
        for field in required_fields:
            self.assertIn(field, dashboard_data)
        
        # Check calculations
        self.assertEqual(dashboard_data['period_days'], 30)
        self.assertEqual(dashboard_data['sessions_played'], 10)
        self.assertGreater(dashboard_data['total_hands'], 0)
        self.assertGreater(dashboard_data['total_time_hours'], 0)
        
        # Check graph data structure
        graph_data = dashboard_data['graph_data']
        self.assertIn('x', graph_data)
        self.assertIn('y', graph_data)
        self.assertEqual(len(graph_data['x']), len(graph_data['y']))
    
    def test_empty_dashboard(self):
        """Test dashboard with no data."""
        empty_dashboard = StatsDashboard()
        
        dashboard_data = empty_dashboard.get_dashboard_data(days=30)
        
        self.assertEqual(dashboard_data['sessions_played'], 0)
        self.assertEqual(dashboard_data['total_hands'], 0)
        self.assertEqual(dashboard_data['total_profit'], 0)
    
    def test_custom_report_creation(self):
        """Test custom report functionality."""
        filters = {
            'game_type': 'NLHE',
            'min_profit': 0,
            'stakes': '0.05/0.10'
        }
        
        metrics = ['total_profit', 'session_count', 'win_rate']
        
        report_name = self.dashboard.create_custom_report('winning_nlhe', filters, metrics)
        self.assertEqual(report_name, 'winning_nlhe')
        self.assertIn('winning_nlhe', self.dashboard.custom_reports)
    
    def test_custom_report_generation(self):
        """Test custom report generation."""
        # Create report
        filters = {'game_type': 'NLHE', 'min_profit': 0}
        metrics = ['total_profit', 'session_count', 'win_rate', 'avg_profit_per_session']
        
        self.dashboard.create_custom_report('test_report', filters, metrics)
        
        # Generate report
        report_data = self.dashboard.generate_custom_report('test_report')
        
        self.assertIsNotNone(report_data)
        self.assertEqual(report_data['report_name'], 'test_report')
        self.assertIn('results', report_data)
        self.assertIn('session_count', report_data)
        
        results = report_data['results']
        for metric in metrics:
            self.assertIn(metric, results)
        
        # Test non-existent report
        invalid_report = self.dashboard.generate_custom_report('nonexistent')
        self.assertIsNone(invalid_report)
    
    def test_bb_per_100_calculation(self):
        """Test big blinds per 100 hands calculation."""
        # This is tested indirectly through dashboard data
        dashboard_data = self.dashboard.get_dashboard_data(days=30)
        
        bb_per_100 = dashboard_data['bb_per_100_hands']
