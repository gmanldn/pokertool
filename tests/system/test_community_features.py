"""Tests for the community platform."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.fspath(Path(__file__).resolve().parents[2] / "src"))

from pokertool.community_features import (
    Challenge,
    CommunityPlatform,
    CommunityTournament,
    ForumPost,
    KnowledgeArticle,
    MentorshipPair,
)


def create_platform(tmp_path: Path) -> CommunityPlatform:
    storage = tmp_path / "community"
    return CommunityPlatform(storage_dir=storage)


def test_forum_posts_challenges_and_articles(tmp_path):
    platform = create_platform(tmp_path)

    post = ForumPost(post_id="p1", author="coach", title="Range Review", content="Let's discuss turn ranges.", tags=["strategy"])
    platform.create_post(post)
    platform.reply_to_post("p1", author="student", message="I like checking turn here.")
    assert platform.posts["p1"].replies

    challenge = Challenge(challenge_id="c1", title="Play 10 SNGs", description="Finish 10 SNG tournaments this week", reward_points=500)
    platform.create_challenge(challenge)
    platform.join_challenge("c1", "hero")
    platform.complete_challenge("c1", "hero")
    assert "hero" in platform.challenges["c1"].completed_participants

    article = KnowledgeArticle(article_id="a1", title="ICM Basics", author="mentor", content="Shortstack play tips", categories=["icm", "tournaments"])
    platform.add_article(article)
    articles = platform.list_articles(category="icm")
    assert articles and articles[0].article_id == "a1"

    pair = MentorshipPair(mentor_id="coach", mentee_id="hero", focus_area="postflop")
    platform.create_mentorship(pair)
    assert platform.mentorships


def test_tournaments_and_export(tmp_path):
    platform = create_platform(tmp_path)
    tournament = CommunityTournament(tournament_id="t1", name="Monthly Cup", start_time=time.time() + 3600, format="bounty")
    platform.schedule_tournament(tournament)
    platform.register_tournament_player("t1", "hero")
    platform.record_tournament_result("t1", "hero", 1)

    export_path = platform.export()
    assert export_path.exists()
