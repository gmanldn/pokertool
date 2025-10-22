"""AI Agent Manager - Core orchestration engine for managing 3 parallel AI agents"""
import asyncio
import logging
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import subprocess
import sys

from pokertool.todo_parser import TodoParser, Task, Priority
from pokertool.todo_updater import TodoUpdater
from pokertool.improve_rollback import RollbackManager
from pokertool.rate_limiter import RateLimiter
from pokertool.error_recovery import ErrorRecoveryManager
from pokertool.ai_providers.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class TaskStrategy(str, Enum):
    """Task selection strategies"""
    TOP = "top"  # Top 20 tasks from start of TODO.md
    BOTTOM = "bottom"  # Bottom 20 tasks from end of TODO.md
    RANDOM = "random"  # Random 20 tasks weighted by priority


class AgentPhase(str, Enum):
    """Agent execution phases"""
    IDLE = "idle"
    LOADING_TASKS = "loading_tasks"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    COMMITTING = "committing"
    DOCUMENTING = "documenting"
    DONE = "done"
    ERROR = "error"
    PAUSED = "paused"


@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    agent_id: str
    provider: BaseAIProvider
    strategy: TaskStrategy
    num_tasks: int = 20
    require_tests: bool = True
    require_approval: bool = False
    auto_commit: bool = True
    fallback_providers: List[BaseAIProvider] = None  # Fallback chain if primary fails

    def __post_init__(self):
        if self.fallback_providers is None:
            self.fallback_providers = []


