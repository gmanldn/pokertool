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
