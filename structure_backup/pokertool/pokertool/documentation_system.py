"""Interactive documentation system with help topics and guides."""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_DOC_DIR = Path.home() / ".pokertool" / "docs"
DEFAULT_DOC_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize(text: str) -> str:
    return textwrap.dedent(text).strip()


@dataclass
class HelpTopic:
    """Help topic metadata."""

    topic_id: str
    title: str
    content: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "content": self.content,
            "tags": list(self.tags),
        }


@dataclass
class VideoTutorial:
    """Video tutorial metadata."""

    tutorial_id: str
    title: str
    url: str
    duration_minutes: int
    summary: str


@dataclass
class GuideStep:
    """Single step in an interactive guide."""

    step_id: str
    content: str
    action_hint: Optional[str] = None


@dataclass
class InteractiveGuide:
    """Interactive walkthrough guide."""

    guide_id: str
    title: str
    steps: List[GuideStep]
    estimated_minutes: int


@dataclass
class FAQEntry:
    """Frequently asked question entry."""

    question: str
    answer: str


@dataclass
class ContextHelp:
    """Context-sensitive help mapping."""

    component_id: str
    topic_id: str
    tooltip: str


class DocumentationSystem:
    """Manages help topics, tutorials, and context help."""

    def __init__(self, storage_dir: Path = DEFAULT_DOC_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.topics: Dict[str, HelpTopic] = {}
        self.tutorials: Dict[str, VideoTutorial] = {}
        self.guides: Dict[str, InteractiveGuide] = {}
        self.faqs: List[FAQEntry] = []
        self.context_map: Dict[str, ContextHelp] = {}

    # ------------------------------------------------------------------
    # Topic management
    # ------------------------------------------------------------------
    def register_topic(self, topic: HelpTopic) -> None:
        topic.content = _sanitize(topic.content)
        self.topics[topic.topic_id] = topic

    def search_topics(self, query: str) -> List[HelpTopic]:
        query = query.lower()
        results = [topic for topic in self.topics.values() if query in topic.title.lower() or query in topic.content.lower()]
        results.sort(key=lambda topic: topic.title)
        return results

    def get_topic(self, topic_id: str) -> Optional[HelpTopic]:
        return self.topics.get(topic_id)

    # ------------------------------------------------------------------
    # Tutorials and guides
    # ------------------------------------------------------------------
    def add_tutorial(self, tutorial: VideoTutorial) -> None:
        self.tutorials[tutorial.tutorial_id] = tutorial

    def list_tutorials(self) -> List[VideoTutorial]:
        return sorted(self.tutorials.values(), key=lambda t: t.title)

    def add_guide(self, guide: InteractiveGuide) -> None:
        self.guides[guide.guide_id] = guide

    def get_guide(self, guide_id: str) -> Optional[InteractiveGuide]:
        return self.guides.get(guide_id)

    # ------------------------------------------------------------------
    # FAQ and context help
    # ------------------------------------------------------------------
    def add_faq_entry(self, entry: FAQEntry) -> None:
        self.faqs.append(entry)

    def list_faq(self) -> List[FAQEntry]:
        return list(self.faqs)

    def register_context_help(self, context: ContextHelp) -> None:
        self.context_map[context.component_id] = context

    def context_help(self, component_id: str) -> Optional[ContextHelp]:
        return self.context_map.get(component_id)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def export(self, filename: str = "documentation.json") -> Path:
        path = self.storage_dir / filename
        payload = {
            "topics": [topic.to_dict() for topic in self.topics.values()],
            "tutorials": [tutorial.__dict__ for tutorial in self.tutorials.values()],
            "guides": [self._guide_to_dict(guide) for guide in self.guides.values()],
            "faq": [entry.__dict__ for entry in self.faqs],
            "context": [context.__dict__ for context in self.context_map.values()],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    @staticmethod
    def _guide_to_dict(guide: InteractiveGuide) -> Dict[str, object]:
        return {
            "guide_id": guide.guide_id,
            "title": guide.title,
            "steps": [step.__dict__ for step in guide.steps],
            "estimated_minutes": guide.estimated_minutes,
        }


__all__ = [
    "ContextHelp",
    "DocumentationSystem",
    "FAQEntry",
    "GuideStep",
    "HelpTopic",
    "InteractiveGuide",
    "VideoTutorial",
]
