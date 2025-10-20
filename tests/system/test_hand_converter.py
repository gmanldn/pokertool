"""Tests for universal hand history converter."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.hand_converter import HandConverter, HandFormatDetector, PokerSite


POKERSTARS_HAND = """PokerStars Hand #1234567890:  Hold'em No Limit ($0.10/$0.25 USD) - 2025/09/30 21:15:42 ET
Table 'Alpha' 6-max Seat #3 is the button
Seat 1: Hero ($25 in chips)
Seat 2: Villain1 ($25 in chips)
Seat 3: Villain2 ($25 in chips)
*** HOLE CARDS ***
Dealt to Hero [Ah Kh]
Hero: raises $0.75 to $1
Villain1: calls $1
*** FLOP *** [As 7c 2d]
Hero: bets $1.25
Villain1: calls $1.25
*** TURN *** [As 7c 2d] [Qc]
Hero: bets $3.50
Villain1: folds
Uncalled bet ($3.50) returned to Hero
"""

PARTYPOKER_HAND = """Game started at 2025/09/30 21:18:11
$0.10/$0.25 No Limit Holdem - PartyPoker
Seat 1: Hero ($25)
Seat 2: Caller ($25)
***HOLE CARDS***
Hero raises to $0.75
Caller calls $0.75
***FLOP*** [Jh 9h 2s]
Hero bets $1.20
Caller calls $1.20
***TURN*** [Jh 9h 2s] [4d]
Hero bets $3.30
Caller folds
"""


GGPOKER_HAND = """PokerCraft Hand #A1B2C3D4
Table: Lunar 6-max - GGPoker
Seat 1: Hero ($25)
Seat 2: Sneaky ($25)
*** HOLE CARDS ***
Hero raises to $0.75
Sneaky calls $0.75
*** FLOP *** [5s 6s Ts]
Hero checks
Sneaky bets $1.50
Hero folds
"""


def test_format_detection_for_major_sites():
    assert HandFormatDetector.detect(POKERSTARS_HAND) is PokerSite.POKERSTARS
    assert HandFormatDetector.detect(PARTYPOKER_HAND) is PokerSite.PARTYPOKER
    assert HandFormatDetector.detect(GGPOKER_HAND) is PokerSite.GGPOKER


def test_single_conversion_preserves_metadata():
    converter = HandConverter()
    result = converter.convert_hand(POKERSTARS_HAND)

    metadata = result.metadata
    assert metadata.detected_site is PokerSite.POKERSTARS
    assert metadata.hand_id == "1234567890"
    assert "Hero" in metadata.players
    assert "Villain1" in metadata.players
    assert metadata.timestamp.startswith("2025/09/30")

    output = result.text.splitlines()
    assert output[0] == "PokerTool Hand History"
    assert any(line.startswith("Stakes: ($0.10/$0.25 USD)") for line in output)
    assert any(line.startswith("PokerStars Hand #1234567890") for line in output)


def test_batch_conversion_skips_invalid_entries():
    converter = HandConverter()
    results = converter.convert_batch([POKERSTARS_HAND, "   ", PARTYPOKER_HAND], PokerSite.GGPOKER)
    assert len(results) == 2
    assert all(result.metadata.target_format is PokerSite.GGPOKER for result in results)

    log = converter.get_conversion_log()
    assert len(log) == 2
    assert log[0]["hand_id"] == "1234567890"


def test_error_correction_cleans_misformatted_text():
    converter = HandConverter()
    corrupted = """PokerStars Hand #9999:  Hold'em No Limit ($0.50/$1.00 USD)
Seat 1:Hero ($100)
Seat 2:Caller ($100)
***HOLE CARDS***
Hero raises to $3
Caller folds"""

    result = converter.convert_hand(corrupted)
    assert "Seat 1: Hero" in result.text
    assert "*** HOLE CARDS ***" in result.text
    assert result.metadata.hand_id == "9999"


def test_convert_file_roundtrip(tmp_path):
    input_path = tmp_path / "hand.txt"
    output_path = tmp_path / "converted.txt"
    input_path.write_text(GGPOKER_HAND, encoding="utf-8")

    converter = HandConverter()
    result = converter.convert_file(input_path, output_path, PokerSite.POKERTOOL)
    assert output_path.exists()
    assert result.metadata.detected_site is PokerSite.GGPOKER
    assert PokerSite.POKERTOOL.value in result.text

    recreated = output_path.read_text(encoding="utf-8")
    assert "--- Original Hand ---" in recreated