class AIAgent:
    """Single AI agent instance"""

    def __init__(self, config: AgentConfig, todo_path: str = "docs/TODO.md"):
        self.config = config
        self.todo_path = todo_path
        self.parser = TodoParser(todo_path)
        self.updater = TodoUpdater(todo_path)
        self.rollback = RollbackManager()
        self.rate_limiter = RateLimiter()
        self.error_recovery = ErrorRecoveryManager()

        self.phase = AgentPhase.IDLE
        self.current_task: Optional[Task] = None
        self.tasks_queue: List[Task] = []
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []

        # Callbacks for status updates
        self.on_phase_change: Optional[Callable[[str, AgentPhase], None]] = None
        self.on_output: Optional[Callable[[str, str], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None

    def set_phase(self, phase: AgentPhase, info: Optional[str] = None):
        """Update agent phase and notify listeners"""
        self.phase = phase
        logger.info(f"Agent {self.config.agent_id} -> {phase.value}")
        if self.on_phase_change:
            self.on_phase_change(self.config.agent_id, phase)
        if info and self.on_output:
            self.on_output(self.config.agent_id, info)

    def output(self, message: str):
        """Send output to terminal"""
        if self.on_output:
            self.on_output(self.config.agent_id, message)
        logger.info(f"[{self.config.agent_id}] {message}")

    def error(self, message: str):
        """Send error message"""
        if self.on_error:
            self.on_error(self.config.agent_id, message)
        logger.error(f"[{self.config.agent_id}] ERROR: {message}")

    async def load_tasks(self) -> bool:
        """Load tasks based on strategy"""
        try:
            self.set_phase(AgentPhase.LOADING_TASKS, "Loading tasks from TODO.md...")

            if self.config.strategy == TaskStrategy.TOP:
                self.tasks_queue = self.parser.get_top_n_tasks(self.config.num_tasks)
            elif self.config.strategy == TaskStrategy.BOTTOM:
                self.tasks_queue = self.parser.get_bottom_n_tasks(self.config.num_tasks)
            else:  # RANDOM
                self.tasks_queue = self.parser.get_random_n_tasks(self.config.num_tasks, weighted=True)

            self.output(f"Loaded {len(self.tasks_queue)} tasks using {self.config.strategy.value} strategy")
            for i, task in enumerate(self.tasks_queue[:5], 1):
                self.output(f"  {i}. [{task.priority.value}][{task.effort.value}] {task.title}")
            if len(self.tasks_queue) > 5:
                self.output(f"  ... and {len(self.tasks_queue) - 5} more tasks")

            return True

        except Exception as e:
            self.error(f"Failed to load tasks: {e}")
            self.set_phase(AgentPhase.ERROR)
            return False

    async def run(self):
        """Main execution loop"""
        try:
            # Load tasks
            if not await self.load_tasks():
                return

            # Process each task
            for task in self.tasks_queue:
                if self.phase == AgentPhase.PAUSED:
                    self.output("Agent paused, waiting...")
                    while self.phase == AgentPhase.PAUSED:
                        await asyncio.sleep(1)

                if self.phase == AgentPhase.ERROR:
                    break

                self.current_task = task
                success = await self.process_task(task)

                if success:
                    self.completed_tasks.append(task)
                else:
                    self.failed_tasks.append(task)

            # Done
            self.set_phase(AgentPhase.DONE,
                          f"Completed {len(self.completed_tasks)}/{len(self.tasks_queue)} tasks")

        except Exception as e:
            self.error(f"Agent execution failed: {e}")
            self.set_phase(AgentPhase.ERROR)

    async def process_task(self, task: Task) -> bool:
        """Process a single task through all phases"""
        try:
            self.output(f"\n{'='*60}")
            self.output(f"Task: [{task.priority.value}][{task.effort.value}] {task.title}")
            self.output(f"Description: {task.description or 'N/A'}")
            self.output(f"{'='*60}\n")

            # Mark as in progress
            self.updater.mark_task_in_progress(task, self.config.agent_id)

            # Planning phase
            plan = await self.planning_phase(task)
            if not plan:
                return False

            # Execution phase
            if not await self.execution_phase(task, plan):
                return False

            # Testing phase
            if self.config.require_tests and not await self.testing_phase(task):
                return False

            # Commit phase
            if self.config.auto_commit and not await self.commit_phase(task):
                return False

            # Documentation phase
            if not await self.documentation_phase(task):
                return False

            # Mark complete
            self.updater.mark_task_complete(task,
                completion_note=f"Completed by {self.config.agent_id}")

            self.output(f"✅ Task completed successfully\n")
            return True

        except Exception as e:
            self.error(f"Task processing failed: {e}")
            return False

    async def _try_with_fallback(self, operation_name: str, operation_func):
        """Try operation with primary provider, fallback to alternatives if it fails"""
        providers_to_try = [self.config.provider] + self.config.fallback_providers

        last_error = None
        for i, provider in enumerate(providers_to_try):
            try:
                is_fallback = i > 0
                if is_fallback:
                    self.output(f"⚠️  Trying fallback provider {i}: {provider.__class__.__name__}")

                result = await operation_func(provider)

                if is_fallback:
                    self.output(f"✅ Fallback provider succeeded")

                return result

            except Exception as e:
                last_error = e
                self.error(f"{operation_name} failed with {provider.__class__.__name__}: {e}")
                if i < len(providers_to_try) - 1:
                    self.output(f"Attempting fallback...")
                continue

        # All providers failed
        raise Exception(f"{operation_name} failed with all providers. Last error: {last_error}")

    async def planning_phase(self, task: Task) -> Optional[str]:
        """Generate execution plan with provider fallback"""
        self.set_phase(AgentPhase.PLANNING, f"Planning: {task.title}")

        try:
            async def plan_with_provider(provider):
                plan = f"Plan for {task.title}"
                # TODO: Use provider to generate actual plan
                return plan

            plan = await self._try_with_fallback("Planning", plan_with_provider)
            self.output(f"📋 Plan created:\n{plan}")
            return plan
        except Exception as e:
            self.error(f"Planning failed: {e}")
            return None

    async def execution_phase(self, task: Task, plan: str) -> bool:
        """Execute the plan"""
        self.set_phase(AgentPhase.EXECUTING, f"Executing: {task.title}")

        try:
            # TODO: Execute plan using AI provider
            self.output(f"⚙️  Executing plan...")
            await asyncio.sleep(1)  # Placeholder
            return True
        except Exception as e:
            self.error(f"Execution failed: {e}")
            return False

    async def testing_phase(self, task: Task) -> bool:
        """Run tests"""
        self.set_phase(AgentPhase.TESTING, f"Testing: {task.title}")

        try:
            self.output(f"🧪 Running tests...")
            # TODO: Run actual tests
            return True
        except Exception as e:
            self.error(f"Testing failed: {e}")
            return False

    async def commit_phase(self, task: Task) -> bool:
        """Create git commit"""
        self.set_phase(AgentPhase.COMMITTING, f"Committing: {task.title}")

        try:
            # Create snapshot before commit
            snapshot = self.rollback.create_snapshot(f"Before {task.title}")
            self.output(f"📸 Created snapshot: {snapshot}")

            # TODO: Create commit with proper message
            self.output(f"💾 Creating commit...")

            return True
        except Exception as e:
            self.error(f"Commit failed: {e}")
            return False

    async def documentation_phase(self, task: Task) -> bool:
        """Update documentation"""
        self.set_phase(AgentPhase.DOCUMENTING, f"Documenting: {task.title}")

        try:
            # TODO: Update docs if needed
            return True
        except Exception as e:
            self.error(f"Documentation failed: {e}")
            return False


class CodeReviewAgent:
    """
    Specialized 4th agent that reviews commits from other agents.

    Reviews commits for:
    - Code quality and best practices
    - Test coverage
    - Documentation completeness
    - Security issues
    - Breaking changes
    """

    def __init__(self, provider: BaseAIProvider, agent_id: str = "code-reviewer"):
        self.provider = provider
        self.agent_id = agent_id
        self.reviews_performed = 0
        self.issues_found = []

        # Callbacks
        self.on_review_complete: Optional[Callable[[Dict], None]] = None
        self.on_output: Optional[Callable[[str, str], None]] = None

    def output(self, message: str):
        """Send output message"""
        if self.on_output:
            self.on_output(self.agent_id, message)
        logger.info(f"[{self.agent_id}] {message}")

    async def review_commit(self, commit_hash: str) -> Dict[str, any]:
        """
        Review a single commit

        Args:
            commit_hash: Git commit hash to review

        Returns:
            Dict with review results:
            {
                "approved": bool,
                "issues": List[str],
                "suggestions": List[str],
                "score": float (0-100)
            }
        """
        try:
            self.output(f"🔍 Reviewing commit {commit_hash[:8]}...")

            # Get commit diff
            diff = await self._get_commit_diff(commit_hash)

            # Get commit message
            commit_msg = await self._get_commit_message(commit_hash)

            # Get changed files
            changed_files = await self._get_changed_files(commit_hash)

            # Build review prompt
            prompt = self._build_review_prompt(commit_hash, commit_msg, diff, changed_files)

            # Get AI review
            review_text = await self.provider.generate_response(prompt)

            # Parse review
            review = self._parse_review(review_text)

            # Update stats
            self.reviews_performed += 1
            if not review["approved"]:
                self.issues_found.extend(review["issues"])

            # Notify
            if self.on_review_complete:
                self.on_review_complete(review)

            # Output summary
            status_emoji = "✅" if review["approved"] else "⚠️ "
            self.output(f"{status_emoji} Review complete: Score {review['score']}/100")
            if review["issues"]:
                self.output(f"  Issues found: {len(review['issues'])}")
                for issue in review["issues"][:3]:
                    self.output(f"    - {issue}")
                if len(review["issues"]) > 3:
                    self.output(f"    ... and {len(review['issues']) - 3} more")

            return review

        except Exception as e:
            logger.error(f"Code review failed: {e}")
            return {
                "approved": False,
                "issues": [f"Review failed: {str(e)}"],
                "suggestions": [],
                "score": 0
            }

    async def _get_commit_diff(self, commit_hash: str) -> str:
        """Get full diff for commit"""
        proc = await asyncio.create_subprocess_exec(
            "git", "show", commit_hash,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()

    async def _get_commit_message(self, commit_hash: str) -> str:
        """Get commit message"""
        proc = await asyncio.create_subprocess_exec(
            "git", "log", "-1", "--format=%B", commit_hash,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode().strip()

    async def _get_changed_files(self, commit_hash: str) -> List[str]:
        """Get list of changed files"""
        proc = await asyncio.create_subprocess_exec(
            "git", "show", "--name-only", "--format=", commit_hash,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return [f.strip() for f in stdout.decode().split('\n') if f.strip()]

    def _build_review_prompt(self, commit_hash: str, commit_msg: str, diff: str, files: List[str]) -> str:
        """Build comprehensive review prompt"""
        return f"""Please review this git commit for code quality, best practices, and potential issues.

**Commit Hash:** {commit_hash}

**Commit Message:**
{commit_msg}

**Files Changed ({len(files)}):**
{chr(10).join(f'- {f}' for f in files)}

**Diff:**
```diff
{diff[:5000]}  # Limit diff size
```

Please provide a detailed review covering:

1. **Code Quality** (0-25 points)
   - Readability and maintainability
   - Follows project conventions
   - Appropriate abstractions

2. **Functionality** (0-25 points)
   - Implementation correctness
   - Edge case handling
   - Error handling

3. **Testing** (0-25 points)
   - Test coverage
   - Test quality
   - Tests for edge cases

4. **Documentation** (0-25 points)
   - Code comments
   - Docstrings
   - Updated docs

**Please respond in this exact format:**

SCORE: [0-100]
APPROVED: [YES/NO]

ISSUES:
- [Issue 1]
- [Issue 2]

SUGGESTIONS:
- [Suggestion 1]
- [Suggestion 2]

SUMMARY:
[2-3 sentence summary]
"""

    def _parse_review(self, review_text: str) -> Dict:
        """Parse AI review response"""
        lines = review_text.strip().split('\n')

        score = 85  # Default score
        approved = True
        issues = []
        suggestions = []
        summary = ""

        current_section = None
        for line in lines:
            line = line.strip()

            if line.startswith("SCORE:"):
                try:
                    score = float(line.split(":")[-1].strip())
                except:
                    pass
            elif line.startswith("APPROVED:"):
                approved = "YES" in line.upper()
            elif line.startswith("ISSUES:"):
                current_section = "issues"
            elif line.startswith("SUGGESTIONS:"):
                current_section = "suggestions"
            elif line.startswith("SUMMARY:"):
                current_section = "summary"
            elif line.startswith("- ") and current_section:
                item = line[2:].strip()
                if current_section == "issues":
                    issues.append(item)
                elif current_section == "suggestions":
                    suggestions.append(item)
            elif current_section == "summary" and line:
                summary += line + " "

        # Auto-fail if score is too low
        if score < 70:
            approved = False

        return {
            "approved": approved,
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "summary": summary.strip()
        }

    async def review_agent_commits(self, agent_id: str, commit_hashes: List[str]) -> Dict:
        """
        Review all commits from a specific agent

        Returns:
            {
                "agent_id": str,
                "total_commits": int,
                "approved_commits": int,
                "rejected_commits": int,
                "average_score": float,
                "all_reviews": List[Dict]
            }
        """
        self.output(f"📊 Reviewing {len(commit_hashes)} commits from {agent_id}...")

        reviews = []
        for commit_hash in commit_hashes:
            review = await self.review_commit(commit_hash)
            reviews.append(review)
            await asyncio.sleep(0.5)  # Rate limiting

        approved_count = sum(1 for r in reviews if r["approved"])
        avg_score = sum(r["score"] for r in reviews) / len(reviews) if reviews else 0

        summary = {
            "agent_id": agent_id,
            "total_commits": len(commit_hashes),
            "approved_commits": approved_count,
            "rejected_commits": len(commit_hashes) - approved_count,
            "average_score": avg_score,
            "all_reviews": reviews
        }

        self.output(f"✨ Agent review complete: {approved_count}/{len(commit_hashes)} approved, avg score: {avg_score:.1f}/100")

        return summary


class AIAgentManager:
    """Manages multiple AI agents working in parallel"""

    def __init__(self, todo_path: str = "docs/TODO.md"):
        self.todo_path = todo_path
        self.agents: Dict[str, AIAgent] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.code_reviewer: Optional[CodeReviewAgent] = None

    def create_agent(self, config: AgentConfig) -> AIAgent:
        """Create and register a new agent"""
        agent = AIAgent(config, self.todo_path)
        self.agents[config.agent_id] = agent
        return agent

    async def start_agent(self, agent_id: str):
        """Start an agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self.agents[agent_id]
        task = asyncio.create_task(agent.run())
        self.tasks[agent_id] = task

    async def stop_agent(self, agent_id: str):
        """Stop an agent"""
        if agent_id in self.tasks:
            self.tasks[agent_id].cancel()
            try:
                await self.tasks[agent_id]
            except asyncio.CancelledError:
                pass
            del self.tasks[agent_id]

        if agent_id in self.agents:
            self.agents[agent_id].set_phase(AgentPhase.IDLE)

    async def pause_agent(self, agent_id: str):
        """Pause an agent"""
        if agent_id in self.agents:
            self.agents[agent_id].set_phase(AgentPhase.PAUSED)

    async def resume_agent(self, agent_id: str):
        """Resume a paused agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            if agent.current_task:
                agent.set_phase(AgentPhase.EXECUTING)
            else:
                agent.set_phase(AgentPhase.LOADING_TASKS)

    async def stop_all(self):
        """Stop all agents"""
        for agent_id in list(self.agents.keys()):
            await self.stop_agent(agent_id)

    def enable_code_review(self, provider: BaseAIProvider):
        """
        Enable code review agent

        Args:
            provider: AI provider to use for code reviews
        """
        self.code_reviewer = CodeReviewAgent(provider)
        logger.info("Code review agent enabled")

    async def review_recent_commits(self, agent_id: str, num_commits: int = 5) -> Optional[Dict]:
        """
        Review recent commits from an agent

        Args:
            agent_id: ID of agent whose commits to review
            num_commits: Number of recent commits to review

        Returns:
            Review summary dict or None if code reviewer not enabled
        """
        if not self.code_reviewer:
            logger.warning("Code reviewer not enabled. Call enable_code_review() first.")
            return None

        # Get recent commit hashes for this agent
        # Look for commits with the agent ID in the commit message
        proc = await asyncio.create_subprocess_exec(
            "git", "log", f"-{num_commits * 3}",  # Get extra to filter
            "--format=%H|||%s",  # Hash and subject
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()

        # Filter commits by agent ID
        agent_commits = []
        for line in stdout.decode().split('\n'):
            if '|||' in line:
                commit_hash, subject = line.split('|||', 1)
                if agent_id.lower() in subject.lower():
                    agent_commits.append(commit_hash.strip())
                    if len(agent_commits) >= num_commits:
                        break

        if not agent_commits:
            logger.warning(f"No commits found for agent {agent_id}")
            return None

        # Review the commits
        return await self.code_reviewer.review_agent_commits(agent_id, agent_commits)
