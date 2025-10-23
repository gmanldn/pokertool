"""
SmartHelper WebSocket Manager

Real-time WebSocket channel for SmartHelper recommendations and table state updates.
Provides pub/sub architecture for broadcasting recommendations to connected clients.

Author: PokerTool Team
Created: 2025-10-22
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    RECOMMENDATION = "recommendation"
    TABLE_STATE = "table_state"
    EQUITY_UPDATE = "equity_update"
    FACTOR_UPDATE = "factor_update"
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: str
    data: Dict[str, Any]
    timestamp: float
    session_id: Optional[str] = None

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self))


class SmartHelperConnection:
    """Represents a single WebSocket connection"""

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str,
        table_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.table_id = table_id
        self.connected_at = time.time()
        self.last_activity = time.time()
        self.subscriptions: Set[str] = set()

        # Stats
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = 0

    def is_alive(self) -> bool:
        """Check if connection is still alive"""
        return self.websocket.client_state == WebSocketState.CONNECTED

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()

    def get_connection_duration(self) -> float:
        """Get connection duration in seconds"""
        return time.time() - self.connected_at


class SmartHelperWebSocketManager:
    """
    Manages WebSocket connections for SmartHelper

    Features:
    - Multiple concurrent connections per user
    - Table-specific subscriptions
    - Message broadcasting
    - Automatic reconnection handling
    - Connection pooling
    """

    def __init__(self):
        # Connection storage
        self.active_connections: Dict[str, SmartHelperConnection] = {}
        self.user_connections: Dict[str, List[str]] = {}  # user_id -> [connection_ids]
        self.table_connections: Dict[str, List[str]] = {}  # table_id -> [connection_ids]

        # Message queue for buffering during reconnection
        self.message_queue: Dict[str, List[WebSocketMessage]] = {}
        self.max_queue_size = 100

        # Stats
        self.total_connections = 0
        self.total_messages_sent = 0
        self.total_messages_received = 0

        logger.info("SmartHelper WebSocket manager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str,
        table_id: Optional[str] = None
    ) -> SmartHelperConnection:
        """
        Accept new WebSocket connection

        Args:
            websocket: FastAPI WebSocket
            connection_id: Unique connection identifier
            user_id: User ID
            table_id: Optional table ID for filtering

        Returns:
            SmartHelperConnection instance
        """
        try:
            await websocket.accept()

            # Create connection
            connection = SmartHelperConnection(
                websocket=websocket,
                connection_id=connection_id,
                user_id=user_id,
                table_id=table_id
            )

            # Store connection
            self.active_connections[connection_id] = connection

            # Add to user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(connection_id)

            # Add to table connections
            if table_id:
                if table_id not in self.table_connections:
                    self.table_connections[table_id] = []
                self.table_connections[table_id].append(connection_id)

            # Send connection acknowledgment
            await self.send_to_connection(
                connection_id,
                MessageType.CONNECTION_ACK,
                {
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "table_id": table_id,
                    "timestamp": time.time()
                }
            )

            # Send queued messages if any
            if connection_id in self.message_queue:
                for message in self.message_queue[connection_id]:
                    await websocket.send_text(message.to_json())
                del self.message_queue[connection_id]

            self.total_connections += 1
            logger.info(f"SmartHelper WebSocket connected: {connection_id} (user: {user_id}, table: {table_id})")

            return connection

        except Exception as e:
            logger.error(f"Error accepting WebSocket connection {connection_id}: {e}")
            raise

    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup connection

        Args:
            connection_id: Connection to disconnect
        """
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return

            # Remove from user connections
            if connection.user_id in self.user_connections:
                self.user_connections[connection.user_id] = [
                    cid for cid in self.user_connections[connection.user_id]
                    if cid != connection_id
                ]
                if not self.user_connections[connection.user_id]:
                    del self.user_connections[connection.user_id]

            # Remove from table connections
            if connection.table_id and connection.table_id in self.table_connections:
                self.table_connections[connection.table_id] = [
                    cid for cid in self.table_connections[connection.table_id]
                    if cid != connection_id
                ]
                if not self.table_connections[connection.table_id]:
                    del self.table_connections[connection.table_id]

            # Remove connection
            del self.active_connections[connection_id]

            logger.info(f"SmartHelper WebSocket disconnected: {connection_id} "
                       f"(duration: {connection.get_connection_duration():.1f}s, "
                       f"messages sent: {connection.messages_sent}, "
                       f"messages received: {connection.messages_received})")

        except Exception as e:
            logger.error(f"Error disconnecting {connection_id}: {e}")

    async def send_to_connection(
        self,
        connection_id: str,
        message_type: MessageType,
        data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Send message to specific connection

        Args:
            connection_id: Target connection
            message_type: Type of message
            data: Message payload
            session_id: Optional session identifier

        Returns:
            True if sent successfully
        """
        connection = self.active_connections.get(connection_id)
        if not connection or not connection.is_alive():
            logger.warning(f"Connection {connection_id} not available for sending")

            # Queue message for reconnection
            if connection_id not in self.message_queue:
                self.message_queue[connection_id] = []

            if len(self.message_queue[connection_id]) < self.max_queue_size:
                message = WebSocketMessage(
                    type=message_type.value,
                    data=data,
                    timestamp=time.time(),
                    session_id=session_id
                )
                self.message_queue[connection_id].append(message)
                logger.debug(f"Message queued for {connection_id} (queue size: {len(self.message_queue[connection_id])})")

            return False

        try:
            message = WebSocketMessage(
                type=message_type.value,
                data=data,
                timestamp=time.time(),
                session_id=session_id
            )

            await connection.websocket.send_text(message.to_json())
            connection.messages_sent += 1
            connection.update_activity()
            self.total_messages_sent += 1

            logger.debug(f"Sent {message_type.value} to {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            connection.errors += 1
            await self.disconnect(connection_id)
            return False

    async def broadcast_to_user(
        self,
        user_id: str,
        message_type: MessageType,
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast message to all user's connections

        Args:
            user_id: Target user
            message_type: Type of message
            data: Message payload

        Returns:
            Number of connections message was sent to
        """
        connection_ids = self.user_connections.get(user_id, [])
        sent_count = 0

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message_type, data):
                sent_count += 1

        logger.debug(f"Broadcast {message_type.value} to user {user_id} ({sent_count}/{len(connection_ids)} connections)")
        return sent_count

    async def broadcast_to_table(
        self,
        table_id: str,
        message_type: MessageType,
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast message to all table connections

        Args:
            table_id: Target table
            message_type: Type of message
            data: Message payload

        Returns:
            Number of connections message was sent to
        """
        connection_ids = self.table_connections.get(table_id, [])
        sent_count = 0

        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, message_type, data):
                sent_count += 1

        logger.debug(f"Broadcast {message_type.value} to table {table_id} ({sent_count}/{len(connection_ids)} connections)")
        return sent_count

    async def broadcast_recommendation(
        self,
        table_id: str,
        recommendation: Dict[str, Any]
    ) -> int:
        """
        Broadcast recommendation update to table

        Args:
            table_id: Table to broadcast to
            recommendation: Recommendation data

        Returns:
            Number of connections reached
        """
        return await self.broadcast_to_table(
            table_id,
            MessageType.RECOMMENDATION,
            recommendation
        )

    async def handle_ping(self, connection_id: str):
        """
        Respond to ping with pong

        Args:
            connection_id: Connection that sent ping
        """
        await self.send_to_connection(
            connection_id,
            MessageType.PONG,
            {"timestamp": time.time()}
        )

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get WebSocket manager statistics

        Returns:
            Dictionary with connection stats
        """
        active_count = len(self.active_connections)
        user_count = len(self.user_connections)
        table_count = len(self.table_connections)

        return {
            "active_connections": active_count,
            "unique_users": user_count,
            "active_tables": table_count,
            "total_connections_lifetime": self.total_connections,
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received,
            "queued_messages": sum(len(q) for q in self.message_queue.values())
        }

    async def cleanup_stale_connections(self, timeout_seconds: int = 300):
        """
        Remove connections that haven't been active for timeout period

        Args:
            timeout_seconds: Inactivity timeout
        """
        current_time = time.time()
        stale_connections = []

        for connection_id, connection in self.active_connections.items():
            if current_time - connection.last_activity > timeout_seconds:
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            logger.warning(f"Removing stale connection: {connection_id}")
            await self.disconnect(connection_id)

        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")


# Global WebSocket manager instance
_ws_manager: Optional[SmartHelperWebSocketManager] = None


def get_ws_manager() -> SmartHelperWebSocketManager:
    """Get or create global WebSocket manager"""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = SmartHelperWebSocketManager()
    return _ws_manager
