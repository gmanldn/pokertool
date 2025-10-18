#!/usr/bin/env python3
"""
Smoke-test helpers for verifying logging in the Betfair scraper module.

Historically this file executed imperatively at import time which caused the
entire pytest session to abort whenever screen capture was unavailable (a common
scenario on CI or headless environments). The module now exposes a proper test
that gracefully skips in those situations, while retaining a `main()` entry
point so developers can still run the comprehensive logging demo manually.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from pokertool.modules.poker_screen_scraper_betfair import create_scraper
except Exception as exc:  # pragma: no cover - handled in tests
    create_scraper = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.mark.scraper
@pytest.mark.integration
@pytest.mark.requires_display
def test_scraper_logging_smoke(caplog: pytest.LogCaptureFixture) -> None:
    """Ensure the Betfair scraper initializes and logs consistently."""
    if IMPORT_ERROR is not None:
        pytest.skip(f"Scraper unavailable: {IMPORT_ERROR}")

    caplog.set_level(logging.INFO)
    scraper = create_scraper("BETFAIR")

    # Initialization should produce informative logs.
    init_logs = [record for record in caplog.records if "PokerScreenScraper initialized" in record.getMessage()]
    assert init_logs, "Scraper initialization did not emit expected logs."

    with caplog.at_level(logging.INFO):
        try:
            image = scraper.capture_table()
        except Exception as exc:
            pytest.skip(f"Screen capture not supported in test environment: {exc}")

    if image is None:
        pytest.skip("Screen capture returned no data; likely running headless.")

    # Even when no table is present the detector should respond gracefully.
    is_poker, confidence, details = scraper.detect_poker_table(image)
    assert 0.0 <= confidence <= 1.0, "Detector returned an invalid confidence score."
    assert isinstance(details, dict)

    if is_poker:
        table_state = scraper.analyze_table(image)
        assert table_state is not None


def main() -> None:
    """Manual CLI entry point mirroring the previous behaviour."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    print("=" * 80)
    print("BETFAIR SCRAPER LOGGING TEST")
    print("=" * 80, "\n")

    if IMPORT_ERROR is not None:
        print(f"❌ Failed to import scraper: {IMPORT_ERROR}")
        sys.exit(1)

    scraper = create_scraper("BETFAIR")
    print(f"✓ Scraper module imported successfully -> {type(scraper).__name__}")

    try:
        image = scraper.capture_table()
    except Exception as exc:
        print(f"❌ Screen capture failed: {exc}")
        sys.exit(1)

    if image is None:
        print("❌ Screen capture returned no image.")
        sys.exit(1)

    print(f"✓ Captured image of size {image.shape[1]}x{image.shape[0]}")

    is_poker, confidence, details = scraper.detect_poker_table(image)
    verdict = "DETECTED" if is_poker else "NOT DETECTED"
    print(f"\nDetector verdict: {verdict} (confidence: {confidence:.1%})")
    print(f"Detector metadata: {details}")

    if is_poker:
        table_state = scraper.analyze_table(image)
        print("\nTable analysis complete:")
        print(f"- Active players: {table_state.active_players}")
        print(f"- Pot size: {table_state.pot_size}")
        print(f"- Stage: {table_state.stage}")
        print(f"- Board cards: {len(table_state.board_cards)}")
        print(f"- Hero cards: {len(table_state.hero_cards)}")
        print(f"- Dealer seat: {table_state.dealer_seat}")
    else:
        print("\nNo table detected; open a Betfair table and re-run this script.")

if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
