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

    async def planning_phase(self, task: Task) -> Optional[str]:
        """Generate execution plan"""
        self.set_phase(AgentPhase.PLANNING, f"Planning: {task.title}")

        try:
            # TODO: Use AI provider to generate plan
            plan = f"Plan for {task.title}"
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


class AIAgentManager:
    """Manages multiple AI agents working in parallel"""

    def __init__(self, todo_path: str = "docs/TODO.md"):
        self.todo_path = todo_path
        self.agents: Dict[str, AIAgent] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

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
