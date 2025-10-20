"""Theme engine with editor, previews, and marketplace integration."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_THEME_DIR = Path.home() / ".pokertool" / "themes"
DEFAULT_THEME_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Palette:
    """Color palette definition."""

    primary: str
    secondary: str
    accent: str
    background: str
    text: str


@dataclass
class Typography:
    """Typography definition."""

    font_family: str
    base_size: int
    heading_weight: str = "bold"
    body_weight: str = "normal"


@dataclass
class Theme:
    """Theme definition combining palette and typography."""

    theme_id: str
    name: str
    palette: Palette
    typography: Typography
    sounds_enabled: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ThemeDraft:
    """Draft theme used by the editor before publishing."""

    draft_id: str
    base_theme_id: Optional[str]
    theme: Theme
    updated_at: float = field(default_factory=time.time)


@dataclass
class MarketplaceEntry:
    """Theme listing metadata for marketplace."""

    theme_id: str
    author: str
    price: float
    description: str
    downloads: int = 0


class ThemeEngine:
    """Core theme registry and application helper."""

    def __init__(self, storage_dir: Path = DEFAULT_THEME_DIR):
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._themes: Dict[str, Theme] = {}
        self._active_theme_id: Optional[str] = None
        self._load_installed_themes()

    def register_theme(self, theme: Theme, activate: bool = False) -> None:
        self._themes[theme.theme_id] = theme
        self._save_theme(theme)
        if activate:
            self._active_theme_id = theme.theme_id

    def list_themes(self) -> List[Theme]:
        return sorted(self._themes.values(), key=lambda theme: theme.name)

    def get_theme(self, theme_id: str) -> Optional[Theme]:
        return self._themes.get(theme_id)

    def active_theme(self) -> Optional[Theme]:
        if self._active_theme_id:
            return self._themes.get(self._active_theme_id)
        return None

    def apply_theme(self, theme_id: str, components: Optional[List[str]] = None) -> Dict[str, Dict[str, str]]:
        theme = self.get_theme(theme_id)
        if not theme:
            raise KeyError(f"Unknown theme: {theme_id}")
        components = components or ["window", "toolbar", "table", "dialog"]
        applied = {}
        for component in components:
            applied[component] = {
                "background": theme.palette.background,
                "text": theme.palette.text,
                "accent": theme.palette.accent,
                "font": theme.typography.font_family,
                "font_size": str(theme.typography.base_size),
            }
        self._active_theme_id = theme_id
        return applied

    def preview_theme(self, theme: Theme) -> Dict[str, Dict[str, str]]:
        return {
            "preview_window": {
                "background": theme.palette.background,
                "text": theme.palette.text,
                "accent": theme.palette.accent,
            },
            "typography": {
                "font": theme.typography.font_family,
                "heading_weight": theme.typography.heading_weight,
            },
        }

    def _save_theme(self, theme: Theme) -> None:
        path = self._storage_dir / f"{theme.theme_id}.json"
        path.write_text(json.dumps(self._serialize_theme(theme), indent=2, sort_keys=True), encoding="utf-8")

    def _load_installed_themes(self) -> None:
        for file in self._storage_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            theme = self._deserialize_theme(data)
            self._themes[theme.theme_id] = theme

    @staticmethod
    def _serialize_theme(theme: Theme) -> Dict[str, object]:
        payload = asdict(theme)
        payload["palette"] = asdict(theme.palette)
        payload["typography"] = asdict(theme.typography)
        return payload

    @staticmethod
    def _deserialize_theme(data: Dict[str, object]) -> Theme:
        palette = Palette(**data["palette"])
        typography = Typography(**data["typography"])
        return Theme(theme_id=data["theme_id"], name=data["name"], palette=palette, typography=typography, sounds_enabled=data.get("sounds_enabled", False), metadata=data.get("metadata", {}))


class ThemeEditor:
    """Draft-based theme editor."""

    def __init__(self, engine: ThemeEngine):
        self.engine = engine
        self._drafts: Dict[str, ThemeDraft] = {}

    def create_draft(self, draft_id: str, base_theme_id: Optional[str], theme: Theme) -> ThemeDraft:
        draft = ThemeDraft(draft_id=draft_id, base_theme_id=base_theme_id, theme=theme)
        self._drafts[draft_id] = draft
        return draft

    def update_draft(self, draft_id: str, theme: Theme) -> ThemeDraft:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise KeyError(f"Unknown draft: {draft_id}")
        draft.theme = theme
        draft.updated_at = time.time()
        self._drafts[draft_id] = draft
        return draft

    def publish_draft(self, draft_id: str, activate: bool = False) -> Theme:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise KeyError(f"Unknown draft: {draft_id}")
        self.engine.register_theme(draft.theme, activate=activate)
        return draft.theme

    def list_drafts(self) -> List[ThemeDraft]:
        return sorted(self._drafts.values(), key=lambda draft: draft.updated_at, reverse=True)


class ThemeMarketplace:
    """Simple marketplace manager for downloadable themes."""

    def __init__(self):
        self._entries: Dict[str, MarketplaceEntry] = {}

    def register_entry(self, entry: MarketplaceEntry) -> None:
        self._entries[entry.theme_id] = entry

    def list_entries(self) -> List[MarketplaceEntry]:
        return sorted(self._entries.values(), key=lambda e: e.price)

    def download_theme(self, theme_id: str) -> MarketplaceEntry:
        entry = self._entries.get(theme_id)
        if not entry:
            raise KeyError(f"Unknown marketplace entry: {theme_id}")
        entry.downloads += 1
        return entry


__all__ = [
    "MarketplaceEntry",
    "Palette",
    "Theme",
    "ThemeDraft",
    "ThemeEditor",
    "ThemeEngine",
    "ThemeMarketplace",
    "Typography",
]
