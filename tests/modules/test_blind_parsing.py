import pytest

from pokertool.modules.poker_screen_scraper_betfair import PokerScreenScraper


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Blinds: £0.05/£0.10 Ante £0.02", (0.05, 0.10, 0.02)),
        ("$1/$2/$0.25", (1.0, 2.0, 0.25)),
        ("Blinds 2/4", (2.0, 4.0, 0.0)),
        ("SB 0.5 BB 1.0 antes 0.1", (0.5, 1.0, 0.1)),
    ],
)
def test_parse_blinds_from_text(text, expected):
    result = PokerScreenScraper._parse_blinds_from_text(text)
    assert result is not None
    sb, bb, ante = result
    assert pytest.approx(sb, rel=1e-6) == expected[0]
    assert pytest.approx(bb, rel=1e-6) == expected[1]
    assert pytest.approx(ante, rel=1e-6) == expected[2]


def test_parse_blinds_returns_none_for_invalid_text():
    assert PokerScreenScraper._parse_blinds_from_text("No blind information here") is None
