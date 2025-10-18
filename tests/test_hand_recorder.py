from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import List
from unittest.mock import patch

import pytest

from pokertool.hand_recorder import HandRecorder, HandRecorderState


@dataclass
class SeatStub:
    seat_number: int
    player_name: str
    stack_size: float
    is_hero: bool = False
    position: str = ""
    cards: List[str] = field(default_factory=list)
    is_active: bool = True
    current_bet: float = 0.0
    status_text: str = ""


class DummyHandHistoryDB:
    def __init__(self):
        self.saved_hand = None

    def save_hand(self, hand):
        self.saved_hand = hand
        return True


def build_state(
    *,
    pot_size: float,
    stage: str,
    hero_stack: float,
    villain_stack: float,
    hero_cards: List[str],
    board_cards: List[str],
) -> SimpleNamespace:
    """Utility helper to create a simplified TableState stub."""
    hero_seat = SeatStub(
        seat_number=1,
        player_name="Hero",
        stack_size=hero_stack,
        is_hero=True,
        cards=list(hero_cards),
        position="BTN",
    )
    villain_seat = SeatStub(
        seat_number=2,
        player_name="Villain",
        stack_size=villain_stack,
        is_hero=False,
        cards=[],
        position="BB",
    )

    return SimpleNamespace(
        pot_size=pot_size,
        stage=stage,
        hero_cards=list(hero_cards),
        board_cards=list(board_cards),
        seats=[hero_seat, villain_seat],
        active_players=2,
        site_detected="BETFAIR",
        hero_seat=1,
    )


def test_hand_recorder_tracks_actions_and_outcomes():
    recorder = HandRecorder()
    db = DummyHandHistoryDB()

    states = [
        build_state(
            pot_size=0.2,
            stage="preflop",
            hero_stack=100.0,
            villain_stack=100.0,
            hero_cards=["As", "Kd"],
            board_cards=[],
        ),
        build_state(
            pot_size=1.2,  # Villain raises 1.0
            stage="preflop",
            hero_stack=100.0,
            villain_stack=99.0,
            hero_cards=["As", "Kd"],
            board_cards=[],
        ),
        build_state(
            pot_size=2.2,  # Hero calls 1.0
            stage="flop",
            hero_stack=99.0,
            villain_stack=99.0,
            hero_cards=["As", "Kd"],
            board_cards=["Ts", "7d", "2c"],
        ),
        build_state(
            pot_size=0.0,  # Pot awarded to hero
            stage="showdown",
            hero_stack=101.8,
            villain_stack=98.2,
            hero_cards=[],
            board_cards=["Ts", "7d", "2c", "9h", "3s"],
        ),
    ]

    with patch("pokertool.hand_history_db.get_hand_history_db", return_value=db):
        for state in states:
            recorder.update(state)

    assert recorder.state == HandRecorderState.COMPLETED
    assert db.saved_hand is not None, "Hand history should be persisted"

    saved_hand = db.saved_hand
    assert saved_hand.hero_result == "won"
    assert pytest.approx(saved_hand.hero_net, rel=1e-3) == 1.8
    assert "Hero" in saved_hand.winners

    # Ensure betting actions are captured (villain raise + hero call)
    action_players = {action.player_name for action in saved_hand.actions}
    assert {"Villain", "Hero"}.issubset(action_players)

