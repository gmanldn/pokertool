#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper functions for enhanced_gui.py - Screen scraper integration.

This module contains scraper-related methods extracted from enhanced_gui.py
to keep the main file under 25,000 tokens.
"""

import time
from typing import Optional, Dict, Any

# Import the global enhanced scraper manager to access cached state
try:
    from pokertool.scrape import _scraper_manager
    ENHANCED_SCRAPER_AVAILABLE = True
except (ImportError, AttributeError) as e:
    ENHANCED_SCRAPER_AVAILABLE = False
    _scraper_manager = None
    print(f"[enhanced_gui_helpers] Warning: Enhanced scraper manager not available: {e}")

# Cache for last known table state - ensures continuous display even during detection failures
_last_table_data: Optional[Dict[str, Any]] = None
_last_update_time: float = 0.0
_cache_timeout: float = 30.0  # Keep cached data for up to 30 seconds


def get_live_table_data_from_scraper(screen_scraper) -> Optional[Dict[str, Any]]:
    """
    Get live table data from the screen scraper for LiveTable display.

    Args:
        screen_scraper: The screen scraper instance

    Returns a dictionary containing:
    - status: Table status string
    - confidence: Detection confidence (0-100)
    - board_cards: List of community cards
    - small_blind, big_blind, ante: Blind levels
    - pot: Current pot size
    - dealer_seat: Dealer button seat number
    - players: Dict of player data by seat number
    - my_hole_cards: Current player's hole cards
    - recommended_action: AI-recommended action
    """
    global _last_table_data, _last_update_time

    print(f"[get_live_table_data] FUNCTION CALLED, scraper={screen_scraper is not None}")

    try:
        # Always try to get data if scraper exists - don't wait for autopilot
        if not screen_scraper:
            print("[get_live_table_data] No screen scraper available")
            # Return cached data if available and not too stale
            if _last_table_data and (time.time() - _last_update_time) < _cache_timeout:
                _last_table_data['data_source'] = 'cached (no scraper)'
                _last_table_data['data_age_seconds'] = time.time() - _last_update_time
                return _last_table_data
            return None

        # Try to get cached state from the enhanced scraper manager first
        # This is much faster than calling analyze_table()
        table_state = None
        print(f"[get_live_table_data] ENHANCED_SCRAPER_AVAILABLE={ENHANCED_SCRAPER_AVAILABLE}, _scraper_manager={_scraper_manager is not None}")
        if ENHANCED_SCRAPER_AVAILABLE and _scraper_manager:
            cached_state = _scraper_manager.get_latest_state()
            print(f"[get_live_table_data] cached_state type: {type(cached_state)}, is_none: {cached_state is None}")
            if cached_state:
                print(f"[get_live_table_data] Got cached state from enhanced scraper manager")
                # The enhanced scraper returns a game_state dict, not a TableState object
                # We need to convert it to the expected format
                # For now, let's just try to use it directly and see what happens
                return _convert_game_state_to_table_data(cached_state)
            else:
                print(f"[get_live_table_data] No cached state available from enhanced scraper")

        # Fall back to calling analyze_table() if no cached state
        if hasattr(screen_scraper, 'analyze_table'):
            print(f"[get_live_table_data] Falling back to analyze_table() (slow)")
            table_state = screen_scraper.analyze_table()
        else:
            print("[get_live_table_data] Screen scraper has no analyze_table method")
            # Return cached data if available
            if _last_table_data and (time.time() - _last_update_time) < _cache_timeout:
                _last_table_data['data_source'] = 'cached (scraper error)'
                _last_table_data['data_age_seconds'] = time.time() - _last_update_time
                return _last_table_data
            return None

        if not table_state:
            print("[get_live_table_data] analyze_table returned None")
            # Return cached data if available
            if _last_table_data and (time.time() - _last_update_time) < _cache_timeout:
                _last_table_data['data_source'] = 'cached (no table state)'
                _last_table_data['data_age_seconds'] = time.time() - _last_update_time
                return _last_table_data
            return None

        # Debug: Log what we got
        seats_count = len(table_state.seats) if hasattr(table_state, 'seats') else 0
        detection_conf = getattr(table_state, 'detection_confidence', 0.0)
        print(f"[get_live_table_data] Got table_state: {seats_count} seats, {detection_conf:.1%} confidence")

        # LOWERED THRESHOLD: Accept even very low confidence detections
        # This ensures continuous display even with intermittent detection
        if detection_conf < 0.001:  # Changed from 0.01 to 0.001
            print(f"[get_live_table_data] Very low confidence ({detection_conf:.1%}), returning cached data if available")
            # Return cached data if available
            if _last_table_data and (time.time() - _last_update_time) < _cache_timeout:
                _last_table_data['data_source'] = 'cached (low confidence)'
                _last_table_data['data_age_seconds'] = time.time() - _last_update_time
                return _last_table_data
            return None

        # Build comprehensive data structure with ALL table information
        data = {
            'status': 'Active',
            'confidence': getattr(table_state, 'detection_confidence', 0.0) * 100,  # Convert to percentage
            'board_cards': [],
            'small_blind': getattr(table_state, 'small_blind', 0.05),
            'big_blind': getattr(table_state, 'big_blind', 0.10),
            'ante': getattr(table_state, 'ante', 0),
            'pot': getattr(table_state, 'pot_size', 0),
            'dealer_seat': getattr(table_state, 'dealer_seat', 0),
            'stage': getattr(table_state, 'stage', 'unknown'),
            'active_players': getattr(table_state, 'active_players', 0),
            'active_turn_seat': getattr(table_state, 'active_turn_seat', 0),  # NEW
            'tournament_name': getattr(table_state, 'tournament_name', None),  # NEW
            'extraction_method': getattr(table_state, 'extraction_method', 'screenshot_ocr'),  # NEW
            'extraction_time_ms': getattr(table_state, 'extraction_time_ms', 0.0),  # NEW
            'players': {},
            'my_hole_cards': [],
            'recommended_action': 'Waiting for game state...',
            'validation_complete': True,
            'warnings': []
        }

        print(f"[get_live_table_data] Data created: pot=${data['pot']}, stage={data['stage']}, players={data['active_players']}")

        # Extract board cards with validation
        if hasattr(table_state, 'board_cards') and table_state.board_cards:
            data['board_cards'] = [str(card) for card in table_state.board_cards]
        else:
            data['warnings'].append("No board cards detected")

        # Extract player information with comprehensive validation
        # Check both 'players' and 'seats' attributes (different scrapers use different names)
        players_list = []
        if hasattr(table_state, 'players') and table_state.players:
            players_list = table_state.players
            print(f"[get_live_table_data] Found players_list from table_state.players: {len(players_list)} players")
        elif hasattr(table_state, 'seats') and table_state.seats:
            players_list = table_state.seats
            print(f"[get_live_table_data] Found players_list from table_state.seats: {len(players_list)} players")
        else:
            print(f"[get_live_table_data] No players_list found. table_state attrs: {dir(table_state)}")

        if players_list:
            players_detected = 0
            players_with_names = 0
            players_with_stacks = 0
            active_players = 0

            # Process ALL seats, not just active ones - show partial data
            for i, player in enumerate(players_list):
                if not player:
                    print(f"[get_live_table_data] Player {i} is None, skipping")
                    continue

                seat_num = getattr(player, 'seat_number', len(data['players']) + 1)

                # Handle both attribute naming conventions (name/player_name, stack/stack_size)
                player_name = getattr(player, 'player_name', None) or getattr(player, 'name', None)
                player_stack = getattr(player, 'stack_size', 0) or getattr(player, 'stack', 0)
                is_active = getattr(player, 'is_active', False)

                print(f"[get_live_table_data] Processing player {i}: seat={seat_num}, name='{player_name}', stack=${player_stack}, active={is_active}")

                # Count this player
                players_detected += 1
                if is_active:
                    active_players += 1

                # Track data quality
                if player_name and player_name.strip():
                    players_with_names += 1
                if player_stack > 0:
                    players_with_stacks += 1

                # Always create player data, even if inactive or incomplete
                player_data = {
                    'name': player_name if (player_name and player_name.strip()) else 'Empty',
                    'stack': player_stack if player_stack > 0 else 0,
                    'bet': getattr(player, 'current_bet', 0) or getattr(player, 'bet', 0) or 0,
                    'hole_cards': [],
                    'status': getattr(player, 'status_text', 'Active' if is_active else 'Empty'),
                    'position': getattr(player, 'position', None) or '',
                    'is_dealer': getattr(player, 'is_dealer', False) or (seat_num == data['dealer_seat']),
                    'is_small_blind': getattr(player, 'is_small_blind', False),
                    'is_big_blind': getattr(player, 'is_big_blind', False),
                    # NEW: Enhanced stats from CDP or OCR
                    'vpip': getattr(player, 'vpip', None),
                    'af': getattr(player, 'af', None),
                    'time_bank': getattr(player, 'time_bank', None),
                    'is_active_turn': getattr(player, 'is_active_turn', False) or (seat_num == data['active_turn_seat']),
                }

                # Extract hole cards if visible (showdown)
                if hasattr(player, 'hole_cards') and player.hole_cards:
                    player_data['hole_cards'] = [str(card) for card in player.hole_cards]

                data['players'][seat_num] = player_data

            # Add validation warnings (informational only - don't block data display)
            if players_detected == 0:
                data['warnings'].append("No players detected at table")
                data['validation_complete'] = False
            else:
                # Show partial data even if incomplete
                if players_with_names < active_players and active_players > 0:
                    data['warnings'].append(f"OCR: {players_with_names}/{active_players} active player names detected")
                if players_with_stacks < active_players and active_players > 0:
                    data['warnings'].append(f"OCR: {players_with_stacks}/{active_players} active player stacks detected")

                # Only mark as incomplete if we have very little data
                if players_with_names == 0 and players_with_stacks == 0:
                    data['validation_complete'] = False
                else:
                    # We have at least some data - mark as complete so it displays
                    data['validation_complete'] = True
        else:
            data['warnings'].append("No player data available")
            data['validation_complete'] = False

        # Extract hero's hole cards with validation (don't warn if not in hand)
        if hasattr(table_state, 'hero_cards') and table_state.hero_cards:
            data['my_hole_cards'] = [str(card) for card in table_state.hero_cards]
        # Don't add warning - hero might not be in hand

        # Validate dealer button (informational only)
        if data['dealer_seat'] == 0 or data['dealer_seat'] is None:
            data['warnings'].append("Dealer button position not detected")

        # TODO: Implement GTO-based recommendation system
        # For now, recommended_action remains "Waiting for game state..."

        # Add metadata about data freshness
        data['data_source'] = 'live'
        data['data_age_seconds'] = 0.0
        data['last_update_timestamp'] = time.time()

        # Cache this data for future use
        _last_table_data = data.copy()
        _last_update_time = time.time()

        # Debug: Log what we're returning
        player_count = len(data.get('players', {}))
        validation_status = "COMPLETE" if data.get('validation_complete', False) else "INCOMPLETE"
        print(f"[get_live_table_data] Returning LIVE data: {player_count} players, {validation_status}, {len(data.get('warnings', []))} warnings")

        # Log detailed player data
        if data.get('players'):
            print(f"[get_live_table_data] Player data being returned:")
            for seat, player_info in data['players'].items():
                print(f"  Seat {seat}: {player_info['name']} - ${player_info['stack']} - {player_info['status']}")
        else:
            print(f"[get_live_table_data] WARNING: No player data in return dict!")

        return data

    except Exception as e:
        print(f"[get_live_table_data] ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Even on error, try to return cached data
        if _last_table_data and (time.time() - _last_update_time) < _cache_timeout:
            _last_table_data['data_source'] = 'cached (exception)'
            _last_table_data['data_age_seconds'] = time.time() - _last_update_time
            print(f"[get_live_table_data] Returning cached data after exception (age: {_last_table_data['data_age_seconds']:.1f}s)")
            return _last_table_data

        return None


def _convert_game_state_to_table_data(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert enhanced scraper's game_state format to LiveTable's expected format.

    game_state has keys like: 'hole_cards', 'board', 'pot', 'position', 'num_players', etc.
    We need to convert this to the format with 'players', 'board_cards', etc.
    """
    print(f"[_convert_game_state] Converting game_state with keys: {list(game_state.keys())[:10]}")

    data = {
        'status': 'Active',
        'confidence': game_state.get('detection_confidence', 0.8) * 100,  # Convert to percentage
        'board_cards': game_state.get('board', []),
        'small_blind': game_state.get('small_blind', 0.05),
        'big_blind': game_state.get('big_blind', 0.10),
        'ante': game_state.get('ante', 0),
        'pot': game_state.get('pot', 0),
        'dealer_seat': game_state.get('dealer_seat', 0),
        'stage': game_state.get('stage', 'unknown'),
        'active_players': game_state.get('num_players', 0),
        'players': {},
        'my_hole_cards': game_state.get('hole_cards', []),
        'recommended_action': 'Waiting for game state...',
        'validation_complete': True,
        'warnings': [],
        'data_source': 'live_cached',
        'data_age_seconds': 0.0,
        'last_update_timestamp': time.time()
    }

    # TODO: Extract player data from game_state if available
    # For now, return minimal data
    print(f"[_convert_game_state] Converted to table_data with {len(data['players'])} players")

    return data
