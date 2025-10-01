"""Community platform utilities: forums, mentorship, tournaments, and knowledge sharing."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_COMMUNITY_DIR = Path.home() / ".pokertool" / "community"
DEFAULT_COMMUNITY_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ForumPost:
    """Forum post representation."""

    post_id: str
    author: str
    title: str
    content: str
    tags: List[str]
    created_at: float = field(default_factory=time.time)
    replies: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class Challenge:
    """Community challenge metadata."""

    challenge_id: str
    title: str
    description: str
    reward_points: int
    participants: List[str] = field(default_factory=list)
    completed_participants: List[str] = field(default_factory=list)


@dataclass
class MentorshipPair:
    """Mentorship pairing."""

    mentor_id: str
    mentee_id: str
    focus_area: str
    started_at: float = field(default_factory=time.time)


@dataclass
class CommunityTournament:
    """Community tournament entry."""

    tournament_id: str
    name: str
    start_time: float
    format: str
    entrants: List[str] = field(default_factory=list)
    results: Dict[str, int] = field(default_factory=dict)


@dataclass
class KnowledgeArticle:
    """Knowledge sharing article."""

    article_id: str
    title: str
    author: str
    content: str
    categories: List[str]
    created_at: float = field(default_factory=time.time)


class CommunityPlatform:
    """Coordinates community features."""

    def __init__(self, storage_dir: Path = DEFAULT_COMMUNITY_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.posts: Dict[str, ForumPost] = {}
        self.challenges: Dict[str, Challenge] = {}
        self.mentorships: List[MentorshipPair] = []
        self.tournaments: Dict[str, CommunityTournament] = {}
        self.articles: Dict[str, KnowledgeArticle] = {}

    # ------------------------------------------------------------------
    # Forums & knowledge
    # ------------------------------------------------------------------
    def create_post(self, post: ForumPost) -> None:
        self.posts[post.post_id] = post

    def reply_to_post(self, post_id: str, author: str, message: str) -> None:
        post = self.posts.get(post_id)
        if not post:
            raise KeyError(f"Unknown post: {post_id}")
        post.replies.append({"author": author, "message": message, "timestamp": time.time()})

    def add_article(self, article: KnowledgeArticle) -> None:
        self.articles[article.article_id] = article

    def list_articles(self, category: Optional[str] = None) -> List[KnowledgeArticle]:
        articles = list(self.articles.values())
        if category:
            articles = [article for article in articles if category in article.categories]
        return sorted(articles, key=lambda article: article.created_at, reverse=True)

    # ------------------------------------------------------------------
    # Challenges & mentorship
    # ------------------------------------------------------------------
    def create_challenge(self, challenge: Challenge) -> None:
        self.challenges[challenge.challenge_id] = challenge

    def join_challenge(self, challenge_id: str, player_id: str) -> None:
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            raise KeyError(f"Unknown challenge: {challenge_id}")
        if player_id not in challenge.participants:
            challenge.participants.append(player_id)

    def complete_challenge(self, challenge_id: str, player_id: str) -> None:
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            raise KeyError(f"Unknown challenge: {challenge_id}")
        if player_id in challenge.participants and player_id not in challenge.completed_participants:
            challenge.completed_participants.append(player_id)

    def create_mentorship(self, pair: MentorshipPair) -> None:
        self.mentorships.append(pair)

    # ------------------------------------------------------------------
    # Tournaments
    # ------------------------------------------------------------------
    def schedule_tournament(self, tournament: CommunityTournament) -> None:
        self.tournaments[tournament.tournament_id] = tournament

    def register_tournament_player(self, tournament_id: str, player_id: str) -> None:
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            raise KeyError(f"Unknown community tournament: {tournament_id}")
        if player_id not in tournament.entrants:
            tournament.entrants.append(player_id)

    def record_tournament_result(self, tournament_id: str, player_id: str, position: int) -> None:
        tournament = self.tournaments.get(tournament_id)
        if not tournament:
            raise KeyError(f"Unknown community tournament: {tournament_id}")
        tournament.results[player_id] = position

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def export(self, filename: str = "community.json") -> Path:
        path = self.storage_dir / filename
        payload = {
            "posts": [self._serialize_post(post) for post in self.posts.values()],
            "challenges": [challenge.__dict__ for challenge in self.challenges.values()],
            "mentorships": [pair.__dict__ for pair in self.mentorships],
            "tournaments": [tournament.__dict__ for tournament in self.tournaments.values()],
            "articles": [article.__dict__ for article in self.articles.values()],
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    @staticmethod
    def _serialize_post(post: ForumPost) -> Dict[str, object]:
        data = post.__dict__.copy()
        data["replies"] = list(post.replies)
        return data


__all__ = [
    "Challenge",
    "CommunityPlatform",
    "CommunityTournament",
    "ForumPost",
    "KnowledgeArticle",
    "MentorshipPair",
]
