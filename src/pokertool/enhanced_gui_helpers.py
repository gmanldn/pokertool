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

        # Try to get cached state from the scraper directly first (much faster!)
        # Priority 1: Check if scraper has get_cached_state method (from continuous capture)
        cached_state = None
        if hasattr(screen_scraper, 'get_cached_state'):
            cached_state = screen_scraper.get_cached_state()
            print(f"[get_live_table_data] Got cached state from scraper: {cached_state is not None}")
            if cached_state:
                return _convert_game_state_to_table_data(cached_state)

        # Priority 2: Try enhanced scraper manager
        table_state = None
        print(f"[get_live_table_data] ENHANCED_SCRAPER_AVAILABLE={ENHANCED_SCRAPER_AVAILABLE}, _scraper_manager={_scraper_manager is not None}")
        if ENHANCED_SCRAPER_AVAILABLE and _scraper_manager:
            cached_state = _scraper_manager.get_latest_state()
            print(f"[get_live_table_data] cached_state type: {type(cached_state)}, is_none: {cached_state is None}")
            if cached_state:
                print(f"[get_live_table_data] Got cached state from enhanced scraper manager")
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

                # Filter out invalid/placeholder names when no real table is detected
                # Common OCR errors or placeholder names: "you", "player", single letters, etc.
                if player_name:
                    name_lower = player_name.strip().lower()
                    invalid_names = {'you', 'player', 'empty', 'seat', '-', '?', 'n/a'}
                    # Also reject single character names (likely OCR errors)
                    if name_lower in invalid_names or (len(name_lower) == 1 and not name_lower.isdigit()):
                        player_name = None  # Treat as empty

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

        # Generate advice data if we have sufficient table information
        advice_data = _generate_advice_data(table_state, data)
        if advice_data:
            data['advice_data'] = advice_data
            # Update recommended_action text for backward compatibility
            if advice_data.has_data:
                action_text = advice_data.action.value
                if advice_data.action_amount:
                    action_text += f" ${advice_data.action_amount:.0f}"
                data['recommended_action'] = action_text

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


def _generate_advice_data(table_state, table_data: Dict[str, Any]):
    """
    Generate LiveAdviceData from table state for detailed explanations.

    Args:
        table_state: Raw table state from scraper
        table_data: Processed table data dictionary

    Returns:
        LiveAdviceData object or None if insufficient data
    """
    try:
        # Import here to avoid circular dependencies
        from pokertool.live_decision_engine import LiveDecisionEngine, GameState
        from pokertool.compact_live_advice_window import LiveAdviceData, ActionType

        # Check if we have enough data for advice generation
        hero_cards = table_data.get('my_hole_cards', [])
        if not hero_cards or len(hero_cards) < 2:
            # No hero cards, can't generate advice
            return None

        # Check if it's hero's turn (optional - generate advice anyway for educational purposes)
        # active_turn_seat = table_data.get('active_turn_seat', 0)
        # my_seat = ... (we'd need to track this)

        # Build GameState from table_data
        game_state = GameState(
            hole_cards=hero_cards,
            community_cards=table_data.get('board_cards', []),
            pot_size=float(table_data.get('pot', 0)),
            call_amount=0.0,  # TODO: Extract from active player or betting action
            min_raise=float(table_data.get('big_blind', 0.10)) * 2,
            max_raise=1000.0,  # TODO: Extract from hero's stack
            stack_size=100.0,  # TODO: Extract hero's actual stack
            position=table_data.get('position', 'unknown'),
            num_opponents=max(1, table_data.get('active_players', 1) - 1),
            street=table_data.get('stage', 'preflop'),
            is_tournament=bool(table_data.get('tournament_name')),
            blinds=(
                float(table_data.get('small_blind', 0.05)),
                float(table_data.get('big_blind', 0.10))
            )
        )

        # Try to extract hero's stack and call amount from players data
        players = table_data.get('players', {})
        for seat, player in players.items():
            # TODO: Identify hero's seat (need handle matching or other logic)
            # For now, use first player with cards as placeholder
            if player.get('hole_cards') and len(player.get('hole_cards', [])) >= 2:
                game_state.stack_size = float(player.get('stack', 100.0))
                break

        # Create a simple decision engine (singleton pattern would be better for performance)
        # For now, create a new one each time
        if not hasattr(_generate_advice_data, '_engine_cache'):
            _generate_advice_data._engine_cache = LiveDecisionEngine(
                bankroll=10000.0,
                win_calc_iterations=5000  # Reduced for speed
            )

        engine = _generate_advice_data._engine_cache

        # Generate advice
        advice = engine.get_live_advice(game_state)

        return advice

    except Exception as e:
        print(f"[_generate_advice_data] Error generating advice: {e}")
        import traceback
        traceback.print_exc()
        return None


