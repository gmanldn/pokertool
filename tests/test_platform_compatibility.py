import pytest

from pokertool.platform_compatibility import (
    as_dict,
    build_markdown_table,
    get_platform_matrix,
    get_site_support,
)


def test_matrix_contains_expected_sites():
    matrix = get_platform_matrix()
    sites = {entry.site for entry in matrix}
    expected = {"betfair", "pokerstars", "partypoker", "ggpoker", "winamax", "888poker", "acr"}
    missing = expected - sites
    assert not missing, f"Missing site metadata for: {sorted(missing)}"


def test_compliance_flags_exposed():
    matrix = {entry.site: entry for entry in get_platform_matrix()}
    assert not matrix["pokerstars"].hud_enabled
    assert matrix["partypoker"].hud_enabled
    assert not matrix["ggpoker"].tracking_enabled


def test_markdown_table_contains_all_sites():
    table = build_markdown_table()
    for site in ("Betfair", "PokerStars", "888poker"):
        assert site in table


def test_get_site_support_invalid():
    with pytest.raises(KeyError):
        get_site_support("nonexistent-site")


def test_as_dict_matches_matrix():
    dict_entries = {entry["site"]: entry for entry in as_dict()}
    matrix_entries = {entry.site: entry for entry in get_platform_matrix()}
    assert dict_entries.keys() == matrix_entries.keys()
    # Spot check a field
    assert dict_entries["betfair"]["hud_enabled"] == matrix_entries["betfair"].hud_enabled
