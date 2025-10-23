"""Improve Tab API - WebSocket endpoints for AI agent terminals"""
import asyncio
import json
import logging
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
import sys
import os

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/improve", tags=["improve"])

# Track active WebSocket connections per agent
active_connections: Dict[str, WebSocket] = {}

# Track agent processes
agent_processes: Dict[str, asyncio.subprocess.Process] = {}


class TerminalConnectionManager:
    """Manages WebSocket connections for agent terminals"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, agent_id: str, websocket: WebSocket):
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        logger.info(f"Agent {agent_id} terminal connected")

    def disconnect(self, agent_id: str):
        """Unregister WebSocket connection"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            logger.info(f"Agent {agent_id} terminal disconnected")

    async def send_output(self, agent_id: str, message: str):
        """Send terminal output to frontend"""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_text(
                    json.dumps({"type": "output", "data": message})
                )
            except Exception as e:
                logger.error(f"Error sending to {agent_id}: {e}")

    async def send_status(self, agent_id: str, status: str, info: Optional[str] = None):
        """Send status update to frontend"""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_text(
                    json.dumps({"type": "status", "status": status, "info": info})
                )
            except Exception as e:
                logger.error(f"Error sending status to {agent_id}: {e}")

    async def send_error(self, agent_id: str, error: str):
        """Send error message to frontend"""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_text(
                    json.dumps({"type": "error", "error": error})
                )
            except Exception as e:
                logger.error(f"Error sending error to {agent_id}: {e}")


# Global connection manager
terminal_manager = TerminalConnectionManager()


@router.websocket("/ws/terminal/{agent_id}")
async def terminal_websocket(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for bidirectional terminal communication

    Messages from frontend:
    - {"type": "input", "data": "command"} - User input
    - {"type": "resize", "cols": 80, "rows": 24} - Terminal resize

    Messages to frontend:
    - {"type": "output", "data": "text"} - Terminal output
    - {"type": "status", "status": "working", "info": "..."} - Status update
    - {"type": "error", "error": "message"} - Error message
    """
    await terminal_manager.connect(agent_id, websocket)

    try:
        while True:
            # Receive messages from frontend
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "input":
                # Handle user input (for interactive commands)
                logger.info(f"Agent {agent_id} received input: {message['data']}")
                # TODO: Send input to agent process stdin

            elif message["type"] == "resize":
                # Handle terminal resize
                logger.info(f"Agent {agent_id} terminal resized: {message['cols']}x{message['rows']}")
                # TODO: Resize PTY if using one

    except WebSocketDisconnect:
        terminal_manager.disconnect(agent_id)
        logger.info(f"Agent {agent_id} WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        terminal_manager.disconnect(agent_id)


@router.post("/agent/{agent_id}/start")
async def start_agent(agent_id: str, provider: str = "claude-code", strategy: str = "top"):
    """
    Start an AI agent

    Parameters:
    - agent_id: Agent identifier (agent1, agent2, agent3)
    - provider: AI provider (claude-code, anthropic, openrouter, openai)
    - strategy: Task selection strategy (top, bottom, random)
    """
    try:
        # Send initial status
        await terminal_manager.send_status(agent_id, "loading_tasks", f"Starting {provider} agent with {strategy} strategy")

        # TODO: Start actual agent process
        await terminal_manager.send_output(agent_id, f"\n🚀 Agent {agent_id} starting...\n")
        await terminal_manager.send_output(agent_id, f"Provider: {provider}\n")
        await terminal_manager.send_output(agent_id, f"Strategy: {strategy}\n")

        return JSONResponse({"status": "started", "agent_id": agent_id})

    except Exception as e:
        logger.error(f"Error starting agent {agent_id}: {e}")
        await terminal_manager.send_error(agent_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop an AI agent"""
    try:
        # TODO: Terminate agent process
        await terminal_manager.send_output(agent_id, f"\n🛑 Agent {agent_id} stopped\n")
        await terminal_manager.send_status(agent_id, "idle")

        return JSONResponse({"status": "stopped", "agent_id": agent_id})

    except Exception as e:
        logger.error(f"Error stopping agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/{agent_id}/pause")
async def pause_agent(agent_id: str):
    """Pause an AI agent"""
    try:
        # TODO: Send pause signal to agent process
        await terminal_manager.send_output(agent_id, f"\n⏸️  Agent {agent_id} paused\n")
        await terminal_manager.send_status(agent_id, "paused")

        return JSONResponse({"status": "paused", "agent_id": agent_id})

    except Exception as e:
        logger.error(f"Error pausing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/{agent_id}/resume")
async def resume_agent(agent_id: str):
    """Resume a paused agent"""
    try:
        # TODO: Send resume signal to agent process
        await terminal_manager.send_output(agent_id, f"\n▶️  Agent {agent_id} resumed\n")
        await terminal_manager.send_status(agent_id, "working")

        return JSONResponse({"status": "resumed", "agent_id": agent_id})

    except Exception as e:
        logger.error(f"Error resuming agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/stop-all")
async def stop_all_agents():
    """Emergency stop all agents"""
    try:
        for agent_id in ["agent1", "agent2", "agent3"]:
            try:
                await stop_agent(agent_id)
            except:
                pass

        return JSONResponse({"status": "all_stopped"})

    except Exception as e:
        logger.error(f"Error stopping all agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-tasks")
async def add_tasks_to_todo(tasks: list):
    """
    Add tasks to TODO.md file

    Request body:
    {
        "tasks": [
            {
                "description": "Task description",
                "priority": "P0",
                "size": "M",
                "file": "path/to/file.py" (optional)
            }
        ]
    }
    """
    try:
        # Get the repo root directory (3 levels up from src/pokertool)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.join(current_dir, "..", "..")
        todo_path = os.path.join(repo_root, "docs", "TODO.md")

        # Read existing TODO.md
        if os.path.exists(todo_path):
            with open(todo_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "# TODO\n\n## Improve Tab Tasks\n\n"

        # Prepare new tasks
        new_tasks_lines = []
        for task in tasks:
            description = task.get('description', '')
            priority = task.get('priority', 'P2')
            size = task.get('size', 'M')
            file_path = task.get('file', '')

            if file_path:
                task_line = f"- [ ] [{priority}][{size}] {description} — `{file_path}`"
            else:
                task_line = f"- [ ] [{priority}][{size}] {description}"

            new_tasks_lines.append(task_line)

        # Find a good place to insert tasks (after the first heading)
        lines = content.split('\n')
        insert_index = 0

        # Find first heading and insert after it
        for i, line in enumerate(lines):
            if line.startswith('# '):
                insert_index = i + 1
                break

        # Add blank line if needed
        if insert_index < len(lines) and lines[insert_index].strip():
            lines.insert(insert_index, '')
            insert_index += 1

        # Insert new tasks
        for task_line in new_tasks_lines:
            lines.insert(insert_index, task_line)
            insert_index += 1

        # Write back to TODO.md
        with open(todo_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        logger.info(f"Added {len(tasks)} task(s) to TODO.md")

        return JSONResponse({
            "status": "success",
            "tasks_added": len(tasks),
            "message": f"Successfully added {len(tasks)} task(s) to TODO.md"
        })

    except Exception as e:
        logger.error(f"Error adding tasks to TODO.md: {e}")
        raise HTTPException(status_code=500, detail=str(e))
