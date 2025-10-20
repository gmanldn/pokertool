"""Centralised platform compatibility matrix for PokerTool.

This module aggregates the current support posture for target poker sites,
including detection strategy, compliance constraints, and key adaptations.
It exists so tooling and documentation can present a single source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .compliance import PokerSiteCompliance


@dataclass(frozen=True)
class SiteSupport:
    """Support metadata for a poker site."""

    site: str
    title: str
    tier: str
    detection: str
    hand_history: str
    hud_enabled: bool
    tracking_enabled: bool
    notes: List[str] = field(default_factory=list)
    restricted_features: List[str] = field(default_factory=list)
    max_tables: Optional[int] = None
    compliance_last_updated: Optional[str] = None
    references: Dict[str, str] = field(default_factory=dict)

    @property
    def hud_status(self) -> str:
        """Return a human readable HUD status."""
        return "Enabled" if self.hud_enabled else "Disabled by compliance"

    @property
    def tracking_status(self) -> str:
        """Return a human readable tracking status."""
        return "Enabled" if self.tracking_enabled else "Disabled by compliance"

    @property
    def restricted_features_display(self) -> str:
        """Return restricted features as comma-separated text."""
        return ", ".join(sorted(self.restricted_features)) if self.restricted_features else "–"


_SITE_METADATA: Dict[str, Dict[str, object]] = {
    "betfair": {
        "title": "Betfair",
        "tier": "Tier 1",
        "detection": (
            "Specialised Betfair detector with Chrome DevTools fast-path fallback."
        ),
        "hand_history": "Live capture via OCR/CDP (no raw hand import yet).",
        "notes": [
            "Primary scraper: src/pokertool/modules/poker_screen_scraper_betfair.py",
            "ROI calibration: src/pokertool/modules/betfair_accuracy_improvements.py",
            "CDP extractor: src/pokertool/modules/chrome_devtools_scraper.py",
        ],
        "references": {
            "scraper": "src/pokertool/modules/poker_screen_scraper_betfair.py",
            "roi": "src/pokertool/modules/betfair_accuracy_improvements.py",
            "cdp": "src/pokertool/modules/chrome_devtools_scraper.py",
        },
    },
    "pokerstars": {
        "title": "PokerStars",
        "tier": "Tier 2",
        "detection": "Universal detector with SmartPokerDetector prioritisation.",
        "hand_history": "Supported via HandConverter (text import).",
        "notes": [
            "Universal detection path: src/pokertool/modules/poker_screen_scraper_betfair.py",
            "Window prioritisation: src/pokertool/smart_poker_detector.py",
            "Hand history detection: src/pokertool/hand_converter.py",
        ],
        "references": {
            "detector": "src/pokertool/smart_poker_detector.py",
            "hand_converter": "src/pokertool/hand_converter.py",
        },
    },
    "partypoker": {
        "title": "PartyPoker",
        "tier": "Tier 2",
        "detection": "Universal detector with colour heuristics + OCR.",
        "hand_history": "Supported via HandConverter (text import).",
        "notes": [
            "Universal detection path: src/pokertool/modules/poker_screen_scraper_betfair.py",
            "Hand history format: src/pokertool/hand_converter.py",
            "Multi-table layout support: src/pokertool/multi_table_support.py",
        ],
        "references": {
            "hand_converter": "src/pokertool/hand_converter.py",
            "multi_table": "src/pokertool/multi_table_support.py",
        },
    },
    "ggpoker": {
        "title": "GGPoker",
        "tier": "Fallback",
        "detection": "Universal detector (screen OCR only, HUD disabled).",
        "hand_history": "Supported via HandConverter (text import).",
        "notes": [
            "Compliance disables live HUD/tracking: src/pokertool/compliance.py",
            "Universal detection fallback: src/pokertool/modules/poker_screen_scraper_betfair.py",
            "Consider post-session analysis only for aggregated stats.",
        ],
        "references": {
            "compliance": "src/pokertool/compliance.py",
            "hand_converter": "src/pokertool/hand_converter.py",
        },
    },
    "winamax": {
        "title": "Winamax",
        "tier": "Fallback",
        "detection": "Universal detector with OCR heuristics.",
        "hand_history": "Supported via HandConverter (text import).",
        "notes": [
            "Universal detection fallback: src/pokertool/modules/poker_screen_scraper_betfair.py",
            "Hand history format: src/pokertool/hand_converter.py",
        ],
        "references": {
            "hand_converter": "src/pokertool/hand_converter.py",
        },
    },
    "888poker": {
        "title": "888poker",
        "tier": "Fallback",
        "detection": "Universal detector with compliance-restricted OCR usage.",
        "hand_history": "Supported via HandConverter (text import).",
        "notes": [
            "Compliance restricts OCR-intensive features: src/pokertool/compliance.py",
            "Hand history detection: src/pokertool/hand_converter.py",
        ],
        "references": {
            "compliance": "src/pokertool/compliance.py",
            "hand_converter": "src/pokertool/hand_converter.py",
        },
    },
    "acr": {
        "title": "Americas Cardroom",
        "tier": "Tier 2",
        "detection": "Universal detector with aggressive multi-table tuning.",
        "hand_history": "Supported via HandConverter (text import).",
        "notes": [
            "Universal detection fallback: src/pokertool/modules/poker_screen_scraper_betfair.py",
            "Hand history detection: src/pokertool/hand_converter.py",
            "Multi-table presets: src/pokertool/multi_table_support.py",
        ],
        "references": {
            "hand_converter": "src/pokertool/hand_converter.py",
            "multi_table": "src/pokertool/multi_table_support.py",
        },
    },
}


def _build_site_support(site: str, metadata: Dict[str, object], compliance: PokerSiteCompliance) -> SiteSupport:
    policy = compliance.get_site_restrictions(site) or compliance.get_site_restrictions("generic")
    return SiteSupport(
        site=site,
        title=metadata["title"],
        tier=metadata["tier"],
        detection=metadata["detection"],
        hand_history=metadata["hand_history"],
        hud_enabled=bool(policy.get("allows_hud", False)),
        tracking_enabled=bool(policy.get("allows_tracking", False)),
        notes=list(metadata.get("notes", [])),
        restricted_features=list(policy.get("restricted_features", [])),
        max_tables=policy.get("max_tables"),
        compliance_last_updated=policy.get("last_updated"),
        references=dict(metadata.get("references", {})),
    )


def get_platform_matrix() -> List[SiteSupport]:
    """Return the compatibility matrix for all configured sites."""
    compliance = PokerSiteCompliance()
    matrix = [
        _build_site_support(site, metadata, compliance)
        for site, metadata in _SITE_METADATA.items()
    ]
    tier_order = {"Tier 1": 0, "Tier 2": 1, "Fallback": 2}
    return sorted(matrix, key=lambda item: (tier_order.get(item.tier, 99), item.title.lower()))


def get_site_support(site: str) -> SiteSupport:
    """Return support metadata for a specific site."""
    site_key = site.lower()
    metadata = _SITE_METADATA.get(site_key)
    if not metadata:
        raise KeyError(f"No platform compatibility metadata for site: {site}")
    compliance = PokerSiteCompliance()
    return _build_site_support(site_key, metadata, compliance)


def iter_site_supports(sites: Optional[Iterable[str]] = None) -> Iterable[SiteSupport]:
    """Iterate over `SiteSupport` entries, respecting optional filtering."""
    if sites is None:
        return get_platform_matrix()
    site_keys = [site.lower() for site in sites]
    compliance = PokerSiteCompliance()
    return (
        _build_site_support(site, _SITE_METADATA[site], compliance)
        for site in site_keys
        if site in _SITE_METADATA
    )


def build_markdown_table(sites: Optional[Iterable[str]] = None) -> str:
    """Return a Markdown table representing the compatibility matrix."""
    supports = list(iter_site_supports(sites))
    header = (
        "| Site | Tier | Detection | HUD | Tracking | Hand Histories | Restricted Features |\n"
        "| --- | --- | --- | --- | --- | --- | --- |"
    )
    rows = [header]
    for support in supports:
        rows.append(
            "| {title} | {tier} | {detection} | {hud} | {tracking} | {hand_history} | {restricted} |".format(
                title=support.title,
                tier=support.tier,
                detection=support.detection.replace("|", "/"),
                hud=support.hud_status,
                tracking=support.tracking_status,
                hand_history=support.hand_history.replace("|", "/"),
                restricted=support.restricted_features_display.replace("|", "/"),
            )
        )
    return "\n".join(rows)


def as_dict(sites: Optional[Iterable[str]] = None) -> List[Dict[str, object]]:
    """Return the compatibility matrix as plain dictionaries (for APIs/tests)."""
    return [
        {
            "site": support.site,
            "title": support.title,
            "tier": support.tier,
            "detection": support.detection,
            "hand_history": support.hand_history,
            "hud_enabled": support.hud_enabled,
            "tracking_enabled": support.tracking_enabled,
            "restricted_features": list(support.restricted_features),
            "max_tables": support.max_tables,
            "compliance_last_updated": support.compliance_last_updated,
            "notes": list(support.notes),
            "references": dict(support.references),
        }
        for support in iter_site_supports(sites)
    ]


def main() -> None:
    """CLI entry point for ad-hoc inspection."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="PokerTool platform compatibility matrix")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown table).",
    )
    parser.add_argument(
        "--sites",
        nargs="*",
        help="Optional list of site names to filter by (e.g. betfair pokerstars).",
    )
    args = parser.parse_args()

    if args.format == "markdown":
        print(build_markdown_table(args.sites))
    else:
        print(json.dumps(as_dict(args.sites), indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI helper
    main()
