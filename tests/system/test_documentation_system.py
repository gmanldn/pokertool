"""Tests for the interactive documentation system."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.documentation_system import (
    ContextHelp,
    DocumentationSystem,
    FAQEntry,
    GuideStep,
    HelpTopic,
    InteractiveGuide,
    VideoTutorial,
)


def create_docs(tmp_path: Path) -> DocumentationSystem:
    storage = tmp_path / "docs"
    return DocumentationSystem(storage_dir=storage)


def test_topic_registration_and_search(tmp_path):
    docs = create_docs(tmp_path)
    topic = HelpTopic(topic_id="getting_started", title="Getting Started", content="""
    Launch PokerTool and connect to your database using the setup wizard.
    """, tags=["setup"])
    docs.register_topic(topic)

    result = docs.search_topics("launch")
    assert result and result[0].topic_id == "getting_started"
    assert "setup wizard" in result[0].content

    retrieved = docs.get_topic("getting_started")
    assert retrieved and retrieved.title == "Getting Started"


def test_guides_faq_and_context_help(tmp_path):
    docs = create_docs(tmp_path)
    guide = InteractiveGuide(
        guide_id="hud_setup",
        title="HUD Setup",
        steps=[
            GuideStep(step_id="s1", content="Open HUD designer"),
            GuideStep(step_id="s2", content="Drag stats onto overlay", action_hint="use drag-and-drop"),
        ],
        estimated_minutes=5,
    )
    docs.add_guide(guide)
    assert docs.get_guide("hud_setup")

    tutorial = VideoTutorial(tutorial_id="intro", title="Intro", url="https://example.com", duration_minutes=4, summary="Overview")
    docs.add_tutorial(tutorial)
    assert docs.list_tutorials()[0].tutorial_id == "intro"

    docs.add_faq_entry(FAQEntry(question="How to reset?", answer="Use settings panel."))
    assert docs.list_faq()[0].question.startswith("How to reset")

    context = ContextHelp(component_id="hud-designer", topic_id="getting_started", tooltip="Need help with HUD?")
    docs.register_context_help(context)
    assert docs.context_help("hud-designer").tooltip.endswith("HUD?")

    export_path = docs.export("docs_dump.json")
    assert export_path.exists()
