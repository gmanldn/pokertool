#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Utilities for broadcasting live table state to web clients."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Sequence


logger = logging.getLogger(__name__)

__all__ = ['broadcast_table_update']


def _normalize_cards(cards: Any) -> List[str]:
    if not cards:
        return []
    if isinstance(cards, str):
        return [cards]
    if isinstance(cards, (list, tuple, set)):
        return [str(card) for card in cards if card]
    return []


def _normalize_players(players: Any) -> List[Dict[str, Any]]:
    resolved: Iterable[Any]
    if isinstance(players, Mapping):
        resolved = players.values()
    elif isinstance(players, Sequence):
        resolved = players
    else:
        return []

    normalised: List[Dict[str, Any]] = []
    for index, entry in enumerate(resolved, start=1):
        if not isinstance(entry, Mapping):
            continue
        seat_raw = entry.get('seat') or entry.get('seat_number') or entry.get('id') or index
        try:
            seat = int(seat_raw)
        except (TypeError, ValueError):
            seat = index

        stack_raw = entry.get('stack')
        chips_raw = entry.get('chips')
        try:
            stack = float(stack_raw if stack_raw is not None else chips_raw or 0)
        except (TypeError, ValueError):
            stack = 0.0

        normalised.append({
            'seat': seat,
            'name': str(entry.get('name') or entry.get('player') or f'Player {seat}'),
            'chips': stack,
            'cards': _normalize_cards(entry.get('cards') or entry.get('hole_cards')),
            'isActive': bool(entry.get('is_active', entry.get('active', True))),
            'isFolded': bool(entry.get('is_folded', entry.get('folded', False))),
            'position': entry.get('position') or entry.get('pos'),
            'isHero': bool(entry.get('is_hero') or entry.get('hero')),
            'notes': entry.get('notes') if isinstance(entry.get('notes'), list) else [],
        })
    return normalised


def _normalise_state(table_id: str, raw_state: Mapping[str, Any]) -> Dict[str, Any]:
    table_name = (
        raw_state.get('table_name')
        or raw_state.get('window_title')
        or raw_state.get('table')
        or table_id
    )

    pot_value = raw_state.get('pot_size', raw_state.get('pot'))
    try:
        pot = float(pot_value or 0)
    except (TypeError, ValueError):
        pot = 0.0

    community_cards = (
        _normalize_cards(raw_state.get('board_cards_ocr'))
        or _normalize_cards(raw_state.get('board_cards'))
        or _normalize_cards(raw_state.get('community_cards'))
    )

    dealer_seat = raw_state.get('dealer_seat')
    if isinstance(dealer_seat, str) and dealer_seat.isdigit():
        dealer_seat = int(dealer_seat)
    elif not isinstance(dealer_seat, int):
        dealer_seat = None

    current_action = (
        raw_state.get('current_action')
        or raw_state.get('action')
        or ('Action required' if raw_state.get('action_required') else 'Idle')
    )

    is_active = bool(
        raw_state.get('table_active', True)
        and not raw_state.get('closed')
    )

    big_blind = raw_state.get('big_blind')
    try:
        big_blind_val = float(big_blind) if big_blind is not None else None
    except (TypeError, ValueError):
        big_blind_val = None

    metadata = {
        'site': raw_state.get('site') or raw_state.get('platform'),
        'stage': raw_state.get('stage'),
        'dealerSeat': dealer_seat,
        'heroSeat': raw_state.get('hero_seat'),
        'lastUpdateTs': raw_state.get('timestamp') or datetime.utcnow().isoformat(),
        'recognition': raw_state.get('recognition_method'),
    }

    if big_blind_val is not None:
        metadata['bigBlind'] = big_blind_val

    return {
        'tableId': table_id,
        'tableName': str(table_name),
        'players': _normalize_players(raw_state.get('players')),
        'pot': pot,
        'communityCards': community_cards,
        'currentAction': str(current_action),
        'isActive': is_active,
        'metadata': metadata,
    }


def _schedule_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
    else:
        loop.create_task(coro)


def broadcast_table_update(table_id: str, state: Dict[str, Any]) -> None:
    """
    Broadcast ``state`` to connected WebSocket clients.

    Falls back gracefully when the API stack is not available.
    """
    if not state:
        return

    try:
        from pokertool.api import FASTAPI_AVAILABLE, get_api  # noqa: WPS433
    except ImportError:
        logger.debug('API stack not available; skipping table update broadcast')
        return

    if not FASTAPI_AVAILABLE:
        logger.debug('FastAPI dependencies not installed; cannot broadcast table updates')
        return

    try:
        api = get_api()
    except Exception as exc:  # pragma: no cover - API initialisation issues
        logger.debug('Failed to obtain API instance: %s', exc)
        return

    message = {
        'type': 'table_update',
        'timestamp': datetime.utcnow().isoformat(),
        'data': _normalise_state(table_id, state),
    }

    async def _send():
        try:
            await api.services.connection_manager.broadcast(message)
        except Exception as exc:  # pragma: no cover - network runtime
            logger.debug('Table update broadcast failed: %s', exc)

    _schedule_async(_send())
