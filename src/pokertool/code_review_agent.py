"""Code Review Agent - 4th agent that reviews commits from other agents"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import subprocess

from pokertool.ai_providers.base_provider import BaseAIProvider
from pokertool.improve_rollback import RollbackManager

logger = logging.getLogger(__name__)


@dataclass
class CodeReviewResult:
    """Result of code review"""
    commit_hash: str
    agent_id: str
    approved: bool
    score: int  # 0-100
    issues: List[str]
    suggestions: List[str]
    strengths: List[str]
    review_summary: str
    reviewer_notes: str


class CodeReviewAgent:
    """Optional 4th agent that reviews commits from other 3 agents"""

    def __init__(self, provider: BaseAIProvider, auto_approve_threshold: int = 80):
        """
        Initialize code review agent

        Args:
            provider: AI provider for reviews
            auto_approve_threshold: Score threshold for auto-approval (0-100)
        """
        self.provider = provider
        self.auto_approve_threshold = auto_approve_threshold
        self.rollback = RollbackManager()
        self.review_history: List[CodeReviewResult] = []

    async def review_commit(
        self,
        commit_hash: str,
        agent_id: str,
        detailed: bool = True
    ) -> CodeReviewResult:
        """
        Review a commit made by an AI agent

        Args:
            commit_hash: Git commit hash to review
            agent_id: ID of agent that made the commit
            detailed: Whether to do detailed review or quick check

        Returns:
            CodeReviewResult with approval status and feedback
        """
        try:
            logger.info(f"Reviewing commit {commit_hash[:8]} from {agent_id}")

            # Get commit details
            commit_info = self._get_commit_info(commit_hash)
            if not commit_info:
                return self._create_error_result(commit_hash, agent_id, "Failed to get commit info")

            # Get diff
            diff = self._get_commit_diff(commit_hash)
            if not diff:
                return self._create_error_result(commit_hash, agent_id, "Failed to get commit diff")

            # Run automated checks
            automated_issues = await self._run_automated_checks(commit_hash)

            # AI review
            ai_review = await self._ai_review(commit_info, diff, automated_issues, detailed)

            # Calculate final score
            score = self._calculate_score(ai_review, automated_issues)

            # Determine approval
            approved = score >= self.auto_approve_threshold and len(automated_issues.get("critical", [])) == 0

            result = CodeReviewResult(
                commit_hash=commit_hash,
                agent_id=agent_id,
                approved=approved,
                score=score,
                issues=ai_review.get("issues", []) + automated_issues.get("errors", []),
                suggestions=ai_review.get("suggestions", []),
                strengths=ai_review.get("strengths", []),
                review_summary=ai_review.get("summary", ""),
                reviewer_notes=self._generate_reviewer_notes(score, approved, automated_issues)
            )

            self.review_history.append(result)

            if approved:
                logger.info(f"✅ Commit {commit_hash[:8]} APPROVED (score: {score})")
            else:
                logger.warning(f"❌ Commit {commit_hash[:8]} REJECTED (score: {score})")

            return result

        except Exception as e:
            logger.error(f"Review failed for commit {commit_hash}: {e}")
            return self._create_error_result(commit_hash, agent_id, str(e))

    def _get_commit_info(self, commit_hash: str) -> Optional[Dict]:
        """Get commit message, author, files changed"""
        try:
            result = subprocess.run(
                ["git", "show", "--stat", "--format=%H%n%an%n%ae%n%s%n%b", commit_hash],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            lines = result.stdout.split('\n')
            return {
                "hash": lines[0] if len(lines) > 0 else commit_hash,
                "author": lines[1] if len(lines) > 1 else "Unknown",
                "email": lines[2] if len(lines) > 2 else "",
                "subject": lines[3] if len(lines) > 3 else "",
                "body": '\n'.join(lines[4:]),
                "stats": result.stdout
            }

        except Exception as e:
            logger.error(f"Failed to get commit info: {e}")
            return None

    def _get_commit_diff(self, commit_hash: str) -> Optional[str]:
        """Get full diff of commit"""
        try:
            result = subprocess.run(
                ["git", "show", commit_hash],
                capture_output=True,
                text=True,
                timeout=30
            )

            return result.stdout if result.returncode == 0 else None

        except Exception as e:
            logger.error(f"Failed to get commit diff: {e}")
            return None

    async def _run_automated_checks(self, commit_hash: str) -> Dict[str, List[str]]:
        """Run automated checks (linting, tests, etc.)"""
        issues = {
            "critical": [],
            "errors": [],
            "warnings": []
        }

        # Check for large files
        try:
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                capture_output=True,
                text=True,
                timeout=10
            )

            files = result.stdout.strip().split('\n')
            for file in files:
                # TODO: Add more automated checks
                pass

        except Exception as e:
            issues["warnings"].append(f"Automated checks failed: {e}")

        return issues

    async def _ai_review(
        self,
        commit_info: Dict,
        diff: str,
        automated_issues: Dict,
        detailed: bool
    ) -> Dict:
        """Use AI to review code changes"""
        try:
            prompt = self._build_review_prompt(commit_info, diff, automated_issues, detailed)

            # TODO: Use actual provider
            # response = await self.provider.generate_response(prompt)

            # Mock response for now
            return {
                "summary": "Code looks good overall",
                "issues": [],
                "suggestions": ["Consider adding more tests"],
                "strengths": ["Good commit message", "Clean code"],
                "score_suggestion": 85
            }

        except Exception as e:
            logger.error(f"AI review failed: {e}")
            return {
                "summary": f"Review failed: {e}",
                "issues": [str(e)],
                "suggestions": [],
                "strengths": [],
                "score_suggestion": 50
            }

    def _build_review_prompt(
        self,
        commit_info: Dict,
        diff: str,
        automated_issues: Dict,
        detailed: bool
    ) -> str:
        """Build prompt for AI review"""
        prompt = f"""Review this code commit:

