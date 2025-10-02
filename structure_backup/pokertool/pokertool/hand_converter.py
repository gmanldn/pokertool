"""Universal hand history converter with format detection."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


class ConversionError(Exception):
    """Raised when a hand conversion cannot be completed."""


class PokerSite(Enum):
    """Supported poker sites and canonical targets."""

    POKERSTARS = "PokerStars"
    PARTYPOKER = "PartyPoker"
    GGPOKER = "GGPoker"
    WINAMAX = "Winamax"
    POKER888 = "888poker"
    ACR = "ACR"
    POKERTOOL = "PokerTool"
    UNKNOWN = "Unknown"

    @classmethod
    def from_value(cls, value: Optional[str]) -> "PokerSite":
        if isinstance(value, cls):
            return value
        if not value:
            return cls.POKERTOOL
        normalized = value.strip().lower()
        for site in cls:
            if site.value.lower() == normalized or site.name.lower() == normalized:
                return site
        return cls.POKERTOOL


@dataclass
class HandMetadata:
    """Metadata preserved during conversion."""

    detected_site: PokerSite
    target_format: PokerSite
    original_site_label: Optional[str]
    hand_id: str
    table_name: Optional[str] = None
    game_type: Optional[str] = None
    stakes: Optional[str] = None
    timestamp: Optional[str] = None
    players: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "detected_site": self.detected_site.value,
            "target_format": self.target_format.value,
            "original_site_label": self.original_site_label,
            "hand_id": self.hand_id,
            "table_name": self.table_name,
            "game_type": self.game_type,
            "stakes": self.stakes,
            "timestamp": self.timestamp,
            "players": list(self.players),
        }


@dataclass
class HandConversionResult:
    """Returned payload for each conversion."""

    text: str
    metadata: HandMetadata


class HandFormatDetector:
    """Detect the originating site for a raw hand history string."""

    _PATTERNS = {
        PokerSite.POKERSTARS: re.compile(r"PokerStars Hand #", re.IGNORECASE),
        PokerSite.PARTYPOKER: re.compile(r"\bPartyPoker\b|\bpartypoker\.net\b", re.IGNORECASE),
        PokerSite.GGPOKER: re.compile(r"\bGGPoker\b|PokerCraft", re.IGNORECASE),
        PokerSite.WINAMAX: re.compile(r"Winamax Poker", re.IGNORECASE),
        PokerSite.POKER888: re.compile(r"888poker", re.IGNORECASE),
        PokerSite.ACR: re.compile(r"Americas Cardroom|ACR", re.IGNORECASE),
    }

    @classmethod
    def detect(cls, raw_hand: str) -> PokerSite:
        for site, pattern in cls._PATTERNS.items():
            if pattern.search(raw_hand):
                return site
        # Fallback heuristics for anonymised exports
        if "Seat" in raw_hand and "*** HOLE CARDS ***" in raw_hand:
            return PokerSite.POKERSTARS
        return PokerSite.UNKNOWN


class HandConverter:
    """High-level interface for converting hand histories between formats."""

    def __init__(self) -> None:
        self._log: List[HandMetadata] = []

    def convert_hand(
        self,
        raw_hand: str,
        target_format: PokerSite | str = PokerSite.POKERTOOL
    ) -> HandConversionResult:
        if not raw_hand or not raw_hand.strip():
            raise ConversionError("Empty hand history supplied")

        cleaned = self._sanitize(raw_hand)
        detected = HandFormatDetector.detect(cleaned)
        target = PokerSite.from_value(target_format)
        metadata = self._extract_metadata(cleaned, detected, target)
        converted_text = self._render_converted_hand(cleaned, metadata)
        self._log.append(metadata)
        return HandConversionResult(text=converted_text, metadata=metadata)

    def convert_batch(
        self,
        raw_hands: Sequence[str],
        target_format: PokerSite | str = PokerSite.POKERTOOL
    ) -> List[HandConversionResult]:
        results: List[HandConversionResult] = []
        for hand in raw_hands:
            try:
                results.append(self.convert_hand(hand, target_format))
            except ConversionError:
                continue
        return results

    def convert_file(
        self,
        input_path: Path,
        output_path: Path,
        target_format: PokerSite | str = PokerSite.POKERTOOL
    ) -> HandConversionResult:
        try:
            raw_text = input_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConversionError(f"Input file not found: {input_path}") from exc
        result = self.convert_hand(raw_text, target_format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.text, encoding="utf-8")
        return result

    def get_conversion_log(self) -> List[dict]:
        return [metadata.to_dict() for metadata in self._log]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _sanitize(self, raw_hand: str) -> str:
        text = raw_hand.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"Seat (\d+):(\S)", r"Seat \1: \2", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Ensure key sections are on their own line for broken exports.
        text = text.replace("***HOLE CARDS***", "*** HOLE CARDS ***")
        text = text.replace("***FLOP***", "*** FLOP ***")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    def _extract_metadata(
        self,
        cleaned: str,
        detected: PokerSite,
        target: PokerSite
    ) -> HandMetadata:
        original_site_label = self._extract_site_label(cleaned)
        hand_id = self._extract_hand_id(cleaned)
        table_name = self._search(cleaned, r"Table '([^']+)'")
        game_type = self._search(cleaned, r"(Hold'em|Omaha|Stud|Razz)")
        stakes = self._search(cleaned, r"\(([^)]+)\)")
        timestamp = self._search(cleaned, r"(\d{4}/\d{2}/\d{2}[^\n]*)")
        players = self._extract_players(cleaned)
        metadata = HandMetadata(
            detected_site=detected,
            target_format=target,
            original_site_label=original_site_label,
            hand_id=hand_id,
            table_name=table_name,
            game_type=game_type,
            stakes=stakes,
            timestamp=timestamp,
            players=players,
        )
        if metadata.stakes and not metadata.stakes.startswith("("):
            metadata.stakes = f"({metadata.stakes.rstrip(')')})"
        return metadata

    def _extract_site_label(self, cleaned: str) -> Optional[str]:
        header_line = cleaned.split("\n", 1)[0]
        return header_line.split(" Hand #")[0].strip() if "Hand #" in header_line else header_line[:30]

    def _extract_hand_id(self, cleaned: str) -> str:
        match = re.search(r"Hand #([\w\-]+)", cleaned)
        if match:
            return match.group(1)
        # Generate deterministic fallback id when parsing fails.
        digest = hashlib.blake2s(cleaned.encode("utf-8")).hexdigest()[:16]
        return f"AUTO-{digest}"

    def _extract_players(self, cleaned: str) -> List[str]:
        players = re.findall(r"Seat \d+: ([^\(\n]+)", cleaned)
        return [player.strip() for player in players]

    def _render_converted_hand(self, cleaned: str, metadata: HandMetadata) -> str:
        lines = [
            "PokerTool Hand History",
            f"Original Site: {metadata.original_site_label or 'Unknown'}",
            f"Detected Site: {metadata.detected_site.value}",
            f"Converted To: {metadata.target_format.value}",
            f"Hand ID: {metadata.hand_id}",
        ]
        if metadata.game_type:
            lines.append(f"Game Type: {metadata.game_type}")
        if metadata.stakes:
            lines.append(f"Stakes: {metadata.stakes}")
        if metadata.table_name:
            lines.append(f"Table: {metadata.table_name}")
        if metadata.timestamp:
            lines.append(f"Timestamp: {metadata.timestamp}")
        if metadata.players:
            lines.append("Players:")
            for player in metadata.players:
                lines.append(f"  - {player}")
        lines.extend(["--- Original Hand ---", cleaned])
        return "\n".join(lines)

    @staticmethod
    def _search(text: str, pattern: str) -> Optional[str]:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None


__all__ = [
    "ConversionError",
    "HandConversionResult",
    "HandConverter",
    "HandFormatDetector",
    "HandMetadata",
    "PokerSite",
]