def _convert_game_state_to_table_data(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert enhanced scraper's game_state format to LiveTable's expected format.

    game_state has keys like: 'hole_cards', 'board', 'pot', 'position', 'num_players', etc.
    We need to convert this to the format with 'players', 'board_cards', etc.
    """
    print(f"[_convert_game_state] Converting game_state with keys: {list(game_state.keys())[:10]}")

    # Extract board cards - handle both 'board' and 'board_cards' keys
    board_cards = game_state.get('board_cards', game_state.get('board', []))

    data = {
        'status': 'Active',
        'confidence': game_state.get('detection_confidence', 0.8) * 100,  # Convert to percentage
        'board_cards': board_cards,
        'small_blind': game_state.get('small_blind', 0.05),
        'big_blind': game_state.get('big_blind', 0.10),
        'ante': game_state.get('ante', 0),
        'pot': game_state.get('pot_size', game_state.get('pot', 0)),
        'dealer_seat': game_state.get('dealer_seat', 0),
        'stage': game_state.get('stage', 'unknown'),
        'active_players': game_state.get('active_players', game_state.get('num_players', 0)),
        'players': {},
        'my_hole_cards': game_state.get('hero_cards', game_state.get('hole_cards', [])),
        'recommended_action': 'Waiting for game state...',
        'validation_complete': True,
        'warnings': [],
        'data_source': 'live_cached',
        'data_age_seconds': 0.0,
        'last_update_timestamp': time.time(),
        'extraction_method': game_state.get('extraction_method', 'unknown'),
        'extraction_time_ms': game_state.get('extraction_time_ms', 0.0),
        'tournament_name': game_state.get('tournament_name'),
        'table_name': game_state.get('table_name'),
    }

    # PHASE 1: Extract ALL player data from seats list (Tasks 1-8)
    seats = game_state.get('seats', [])
    if seats:
        print(f"[_convert_game_state] Processing {len(seats)} seats from game_state")

        for seat_info in seats:
            # Handle both dataclass and dict formats
            if hasattr(seat_info, 'seat_number'):
                # Dataclass format
                seat_num = seat_info.seat_number
                is_active = seat_info.is_active
                player_name = seat_info.player_name
                stack = seat_info.stack_size
                is_hero = seat_info.is_hero
                is_dealer = seat_info.is_dealer
                is_sb = seat_info.is_small_blind
                is_bb = seat_info.is_big_blind
                position = seat_info.position
                vpip = seat_info.vpip
                af = seat_info.af
                time_bank = seat_info.time_bank
                is_active_turn = seat_info.is_active_turn
                current_bet = seat_info.current_bet
                status_text = seat_info.status_text
            else:
                # Dict format
                seat_num = seat_info.get('seat_number', 0)
                is_active = seat_info.get('is_active', False)
                player_name = seat_info.get('player_name', '')
                stack = seat_info.get('stack_size', 0.0)
                is_hero = seat_info.get('is_hero', False)
                is_dealer = seat_info.get('is_dealer', False)
                is_sb = seat_info.get('is_small_blind', False)
                is_bb = seat_info.get('is_big_blind', False)
                position = seat_info.get('position', '')
                vpip = seat_info.get('vpip')
                af = seat_info.get('af')
                time_bank = seat_info.get('time_bank')
                is_active_turn = seat_info.get('is_active_turn', False)
                current_bet = seat_info.get('current_bet', 0.0)
                status_text = seat_info.get('status_text', '')

            # Skip empty seats (no name or name is empty string)
            if not player_name or player_name.strip() == '':
                continue

            # Build position indicator string
            position_indicators = []
            if is_dealer:
                position_indicators.append('BTN')
            if is_sb:
                position_indicators.append('SB')
            if is_bb:
                position_indicators.append('BB')
            if position and position not in position_indicators:
                position_indicators.append(position)

            position_str = '/'.join(position_indicators) if position_indicators else ''

            # Determine player status
            if not status_text:
                if is_active:
                    status_text = 'Active'
                else:
                    status_text = 'Sitting Out'

            # Build player dict
            player_dict = {
                'name': player_name,
                'stack': stack,
                'active': is_active,
                'status': status_text,
                'position': position_str,
                'is_dealer': is_dealer,
                'is_small_blind': is_sb,
                'is_big_blind': is_bb,
                'is_hero': is_hero,
                'is_active_turn': is_active_turn,
                'bet': current_bet,
                'vpip': vpip,
                'af': af,
                'time_bank': time_bank,
                'hole_cards': ['', ''],  # Hole cards only shown for hero
            }

            # Add hero's hole cards if this is the hero
            if is_hero:
                hero_cards = game_state.get('hero_cards', game_state.get('hole_cards', []))
                if hero_cards and len(hero_cards) >= 2:
                    player_dict['hole_cards'] = hero_cards[:2]
                    # Also update the top-level my_hole_cards
                    data['my_hole_cards'] = hero_cards[:2]

            data['players'][seat_num] = player_dict

        print(f"[_convert_game_state] Converted to table_data with {len(data['players'])} players")

        # Update active_players count based on actual active players
        active_count = sum(1 for p in data['players'].values() if p.get('active', False))
        if active_count > 0:
            data['active_players'] = active_count
    else:
        print(f"[_convert_game_state] No seats data found in game_state")
        print(f"[_convert_game_state] Available keys: {list(game_state.keys())}")

    return data