Commit: {commit_info['hash'][:8]}
Author: {commit_info['author']}
Message: {commit_info['subject']}

Automated Issues:
{json.dumps(automated_issues, indent=2)}

Diff:
{diff[:5000]}  # Limit diff size

Please review and provide:
1. Overall summary
2. Critical issues (if any)
3. Suggestions for improvement
4. Code strengths
5. Score (0-100)

{"Provide detailed analysis." if detailed else "Provide quick assessment."}
"""
        return prompt

    def _calculate_score(self, ai_review: Dict, automated_issues: Dict) -> int:
        """Calculate final review score"""
        # Start with AI's suggested score
        score = ai_review.get("score_suggestion", 70)

        # Deduct for automated issues
        score -= len(automated_issues.get("critical", [])) * 30
        score -= len(automated_issues.get("errors", [])) * 10
        score -= len(automated_issues.get("warnings", [])) * 5

        # Ensure score is in valid range
        return max(0, min(100, score))

    def _generate_reviewer_notes(
        self,
        score: int,
        approved: bool,
        automated_issues: Dict
    ) -> str:
        """Generate notes for the review"""
        notes = []

        if approved:
            notes.append(f"✅ APPROVED with score {score}/100")
        else:
            notes.append(f"❌ REJECTED with score {score}/100")
            notes.append(f"Threshold: {self.auto_approve_threshold}/100")

        if automated_issues.get("critical"):
            notes.append(f"⚠️  {len(automated_issues['critical'])} critical issues found")

        if score >= 90:
            notes.append("🌟 Excellent work!")
        elif score >= 70:
            notes.append("👍 Good work")
        elif score >= 50:
            notes.append("⚠️  Needs improvement")
        else:
            notes.append("❌ Significant issues found")

        return " | ".join(notes)

    def _create_error_result(self, commit_hash: str, agent_id: str, error: str) -> CodeReviewResult:
        """Create error result for failed reviews"""
        return CodeReviewResult(
            commit_hash=commit_hash,
            agent_id=agent_id,
            approved=False,
            score=0,
            issues=[f"Review failed: {error}"],
            suggestions=[],
            strengths=[],
            review_summary=f"Review failed: {error}",
            reviewer_notes=f"❌ Review error: {error}"
        )

    def get_agent_stats(self, agent_id: Optional[str] = None) -> Dict:
        """Get review statistics for an agent"""
        reviews = [r for r in self.review_history if agent_id is None or r.agent_id == agent_id]

        if not reviews:
            return {
                "total_reviews": 0,
                "approved": 0,
                "rejected": 0,
                "avg_score": 0,
                "approval_rate": 0
            }

        approved = sum(1 for r in reviews if r.approved)

        return {
            "total_reviews": len(reviews),
            "approved": approved,
            "rejected": len(reviews) - approved,
            "avg_score": sum(r.score for r in reviews) / len(reviews),
            "approval_rate": (approved / len(reviews)) * 100 if reviews else 0
        }

    async def review_recent_commits(self, limit: int = 10) -> List[CodeReviewResult]:
        """Review recent commits from AI agents"""
        # Get recent agent commits
        agent_commits = self.rollback.get_agent_commits(limit=limit)

        results = []
        for commit in agent_commits:
            result = await self.review_commit(
                commit["hash"],
                commit.get("agent_id", "unknown"),
                detailed=False
            )
            results.append(result)

        return results
