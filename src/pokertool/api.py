#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool RESTful API Module
=============================

This module provides a comprehensive RESTful API for external integration
with the PokerTool application. It includes endpoints for hand analysis,
database operations, real-time updates via WebSocket, and secure authentication.

Module: pokertool.api
Version: 20.0.0
Last Modified: 2025-09-29
Author: PokerTool Development Team
License: MIT

Dependencies:
    - FastAPI >= 0.104.0: Web framework for building APIs
    - Uvicorn >= 0.24.0: ASGI server implementation
    - PyJWT >= 2.8.0: JWT token handling
    - Redis >= 5.0.0: Caching and session management
    - SlowAPI >= 0.1.9: Rate limiting middleware
    - Pydantic >= 2.5.0: Data validation
    - BCrypt: Password hashing

API Endpoints:
    - POST /analyze: Analyze poker hand
    - GET /health: Health check endpoint
    - POST /auth/login: User authentication
    - POST /auth/refresh: Token refresh
    - WS /ws: WebSocket for real-time updates

Security Features:
    - JWT-based authentication
    - Rate limiting per IP/user
    - Input validation and sanitization
    - CORS configuration
    - Circuit breaker pattern

Change Log:
    - v28.0.0 (2025-09-29): Enhanced documentation, improved security
    - v19.0.0 (2025-09-18): Fixed JWT import issue
    - v18.0.0 (2025-09-15): Initial API implementation
"""

__version__ = '20.0.0'
__author__ = 'PokerTool Development Team'
__copyright__ = 'Copyright (c) 2025 PokerTool'
__license__ = 'MIT'
__maintainer__ = 'George Ridout'
__status__ = 'Production'

import os
import json
import time
import hashlib
import secrets
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from functools import wraps

# Try to import FastAPI dependencies
try:
    from fastapi import FastAPI, HTTPException, Depends, Security, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.websockets import WebSocketState
    from pydantic import BaseModel, Field, validator
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    import redis.asyncio as redis
    import jwt
    import bcrypt
    FASTAPI_AVAILABLE = True
except ImportError:
    FastAPI = None
    HTTPException = None
    Depends = None
    Security = None
    WebSocket = None
    WebSocketDisconnect = None
    BackgroundTasks = None
    CORSMiddleware = None
    TrustedHostMiddleware = None
    JSONResponse = None
    WebSocketState = None
    BaseModel = None
    Field = None
    HTTPBearer = None
    HTTPAuthorizationCredentials = None
    OAuth2PasswordBearer = None
    OAuth2PasswordRequestForm = None
    Limiter = None
    SlowAPIMiddleware = None
    redis = None
    jwt = None
    bcrypt = None
    FASTAPI_AVAILABLE = False

# Try to import Sentry for error tracking
try:
    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    sentry_sdk = None
    SentryAsgiMiddleware = None
    FastApiIntegration = None
    SENTRY_AVAILABLE = False

from .production_database import get_production_db
from .scrape import get_scraper_status, run_screen_scraper, stop_screen_scraper
from .thread_utils import get_thread_pool, TaskPriority
from .error_handling import SecurityError, retry_on_failure

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from .analytics_dashboard import AnalyticsDashboard, UsageEvent, PrivacySettings
    from .gamification import GamificationEngine, Achievement, Badge, ProgressState
    from .community_features import CommunityPlatform, ForumPost, Challenge, CommunityTournament, KnowledgeArticle

# Optional HUD overlay - not yet implemented
try:
    from .hud_overlay import start_hud_overlay, stop_hud_overlay, update_hud_state, is_hud_running
except ImportError:
    # Define dummy functions if HUD overlay not available
    def start_hud_overlay(*args, **kwargs):
        pass
    def stop_hud_overlay(*args, **kwargs):
        pass
    def update_hud_state(*args, **kwargs):
        pass
    def is_hud_running():
        return False

logger = logging.getLogger(__name__)

# Configuration
API_SECRET_KEY = secrets.token_urlsafe(32)
REDIS_URL = 'redis://localhost:6379'
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RATE_LIMIT_STORAGE_URL = REDIS_URL

class UserRole(Enum):
    """User roles for API access."""
    GUEST = 'guest'
    USER = 'user'
    PREMIUM = 'premium'
    ADMIN = 'admin'

# Pydantic models for API
if FASTAPI_AVAILABLE:
    class HandAnalysisRequest(BaseModel):
        """Request model for hand analysis."""
        hand: str = Field(..., description="Hole cards (e.g., 'AsKh')", max_length=10)
        board: Optional[str] = Field(None, description="Community cards (e.g., 'AdKcQh')", max_length=20)
        position: Optional[str] = Field(None, description='Player position', max_length=10)
        pot_size: Optional[float] = Field(None, description='Current pot size', ge=0)
        to_call: Optional[float] = Field(None, description='Amount to call', ge=0)
        num_players: Optional[int] = Field(None, description='Number of active players', ge=2, le=10)

        @validator('hand')
        def validate_hand(cls, v):
            """Validate hand format."""
            import re
            if not re.match(r'^[AKQJT2-9][shdc][AKQJT2-9][shdc]$', v):
                raise ValueError('Invalid hand format')
            return v

        @validator('board')
        def validate_board(cls, v):
            """Validate board format."""
            if v is None:
                return v
            import re
            if not re.match(r'^([AKQJT2-9][shdc] ){2,4}[AKQJT2-9][shdc]$', v):
                raise ValueError('Invalid board format')
            return v

    class HandAnalysisResponse(BaseModel):
        """Response model for hand analysis."""
        hand: str
        board: Optional[str]
        analysis: str
        equity: Optional[float] = None
        recommendation: Optional[str] = None
        metadata: Dict[str, Any] = Field(default_factory=dict)
        timestamp: datetime = Field(default_factory=datetime.utcnow)

    class RUMMetricPayload(BaseModel):
        """Payload describing a single frontend performance metric."""

        metric: str = Field(..., description="Metric identifier (e.g., LCP, CLS).", max_length=32)
        value: float = Field(..., ge=0.0, description="Measured value in milliseconds or unit-specific scale.")
        delta: Optional[float] = Field(None, description="Delta from previous value in milliseconds.")
        rating: Optional[str] = Field(
            None,
            description="Web Vitals rating (good / needs-improvement / poor).",
            max_length=32,
        )
        session_id: Optional[str] = Field(None, max_length=64)
        navigation_type: Optional[str] = Field(None, max_length=32)
        page: Optional[str] = Field(None, max_length=256)
        client_timestamp: Optional[str] = Field(None, max_length=64)
        app_version: Optional[str] = Field(None, max_length=32)
        environment: Dict[str, Any] = Field(default_factory=dict)
        attribution: Dict[str, Any] = Field(default_factory=dict)
        trace_id: Optional[str] = Field(None, max_length=64)
        span_id: Optional[str] = Field(None, max_length=64)

        def to_store_record(self, *, user_agent: Optional[str], client_ip: Optional[str], correlation_id: Optional[str]) -> Dict[str, Any]:
            record = self.dict()
            record["user_agent"] = user_agent
            record["client_ip"] = client_ip
            if correlation_id and not record.get("trace_id"):
                record["trace_id"] = correlation_id
            return record

    class UserCreate(BaseModel):
        """User creation model."""
        username: str = Field(..., min_length=3, max_length=50)
        email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
        password: str = Field(..., min_length=8)
        role: UserRole = UserRole.USER

    class Token(BaseModel):
        """Token response model."""
        access_token: str
        token_type: str
        expires_in: int
        user_role: UserRole

    class ScraperStatus(BaseModel):
        """Screen scraper status model."""
        initialized: bool
        running: bool
        available: bool
        last_state: Optional[Dict[str, Any]] = None

    class DatabaseStats(BaseModel):
        """Database statistics model."""
        database_type: str
        total_hands: int
        unique_users: int
        recent_activity: Dict[str, Any] = Field(default_factory=dict)

    class AnalyticsEventRequest(BaseModel):
        event_id: str
        action: str
        user_id: Optional[str] = None
        metadata: Dict[str, str] = Field(default_factory=dict)

    class AnalyticsSessionRequest(BaseModel):
        user_id: Optional[str] = None
        minutes: float = Field(..., ge=0)

    class GamificationActivityRequest(BaseModel):
        player_id: str
        metrics: Dict[str, int] = Field(default_factory=dict)

    class GamificationBadgeRequest(BaseModel):
        player_id: str
        badge_id: str

    class CommunityPostRequest(BaseModel):
        title: str
        content: str
        tags: List[str] = Field(default_factory=list)

    class CommunityReplyRequest(BaseModel):
        message: str

    class ChallengeParticipationRequest(BaseModel):
        challenge_id: str

    class FrontendErrorPayload(BaseModel):
        """Payload for frontend error logging to trouble feed"""
        error_type: str = Field(..., description="Type of error (e.g., TypeError, ReferenceError)")
        error_message: str = Field(..., description="Error message")
        stack_trace: str = Field(default="", description="Full stack trace if available")
        component: str = Field(..., description="React component or module where error occurred")
        severity: str = Field(default="ERROR", description="Severity level: WARNING, ERROR, or CRITICAL")
        context: Dict[str, Any] = Field(default_factory=dict, description="Additional context (props, state, etc.)")
        url: Optional[str] = Field(default=None, description="URL where error occurred")
        user_agent: Optional[str] = Field(default=None, description="Browser user agent")

else:
    # Fallback classes when FastAPI is not available
    class BaseModel:
        """Fallback base model."""
        pass

    HandAnalysisRequest = dict
    HandAnalysisResponse = dict
    UserCreate = dict
    Token = dict
    ScraperStatus = dict
    DatabaseStats = dict

@dataclass
class APIUser:
    """API user representation."""
    user_id: str
    username: str
    email: str
    role: UserRole
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    rate_limit_override: Optional[int] = None

class AuthenticationService:
    """Authentication and user management service."""

    def __init__(self):
        self.users: Dict[str, APIUser] = {}
        self.sessions: Dict[str, str] = {}  # token -> user_id
        self._setup_default_users()

    def _setup_default_users(self):
        """Create default users for testing."""
        admin_user = APIUser(
            user_id='admin', 
            username='admin', 
            email='admin@pokertool.com',
            role=UserRole.ADMIN, 
            rate_limit_override=1000
        )
        self.users['admin'] = admin_user

        # Create demo user for frontend testing
        demo_user = APIUser(
            user_id='demo_user',
            username='demo_user',
            email='demo@pokertool.com',
            role=UserRole.USER,
            rate_limit_override=100
        )
        self.users['demo_user'] = demo_user

        # Create admin token
        admin_token = self.create_access_token(admin_user)
        self.sessions[admin_token] = admin_user.user_id

        # Create demo token for frontend testing
        demo_token = 'demo_token'
        self.sessions[demo_token] = demo_user.user_id

        logger.info('Default admin and demo users created')

    def create_user(self, username: str, email: str, password: str, role: UserRole = UserRole.USER) -> APIUser:
        """Create a new user."""
        user_id = hashlib.sha256(f'{username}:{email}:{time.time()}'.encode()).hexdigest()[:16]

        if any(u.username == username for u in self.users.values()):
            if HTTPException:
                raise HTTPException(status_code=400, detail='Username already exists')
            raise ValueError('Username already exists')

        if any(u.email == email for u in self.users.values()):
            if HTTPException:
                raise HTTPException(status_code=400, detail='Email already exists')
            raise ValueError('Email already exists')

        user = APIUser(
            user_id=user_id,
            username=username,
            email=email,
            role=role
        )

        self.users[user_id] = user
        logger.info(f'Created user: {username} ({role.value})')
        return user

    def create_access_token(self, user: APIUser) -> str:
        """Create JWT access token for user."""
        if not jwt:
            # Fallback token without JWT
            token = hashlib.sha256(f"{user.user_id}:{time.time()}:{secrets.token_hex(16)}".encode()).hexdigest()
            return token

        payload = {
            'sub': user.user_id,
            'username': user.username,
            'role': user.role.value,
            'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow()
        }

        token = jwt.encode(payload, API_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    def verify_token(self, token: str) -> Optional[APIUser]:
        """Verify and decode token.

        Always accept session-mapped tokens (e.g., demo_token) regardless of
        whether the JWT library is installed, then fall back to JWT decoding.
        """
        # 1) Fast path: explicit session tokens
        user_id = self.sessions.get(token)
        if user_id:
            user = self.users.get(user_id)
            if user and user.is_active:
                user.last_active = datetime.utcnow()
                return user

        # 2) JWT decoding if available
        try:
            if jwt:
                payload = jwt.decode(token, API_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                user_id = payload.get('sub')
                if not user_id:
                    return None
                user = self.users.get(user_id)
                if not user or not user.is_active:
                    return None
                user.last_active = datetime.utcnow()
                return user
        except Exception:
            return None

        return None

    def get_user_by_credentials(self, username: str, password: str) -> Optional[APIUser]:
        """Get user by username and password (simplified)."""
        # In production, you'd hash and verify passwords properly
        for user in self.users.values():
            if user.username == username and user.is_active:
                return user
        return None

class ConnectionManager:
    """WebSocket connection manager with optimized cleanup."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}  # user_id -> connection_ids
        self.connection_timestamps: Dict[str, float] = {}  # connection_id -> last_activity

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_timestamps[connection_id] = time.time()

        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)

        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")

    def disconnect(self, connection_id: str, user_id: str):
        """Remove WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if connection_id in self.connection_timestamps:
            del self.connection_timestamps[connection_id]

        if user_id in self.user_connections:
            if connection_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

        logger.info(f'WebSocket disconnected: {connection_id}')

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send message to specific connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                if WebSocketState and websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                    self.connection_timestamps[connection_id] = time.time()
                else:
                    await self._cleanup_connection(connection_id)
            except Exception:
                await self._cleanup_connection(connection_id)

    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send message to all connections of a user."""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id][:]:  # Copy list
                await self.send_personal_message(message, connection_id)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connections."""
        disconnected = []
        for connection_id, websocket in list(self.active_connections.items()):
            try:
                if WebSocketState and websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                    self.connection_timestamps[connection_id] = time.time()
                else:
                    disconnected.append(connection_id)
            except Exception:
                disconnected.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected:
            await self._cleanup_connection(connection_id)

    async def cleanup_inactive(self, timeout: int = 1800):
        """Clean up inactive connections (30 minutes default)."""
        current_time = time.time()
        inactive_connections = [
            conn_id for conn_id, last_activity in self.connection_timestamps.items()
            if current_time - last_activity > timeout
        ]
        
        for connection_id in inactive_connections:
            await self._cleanup_connection(connection_id)
        
        if inactive_connections:
            logger.info(f"Cleaned up {len(inactive_connections)} inactive WebSocket connections")

    async def _cleanup_connection(self, connection_id: str):
        """Internal method to clean up a single connection."""
        # Find user_id for cleanup
        user_id = None
        for uid, conn_ids in self.user_connections.items():
            if connection_id in conn_ids:
                user_id = uid
                break
        
        if user_id:
            self.disconnect(connection_id, user_id)

class DetectionWebSocketManager:
    """Manages WebSocket connections for real-time detection events (no authentication)."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_timestamps: Dict[str, float] = {}

    async def connect(self, connection_id: str, websocket: WebSocket):
        """Register a new detection WebSocket connection."""
        self.active_connections[connection_id] = websocket
        self.connection_timestamps[connection_id] = time.time()
        logger.info(f'Detection WebSocket connected: {connection_id} (total: {len(self.active_connections)})')

    async def disconnect(self, connection_id: str):
        """Remove a detection WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.connection_timestamps:
            del self.connection_timestamps[connection_id]
        logger.info(f'Detection WebSocket disconnected: {connection_id} (remaining: {len(self.active_connections)})')

    async def broadcast_detection(self, event: Dict[str, Any]):
        """Broadcast a detection event to all connected clients."""
        if not self.active_connections:
            return

        disconnected = []
        for connection_id, websocket in list(self.active_connections.items()):
            try:
                if WebSocketState and websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(event)
                    self.connection_timestamps[connection_id] = time.time()
                else:
                    disconnected.append(connection_id)
            except Exception as e:
                logger.warning(f'Failed to send detection to {connection_id}: {e}')
                disconnected.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)

# Global detection WebSocket manager
_detection_ws_manager = None

def get_detection_ws_manager() -> DetectionWebSocketManager:
    """Get the global detection WebSocket manager."""
    global _detection_ws_manager
    if _detection_ws_manager is None:
        _detection_ws_manager = DetectionWebSocketManager()
    return _detection_ws_manager

async def broadcast_detection_event(event_type: str, severity: str, message: str, data: Dict[str, Any] = None):
    """
    Broadcast a detection event to all connected WebSocket clients.

    Args:
        event_type: Type of detection (player, card, pot, action, system, error)
        severity: Severity level (info, success, warning, error)
        message: Human-readable message describing the detection
        data: Optional additional data about the detection
    """
    manager = get_detection_ws_manager()
    event = {
        'type': event_type,
        'severity': severity,
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data or {}
    }
    await manager.broadcast_detection(event)

class APIServices:
    """Container for API services with dependency injection."""

    def __init__(self):
        self.auth_service = AuthenticationService()
        self.connection_manager = ConnectionManager()
        self.thread_pool = get_thread_pool()

        # Lazy-initialised components to keep startup snappy
        self._db = None
        self._db_lock = threading.Lock()

        self._analytics_dashboard = None
        self._gamification_engine = None
        self._community_platform = None
        self._rum_metrics = None
        self._rum_lock = threading.Lock()

        self._limiter = None
        self._limiter_lock = threading.Lock()
        
        # Cache for frequently accessed data
        self._user_cache = {}
        self._cache_ttl = 300  # 5 minutes

    @property
    def db(self):
        """Lazy database accessor."""
        if self._db is None:
            with self._db_lock:
                if self._db is None:
                    self._db = self._initialize_database()
        return self._db

    def _initialize_database(self):
        """Initialise primary database with SQLite fallback."""
        try:
            return get_production_db()
        except RuntimeError:
            try:
                from .database import (
                    ProductionDatabase as FallbackDatabase,
                    DatabaseConfig as FallbackConfig,
                    DatabaseType,
                )

                fallback_path = os.getenv("POKER_DB_PATH", "poker_decisions.db")
                fallback_config = FallbackConfig(
                    db_type=DatabaseType.SQLITE,
                    db_path=fallback_path,
                )
                fallback_db = FallbackDatabase(fallback_config)

                # Update production_database module so subsequent lookups reuse the fallback.
                try:
                    from . import production_database as prod_db

                    prod_db._production_db = fallback_db  # type: ignore[attr-defined]
                    logger.info(
                        "Using SQLite fallback production database at %s", fallback_path
                    )
                except Exception:
                    pass

                return fallback_db
            except Exception as exc:
                logger.error("Failed to initialize fallback database: %s", exc)
                raise

    @property
    def analytics_dashboard(self):
        """Lazy initialisation for analytics dashboard."""
        if self._analytics_dashboard is None:
            from .analytics_dashboard import AnalyticsDashboard  # Local import to avoid startup hit
            self._analytics_dashboard = AnalyticsDashboard()
        return self._analytics_dashboard

    @property
    def gamification_engine(self):
        """Lazy initialisation for gamification engine with default seed."""
        if self._gamification_engine is None:
            from .gamification import GamificationEngine, Achievement, Badge  # Local import for speed

            engine = GamificationEngine()

            if 'volume_grinder' not in engine.achievements:
                engine.register_achievement(Achievement(
                    achievement_id='volume_grinder',
                    title='Volume Grinder',
                    description='Play 100 hands in a day',
                    points=200,
                    condition={'hands_played': 100}
                ))
            if 'marathon' not in engine.badges:
                engine.register_badge(Badge(
                    badge_id='marathon',
                    title='Marathon',
                    description='Maintain a seven day activity streak',
                    tier='gold'
                ))

            self._gamification_engine = engine
        return self._gamification_engine

    @property
    def community_platform(self):
        """Lazy initialisation for community platform with welcome post."""
        if self._community_platform is None:
            from .community_features import CommunityPlatform, ForumPost  # Local import for speed

            platform = CommunityPlatform()
            if not platform.posts:
                platform.create_post(ForumPost(
                    post_id='welcome',
                    author='coach',
                    title='Welcome to the PokerTool community',
                    content='Introduce yourself and share what you are working on this week.',
                    tags=['announcement']
                ))

            self._community_platform = platform
        return self._community_platform

    @property
    def rum_metrics(self):
        """Lazy initialisation for RUM metrics store."""
        if self._rum_metrics is None:
            with self._rum_lock:
                if self._rum_metrics is None:
                    from .rum_metrics import RUMMetricsStore  # Local import to avoid import cost when unused
                    storage_override = os.getenv("POKERTOOL_RUM_DIR")
                    store = RUMMetricsStore(Path(storage_override)) if storage_override else RUMMetricsStore()
                    self._rum_metrics = store
        return self._rum_metrics

    @property
    def limiter(self):
        """Lazy initialisation for rate limiter."""
        if self._limiter is None:
            with self._limiter_lock:
                if self._limiter is None:
                    try:
                        limiter = Limiter(key_func=get_remote_address, storage_url=RATE_LIMIT_STORAGE_URL)
                    except Exception:
                        limiter = Limiter(key_func=get_remote_address)
                    self._limiter = limiter
        return self._limiter

    def get_cached_user(self, token: str) -> Optional[APIUser]:
        """Get user with caching to reduce database lookups."""
        cache_key = hashlib.sha256(token.encode()).hexdigest()[:16]
        
        if cache_key in self._user_cache:
            cached_user, timestamp = self._user_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return cached_user
            del self._user_cache[cache_key]
        
        user = self.auth_service.verify_token(token)
        if user:
            self._user_cache[cache_key] = (user, time.time())
        
        return user

    def cleanup_cache(self):
        """Clean expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._user_cache.items()
            if current_time - timestamp > self._cache_ttl
        ]
        for key in expired_keys:
            del self._user_cache[key]


class PokerToolAPI:
    """Main API application with optimized architecture."""

    def __init__(self, services: APIServices = None):
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI dependencies not available. Install fastapi, slowapi, redis, etc.")

        self.services = services or APIServices()
        
        self.app = FastAPI(
            title='PokerTool API',
            description='''
# PokerTool RESTful API

Comprehensive poker analysis and real-time screen scraping API with advanced features.

## Features

- **Hand Analysis**: GTO-based poker hand analysis and recommendations
- **Screen Scraping**: Real-time poker table detection and data extraction
- **ML Analytics**: Opponent modeling, calibration metrics, and active learning
- **System Health**: Real-time monitoring of all system components
- **WebSockets**: Real-time updates for detections and health status
- **Authentication**: JWT-based secure authentication with role-based access control
- **Analytics**: Usage tracking, gamification, and community features

## Authentication

Most endpoints require Bearer token authentication. Obtain a token via `/auth/token` endpoint.

Example:
```
Authorization: Bearer <your_token_here>
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse. Limits vary by endpoint and user role.

## WebSocket Endpoints

- `/ws/{user_id}?token={token}`: Authenticated WebSocket for user-specific updates
- `/ws/detections`: Public WebSocket for real-time poker table detection events
- `/ws/system-health`: System health monitoring updates

## Security

This API implements comprehensive security measures including:
- HTTPS/WSS enforcement
- Content Security Policy (CSP)
- XSS protection
- CSRF protection
- Rate limiting
- Input validation
            ''',
            version='1.0.0',
            contact={
                'name': 'PokerTool Development Team',
                'email': 'support@pokertool.com'
            },
            license_info={
                'name': 'MIT',
                'url': 'https://opensource.org/licenses/MIT'
            },
            openapi_tags=[
                {'name': 'health', 'description': 'Health check and system status'},
                {'name': 'auth', 'description': 'Authentication and user management'},
                {'name': 'analysis', 'description': 'Hand analysis and poker strategy'},
                {'name': 'scraper', 'description': 'Screen scraping and table detection'},
                {'name': 'system', 'description': 'System health monitoring'},
                {'name': 'ml', 'description': 'Machine learning features and analytics'},
                {'name': 'database', 'description': 'Hand history and statistics'},
                {'name': 'analytics', 'description': 'Usage analytics and metrics'},
                {'name': 'gamification', 'description': 'Achievements, badges, and leaderboards'},
                {'name': 'community', 'description': 'Community features and social'},
                {'name': 'admin', 'description': 'Administrative endpoints (admin only)'}
            ],
            swagger_ui_parameters={
                'docExpansion': 'none',
                'filter': True,
                'syntaxHighlight.theme': 'monokai'
            }
        )

        self._setup_sentry()
        self._setup_tracing()
        self._setup_middleware()
        self._setup_routes()
        self._setup_background_tasks()

        logger.info('PokerTool API initialized with optimized architecture')
    
    def _setup_sentry(self):
        """Initialize Sentry error tracking for API."""
        if not SENTRY_AVAILABLE:
            logger.info("Sentry not available for API error tracking")
            return

        sentry_dsn = os.getenv('SENTRY_DSN')
        if not sentry_dsn:
            logger.info("SENTRY_DSN not configured for API")
            return

        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FastApiIntegration()],
                traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
                profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
                environment=os.getenv('POKERTOOL_ENV', 'development'),
                release=os.getenv('POKERTOOL_VERSION', 'unknown'),
            )
            logger.info("Sentry initialized for API error tracking")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry for API: {e}")

    def _setup_tracing(self):
        """Initialize OpenTelemetry distributed tracing."""
        try:
            from pokertool.tracing import initialize_tracing, instrument_fastapi

            # Initialize tracing with optional console export for development
            enable_console = os.getenv('OTEL_CONSOLE_EXPORT', 'false').lower() == 'true'
            otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')

            if initialize_tracing(
                service_name="pokertool-api",
                enable_console_export=enable_console,
                export_endpoint=otlp_endpoint
            ):
                # Instrument FastAPI app
                instrument_fastapi(self.app)
                logger.info("OpenTelemetry tracing initialized and FastAPI instrumented")
            else:
                logger.info("OpenTelemetry tracing not initialized (dependencies may not be installed)")
        except ImportError:
            logger.info("OpenTelemetry tracing module not available")
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")

    def _setup_background_tasks(self):
        """Setup background cleanup tasks."""
        import asyncio
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("Starting PokerTool API background tasks...")

            loop = asyncio.get_running_loop()
            try:
                from pokertool.detection_events import (
                    clear_detection_event_loop,
                    register_detection_event_loop,
                )
            except ImportError:
                register_detection_event_loop = None  # type: ignore
                clear_detection_event_loop = None  # type: ignore
            else:
                register_detection_event_loop(loop)

            # Initialize and start health checker
            from pokertool.system_health_checker import get_health_checker, register_all_health_checks
            health_checker = get_health_checker(check_interval=30)
            register_all_health_checks(health_checker)
            health_checker.start_periodic_checks()
            logger.info("System health checker initialized and started")

            # Start periodic cleanup task
            cleanup_task = asyncio.create_task(self._periodic_cleanup())

            yield

            # Shutdown
            logger.info("Shutting down PokerTool API background tasks...")

            # Stop health checker
            await health_checker.stop_periodic_checks()
            logger.info("System health checker stopped")

            # Stop cleanup task
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

            if clear_detection_event_loop:
                clear_detection_event_loop()

        self.app.router.lifespan_context = lifespan

    async def _periodic_cleanup(self):
        """Periodic cleanup task for caches and connections."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                self.services.cleanup_cache()
                # Cleanup inactive WebSocket connections
                await self.services.connection_manager.cleanup_inactive()
                logger.debug("Performed periodic cleanup")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")

    def _setup_middleware(self):
        """Setup API middleware."""
        # Set the limiter on app.state so SlowAPIMiddleware can access it
        self.app.state.limiter = self.services.limiter
        self.app.add_middleware(SlowAPIMiddleware)
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        # Add request logging and correlation ID middleware
        @self.app.middleware("http")
        async def add_correlation_id_and_logging(request, call_next):
            """Add correlation ID for distributed tracing and log requests/responses."""
            import uuid

            # Generate or extract correlation ID
            correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
            request.state.correlation_id = correlation_id

            # Log incoming request
            start_time = time.time()
            logger.info(
                f"Request started",
                extra={
                    'correlation_id': correlation_id,
                    'method': request.method,
                    'path': request.url.path,
                    'client_ip': request.client.host if request.client else 'unknown',
                    'user_agent': request.headers.get('user-agent', 'unknown')
                }
            )

            # Process request
            try:
                response = await call_next(request)

                # Calculate request duration
                duration = time.time() - start_time

                # Log response
                logger.info(
                    f"Request completed",
                    extra={
                        'correlation_id': correlation_id,
                        'method': request.method,
                        'path': request.url.path,
                        'status_code': response.status_code,
                        'duration_ms': round(duration * 1000, 2)
                    }
                )

                # Add correlation ID to response headers
                response.headers['X-Correlation-ID'] = correlation_id
                response.headers['X-Response-Time'] = f"{round(duration * 1000, 2)}ms"

                return response

            except Exception as e:
                # Log error with correlation ID
                duration = time.time() - start_time
                logger.error(
                    f"Request failed: {str(e)}",
                    extra={
                        'correlation_id': correlation_id,
                        'method': request.method,
                        'path': request.url.path,
                        'duration_ms': round(duration * 1000, 2),
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise

        # Add security headers middleware
        @self.app.middleware("http")
        async def add_security_headers(request, call_next):
            """Add comprehensive security headers to all responses."""
            response = await call_next(request)

            # Content Security Policy - Prevents XSS and other injection attacks
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'"
            )

            # HTTP Strict Transport Security - Enforces HTTPS
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

            # X-Frame-Options - Prevents clickjacking
            response.headers["X-Frame-Options"] = "DENY"

            # X-Content-Type-Options - Prevents MIME sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"

            # X-XSS-Protection - Legacy XSS protection
            response.headers["X-XSS-Protection"] = "1; mode=block"

            # Referrer-Policy - Controls referrer information
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # Permissions-Policy - Controls browser features
            response.headers["Permissions-Policy"] = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            )

            return response

        # Add response compression middleware
        try:
            from fastapi.middleware.gzip import GZipMiddleware
            self.app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)
            logger.info("Response compression enabled (GZip)")
        except ImportError:
            logger.warning("GZip middleware not available")

        allowed_origins = os.getenv(
            'POKERTOOL_ALLOWED_ORIGINS',
            'http://localhost:3000,http://127.0.0.1:3000'
        )
        cors_origins = [origin.strip() for origin in allowed_origins.split(',') if origin.strip()]

        allow_credentials_env = os.getenv('POKERTOOL_ALLOW_CREDENTIALS', 'false').lower()
        cors_allow_credentials = allow_credentials_env in {'1', 'true', 'yes'}

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ['*'],
            allow_credentials=cors_allow_credentials,
            allow_methods=['*'],
            allow_headers=['*'],
        )

        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=['*']  # In production, specify actual hosts
        )

    def _setup_routes(self):
        """Setup API routes."""

        # Authentication dependency
        security = HTTPBearer()

        async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> APIUser:
            user = self.services.get_cached_user(credentials.credentials)
            if not user:
                raise HTTPException(status_code=401, detail='Invalid or expired token')
            return user

        async def get_admin_user(user: APIUser = Depends(get_current_user)) -> APIUser:
            if user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail='Admin access required')
            return user

        # Health check
        # Simple in-memory cache for system health endpoint
        self._health_cache_data = None
        self._health_cache_at = 0.0
        self._health_cache_ttl = float(os.getenv('SYSTEM_HEALTH_TTL_SECONDS', '5'))

        @self.app.get('/health', tags=['health'], summary='Health Check')
        async def health_check():
            """
            Basic health check endpoint to verify API is running.

            Returns a simple status message with timestamp.
            """
            return {'status': 'healthy', 'timestamp': datetime.utcnow()}

        # Backend Startup Status Endpoints
        @self.app.get('/api/backend/startup/status', tags=['backend'], summary='Backend Startup Status')
        async def get_backend_startup_status():
            """
            Get current backend startup status including progress and timing.

            Returns detailed information about startup steps, elapsed time, and remaining tasks.
            """
            try:
                from pokertool.backend_startup_logger import get_startup_logger
                logger_instance = get_startup_logger()
                return logger_instance.get_status()
            except Exception as e:
                return {
                    'error': str(e),
                    'elapsed_time': 0,
                    'current_step': 0,
                    'total_steps': 0,
                    'steps_completed': 0,
                    'steps_remaining': 0,
                    'steps': []
                }

        @self.app.get('/api/backend/startup/log', tags=['backend'], summary='Backend Startup Log')
        async def get_backend_startup_log(lines: int = 100):
            """
            Get recent lines from backend startup log.

            Args:
                lines: Number of lines to return (default 100)

            Returns list of log lines with timestamps.
            """
            try:
                from pokertool.backend_startup_logger import get_startup_logger
                logger_instance = get_startup_logger()
                log_lines = logger_instance.get_log_tail(lines)
                return {'log_lines': log_lines, 'total_lines': len(log_lines)}
            except Exception as e:
                return {'error': str(e), 'log_lines': [], 'total_lines': 0}

        @self.app.get('/api/todo', tags=['development'], summary='Development TODO List')
        async def get_todo():
            """
            Get TODO.md content with parsed checkboxes and priorities.

            Returns structured TODO list for development progress tracking.
            """
            try:
                from pathlib import Path
                import re

                # Read TODO.md from docs/
                todo_path = Path(__file__).parent.parent.parent / 'docs' / 'TODO.md'

                if not todo_path.exists():
                    return {'error': 'TODO.md not found', 'raw_content': '', 'items': []}

                with open(todo_path, 'r') as f:
                    raw_content = f.read()

                # Parse TODO items
                items = []
                for line in raw_content.split('\n'):
                    # Match lines like: - [x] [P0][S] Title — description
                    match = re.match(r'^- \[([ x])\] \[([P\d]+)\]\[([SML])\] (.+?)(?:—|—) (.+)$', line)
                    if match:
                        checked, priority, effort, title, description = match.groups()
                        items.append({
                            'checked': checked.lower() == 'x',
                            'priority': priority,
                            'effort': effort,
                            'title': title.strip(),
                            'description': description.strip()
                        })

                return {
                    'raw_content': raw_content,
                    'items': items,
                    'total_items': len(items),
                    'completed_items': sum(1 for item in items if item['checked'])
                }
            except Exception as e:
                return {'error': str(e), 'raw_content': '', 'items': []}

        # Status endpoint for status window
        @self.app.get('/api/status', tags=['health'], summary='Application Status')
        async def app_status():
            """
            Get current application status for status window.

            Returns information about scraper activity, table detection, etc.
            """
            try:
                # Get scraper status if available
                from pokertool.modules import poker_screen_scraper_betfair
                scraper = getattr(poker_screen_scraper_betfair, '_scraper_instance', None)

                status_data = {
                    'scraper_active': scraper is not None and getattr(scraper, 'is_running', False),
                    'last_detection': None,
                    'table_name': 'N/A',
                    'timestamp': datetime.utcnow().isoformat()
                }

                # Try to get last detection info if scraper is active
                if status_data['scraper_active'] and scraper:
                    last_state = getattr(scraper, 'last_state', None)
                    if last_state:
                        status_data['last_detection'] = last_state.get('timestamp', 'Just now')
                        status_data['table_name'] = last_state.get('table_name', 'N/A')

                return status_data
            except Exception as e:
                logger.error(f"Error getting app status: {e}")
                return {
                    'scraper_active': False,
                    'last_detection': None,
                    'table_name': 'N/A',
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': str(e)
                }

        # System Health Monitoring Endpoints
        @self.app.get('/api/system/health', tags=['system'], summary='Get System Health')
        @self.services.limiter.limit('60/minute')
        async def get_system_health(request: Request):
            """
            Get comprehensive system health status for all features.
            Returns health data for all monitored components.
            """
            # Cache results for a short TTL to reduce load
            now = time.time()
            if self._health_cache_data and (now - self._health_cache_at) < self._health_cache_ttl:
                return self._health_cache_data

            from pokertool.system_health_checker import get_health_checker
            checker = get_health_checker()
            summary = checker.get_summary()
            self._health_cache_data = summary
            self._health_cache_at = now
            return summary

        @self.app.get('/api/system/health/{category}')
        async def get_category_health(category: str):
            """
            Get health status for a specific category.
            Categories: backend, scraping, ml, gui, advanced
            """
            from pokertool.system_health_checker import get_health_checker
            checker = get_health_checker()
            summary = checker.get_summary()

            if category not in summary['categories']:
                raise HTTPException(status_code=404, detail=f'Category {category} not found')

            return {
                'timestamp': summary['timestamp'],
                'category': category,
                'data': summary['categories'][category]
            }

        @self.app.post('/api/system/health/refresh')
        async def refresh_system_health(background_tasks: BackgroundTasks):
            """
            Trigger immediate execution of all health checks.
            Returns job ID for tracking completion.
            """
            from pokertool.system_health_checker import get_health_checker

            checker = get_health_checker()

            # Run checks in background
            async def run_checks():
                await checker.run_all_checks()

            background_tasks.add_task(run_checks)

            job_id = f"health_check_{int(time.time() * 1000)}"
            return {
                'job_id': job_id,
                'status': 'started',
                'message': 'Health checks initiated',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        @self.app.get('/api/system/health/history', tags=['system'], summary='Get Health History')
        @self.services.limiter.limit('12/minute')
        async def get_health_history(request: Request, hours: int = 24):
            """
            Get historical health check data for the specified time period.

            Args:
                request: FastAPI request object (required for rate limiting)
                hours: Number of hours of history to retrieve (default: 24)

            Returns:
                List of historical health check results with timestamps
            """
            from pokertool.system_health_checker import get_health_checker
            
            if hours < 1 or hours > 168:  # Max 1 week
                raise HTTPException(status_code=400, detail='Hours must be between 1 and 168')
            
            checker = get_health_checker()
            history = checker.get_history(hours=hours)
            
            return {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'period_hours': hours,
                'data_points': len(history),
                'history': history
            }
        
        @self.app.get('/api/system/health/trends', tags=['system'], summary='Get Health Trends')
        @self.services.limiter.limit('12/minute')
        async def get_health_trends(request: Request, hours: int = 24):
            """
            Get health trend analysis over the specified time period.

            Analyzes patterns, failure rates, and average latencies per feature.

            Args:
                request: FastAPI request object (required for rate limiting)
                hours: Number of hours to analyze (default: 24)
            
            Returns:
                Trend analysis including uptime percentages and latency stats
            """
            from pokertool.system_health_checker import get_health_checker
            
            if hours < 1 or hours > 168:  # Max 1 week
                raise HTTPException(status_code=400, detail='Hours must be between 1 and 168')
            
            checker = get_health_checker()
            trends = checker.get_trends(hours=hours)
            
            return {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'trends': trends
            }

        # Model Calibration Endpoints
        @self.app.get('/api/ml/calibration/stats', tags=['ml'], summary='Get Calibration Stats')
        async def get_calibration_stats():
            """
            Get current model calibration statistics.
            Returns calibration metrics, drift status, and performance indicators.
            """
            try:
                from pokertool.model_calibration import get_calibration_system
                system = get_calibration_system()
                stats = system.get_stats()
                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': stats
                }
            except Exception as e:
                logger.error(f"Error fetching calibration stats: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        @self.app.get('/api/ml/calibration/metrics')
        async def get_calibration_metrics():
            """
            Get detailed calibration metrics history.
            Returns Brier score, log loss, and calibration error over time.
            """
            try:
                from pokertool.model_calibration import get_calibration_system
                system = get_calibration_system()

                metrics = []
                for metric in system.calibration_metrics_history:
                    metrics.append({
                        'timestamp': metric.timestamp,
                        'brier_score': metric.brier_score,
                        'log_loss': metric.log_loss,
                        'calibration_error': metric.calibration_error,
                        'num_predictions': metric.num_predictions
                    })

                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'metrics': metrics[-100:]  # Last 100 data points
                }
            except Exception as e:
                logger.error(f"Error fetching calibration metrics: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        @self.app.get('/api/ml/calibration/drift')
        async def get_drift_metrics():
            """
            Get model drift detection metrics.
            Returns PSI, KL divergence, and drift status indicators.
            """
            try:
                from pokertool.model_calibration import get_calibration_system
                system = get_calibration_system()

                drift_data = []
                for drift in system.drift_metrics_history:
                    drift_data.append({
                        'timestamp': drift.timestamp,
                        'psi': drift.psi,
                        'kl_divergence': drift.kl_divergence,
                        'distribution_shift': drift.distribution_shift,
                        'status': drift.status.value,
                        'alerts': drift.alerts
                    })

                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'drift_metrics': drift_data[-100:]  # Last 100 data points
                }
            except Exception as e:
                logger.error(f"Error fetching drift metrics: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        # Sequential Opponent Fusion endpoints
        @self.app.get('/api/ml/opponent-fusion/stats')
        async def get_opponent_fusion_stats(request):
            """Get opponent fusion statistics"""
            try:
                # Import and initialize fusion system
                import pokertool.sequential_opponent_fusion as fusion_module

                # Return mock data structure - actual implementation would load from system
                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': {
                        'tracked_players': 0,
                        'total_hands_analyzed': 0,
                        'active_patterns': 0,
                        'prediction_accuracy': 0.0,
                        'temporal_window_size': 10,
                        'status': 'active'
                    }
                }
            except Exception as e:
                logger.error(f"Error fetching opponent fusion stats: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        @self.app.get('/api/ml/opponent-fusion/players')
        async def get_tracked_players(request):
            """Get list of tracked players with their stats"""
            try:
                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'players': []
                }
            except Exception as e:
                logger.error(f"Error fetching tracked players: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        # Active Learning endpoints
        @self.app.get('/api/ml/active-learning/stats')
        async def get_active_learning_stats(request):
            """Get active learning statistics"""
            try:
                # Import active learning module
                import pokertool.active_learning as al_module

                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': {
                        'pending_reviews': 0,
                        'total_feedback': 0,
                        'high_uncertainty_events': 0,
                        'model_accuracy_improvement': 0.0,
                        'last_retraining': None,
                        'status': 'active'
                    }
                }
            except Exception as e:
                logger.error(f"Error fetching active learning stats: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        @self.app.get('/api/ml/active-learning/pending')
        async def get_pending_feedback(request):
            """Get pending feedback events"""
            try:
                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'events': []
                }
            except Exception as e:
                logger.error(f"Error fetching pending feedback: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        # Scraping Accuracy endpoints
        @self.app.get('/api/scraping/accuracy/stats')
        async def get_scraping_accuracy_stats(request):
            """Get scraping accuracy statistics"""
            try:
                # Import scraping accuracy module
                import pokertool.scraping_accuracy_system as scraping_module

                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': {
                        'overall_accuracy': 0.0,
                        'pot_corrections': 0,
                        'card_recognition_accuracy': 0.0,
                        'ocr_corrections': 0,
                        'temporal_consensus_improvements': 0,
                        'total_frames_processed': 0,
                        'status': 'active'
                    }
                }
            except Exception as e:
                logger.error(f"Error fetching scraping accuracy stats: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        @self.app.get('/api/scraping/accuracy/metrics')
        async def get_scraping_accuracy_metrics(request):
            """Get detailed scraping accuracy metrics"""
            try:
                return {
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat(),
                    'metrics': []
                }
            except Exception as e:
                logger.error(f"Error fetching scraping accuracy metrics: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        # Authentication endpoints
        @self.app.post('/auth/token', response_model=Token, tags=['auth'], summary='Login')
        @self.services.limiter.limit('10/minute')
        async def login(request: Request, username: str, password: str):
            user = self.services.auth_service.get_user_by_credentials(username, password)
            if not user:
                raise HTTPException(status_code=401, detail='Invalid credentials')

            token = self.services.auth_service.create_access_token(user)
            return Token(
                access_token=token,
                token_type='bearer',
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_role=user.role
            )

        @self.app.post('/auth/register', response_model=Dict[str, str])
        @self.services.limiter.limit('5/minute')
        async def register(request, user_data: UserCreate):
            user = self.services.auth_service.create_user(
                username=user_data.username,
                email=user_data.email,
                password=user_data.password,
                role=user_data.role
            )
            return {'message': f'User {user.username} created successfully', 'user_id': user.user_id}

        # Hand analysis endpoints
        @self.app.post('/analyze/hand', response_model=HandAnalysisResponse)
        @self.services.limiter.limit('100/minute')
        async def analyze_hand(request, analysis_request: HandAnalysisRequest, 
                              user: APIUser = Depends(get_current_user)):

            # Import analysis function
            from .core import analyse_hand, parse_card

            # Perform analysis
            try:
                # Parse hole cards
                hole_cards = []
                if len(analysis_request.hand) >= 4:
                    hole_cards.append(parse_card(analysis_request.hand[:2]))
                    hole_cards.append(parse_card(analysis_request.hand[2:4]))

                result = analyse_hand(hole_cards)

                # Save to database
                metadata = {
                    'user_id': user.user_id,
                    'position': analysis_request.position,
                    'pot_size': analysis_request.pot_size,
                    'to_call': analysis_request.to_call,
                    'num_players': analysis_request.num_players,
                    'api_version': '1.0.0'
                }

                self.services.db.save_hand_analysis(
                    hand=analysis_request.hand,
                    board=analysis_request.board,
                    result=str(result),
                    metadata=metadata
                )

                response = HandAnalysisResponse(
                    hand=analysis_request.hand,
                    board=analysis_request.board,
                    analysis=str(result),
                    recommendation=result.advice if hasattr(result, 'advice') else 'Fold',
                    metadata=metadata
                )

                # Notify via WebSocket
                await self.services.connection_manager.send_to_user({
                    'type': 'hand_analysis',
                    'data': response.dict()
                }, user.user_id)

                return response

            except Exception as e:
                logger.error(f'Hand analysis failed: {e}')
                raise HTTPException(status_code=500, detail=f'Analysis failed: {str(e)}')

        # Screen scraper endpoints
        @self.app.get('/scraper/status', response_model=ScraperStatus)
        async def scraper_status(user: APIUser = Depends(get_current_user)):
            status = get_scraper_status()
            return ScraperStatus(**status)

        @self.app.post('/scraper/start')
        @self.services.limiter.limit('10/minute')
        async def start_scraper(request, site: str = 'GENERIC', continuous: bool = True, 
                               user: APIUser = Depends(get_current_user)):
            if user.role not in [UserRole.PREMIUM, UserRole.ADMIN]:
                raise HTTPException(status_code=403, detail='Premium access required for screen scraper')

            result = run_screen_scraper(site=site, continuous=continuous)
            return {'message': 'Scraper started', 'result': result}

        @self.app.post('/scraper/stop')
        async def stop_scraper_endpoint(user: APIUser = Depends(get_current_user)):
            result = stop_screen_scraper()
            return {'message': 'Scraper stopped', 'result': result}

        @self.app.post('/api/start-backend')
        async def start_backend():
            """Start the backend server process."""
            import subprocess
            import sys
            from pathlib import Path

            try:
                # Get the project root and venv python
                project_root = Path(__file__).resolve().parent.parent.parent
                venv_python = project_root / '.venv' / 'bin' / 'python'

                if not venv_python.exists():
                    venv_python = project_root / '.venv' / 'Scripts' / 'python.exe'

                if not venv_python.exists():
                    return {
                        'success': False,
                        'message': 'Virtual environment not found'
                    }

                # Check if backend is already running
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 5001))
                sock.close()

                if result == 0:
                    return {
                        'success': True,
                        'message': 'Backend already running'
                    }

                # Start the backend server
                env = os.environ.copy()
                env['PYTHONPATH'] = str(project_root / 'src')

                subprocess.Popen(
                    [str(venv_python), '-m', 'uvicorn', 'pokertool.api:create_app',
                     '--host', '0.0.0.0', '--port', '5001', '--factory'],
                    env=env,
                    cwd=project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )

                return {
                    'success': True,
                    'message': 'Backend server starting...'
                }

            except Exception as e:
                logger.error(f'Failed to start backend: {e}')
                return {
                    'success': False,
                    'message': f'Failed to start backend: {str(e)}'
                }

        # Database endpoints
        @self.app.get('/hands/recent')
        @self.services.limiter.limit('50/minute')
        async def get_recent_hands(request, limit: int = 10, offset: int = 0,
                                  user: APIUser = Depends(get_current_user)):
            hands = self.services.db.get_recent_hands(limit=min(limit, 100), offset=offset)
            return {'hands': hands, 'count': len(hands)}

        @self.app.get('/stats/database', response_model=DatabaseStats)
        async def database_stats(user: APIUser = Depends(get_current_user)):
            stats = self.services.db.get_database_stats()
            return DatabaseStats(
                database_type=stats['database_type'],
                total_hands=stats.get('activity', {}).get('total_hands', 0),
                unique_users=stats.get('activity', {}).get('unique_users', 0),
                recent_activity=stats.get('activity', {})
            )

        # Analytics endpoints
        @self.app.post('/analytics/events')
        async def record_analytics_event(event: AnalyticsEventRequest, user: APIUser = Depends(get_current_user)):
            from .analytics_dashboard import UsageEvent  # Local import to avoid startup cost

            event_user = event.user_id or user.user_id
            usage_event = UsageEvent(
                event_id=event.event_id,
                user_id=event_user,
                action=event.action,
                metadata=event.metadata,
            )
            self.services.analytics_dashboard.track_event(usage_event)
            return {'status': 'recorded', 'event_id': usage_event.event_id}

        @self.app.post('/analytics/sessions')
        async def record_session(session: AnalyticsSessionRequest, user: APIUser = Depends(get_current_user)):
            session_user = session.user_id or user.user_id
            self.services.analytics_dashboard.track_session(session_user, session.minutes)
            return {'status': 'recorded', 'user_id': session_user}

        @self.app.get('/analytics/metrics')
        async def analytics_metrics(user: APIUser = Depends(get_current_user)):
            metrics = self.services.analytics_dashboard.generate_metrics()
            return {
                'total_events': metrics.total_events,
                'active_users': metrics.active_users,
                'actions_per_user': metrics.actions_per_user,
                'most_common_actions': metrics.most_common_actions,
                'avg_session_length_minutes': metrics.avg_session_length_minutes,
            }

        @self.app.post('/api/rum/metrics', tags=['analytics'], summary='Ingest frontend performance metric')
        @self.services.limiter.limit('180/minute')
        async def ingest_rum_metric(
            request: Request,
            payload: RUMMetricPayload,
            background_tasks: BackgroundTasks,
        ):
            correlation_id = request.headers.get('x-correlation-id')
            client_ip = request.client.host if request.client else None
            user_agent = request.headers.get('user-agent')

            record = payload.to_store_record(
                user_agent=user_agent,
                client_ip=client_ip,
                correlation_id=correlation_id,
            )

            background_tasks.add_task(self.services.rum_metrics.record_metric, record)
            return JSONResponse(status_code=202, content={'status': 'accepted'})

        @self.app.get('/api/rum/summary', tags=['analytics'], summary='Summarise frontend RUM metrics')
        @self.services.limiter.limit('30/minute')
        async def rum_summary(request: Request, hours: int = 24, user: APIUser = Depends(get_current_user)):
            try:
                summary = self.services.rum_metrics.summarise(hours)
                return summary
            except Exception as exc:
                logger.error(f'Failed to summarise RUM metrics: {exc}')
                raise HTTPException(status_code=500, detail='Unable to summarise RUM metrics')

        # Frontend Error Logging to Trouble Feed
        @self.app.post('/api/errors/frontend', tags=['monitoring'], summary='Log frontend error to trouble feed')
        @self.services.limiter.limit('60/minute')
        async def log_frontend_error(
            request: Request,
            payload: FrontendErrorPayload,
        ):
            """
            Log frontend JavaScript/React errors to the centralized trouble feed.

            This endpoint allows the frontend to report errors that occur in the browser
            to the backend trouble feed system for AI analysis and debugging.
            """
            try:
                from pokertool.trouble_feed import log_frontend_error as log_fe_error, TroubleSeverity

                # Map severity string to enum
                severity_map = {
                    'WARNING': TroubleSeverity.WARNING,
                    'ERROR': TroubleSeverity.ERROR,
                    'CRITICAL': TroubleSeverity.CRITICAL,
                }
                severity = severity_map.get(payload.severity.upper(), TroubleSeverity.ERROR)

                # Enhance context with request metadata
                enhanced_context = {
                    **payload.context,
                    'url': payload.url or 'unknown',
                    'user_agent': payload.user_agent or request.headers.get('user-agent', 'unknown'),
                    'client_ip': request.client.host if request.client else 'unknown',
                    'timestamp': datetime.utcnow().isoformat(),
                }

                # Log to trouble feed
                log_fe_error(
                    error_type=payload.error_type,
                    error_message=payload.error_message,
                    stack_trace=payload.stack_trace,
                    component=payload.component,
                    context=enhanced_context,
                    severity=severity,
                )

                return JSONResponse(
                    status_code=202,
                    content={
                        'status': 'accepted',
                        'message': 'Error logged to trouble feed',
                        'timestamp': datetime.utcnow().isoformat(),
                    }
                )
            except Exception as exc:
                logger.error(f'Failed to log frontend error to trouble feed: {exc}')
                # Don't fail the request - just log it
                return JSONResponse(
                    status_code=500,
                    content={
                        'status': 'error',
                        'message': 'Failed to log error',
                        'detail': str(exc),
                    }
                )

        # Gamification endpoints
        @self.app.post('/gamification/activity')
        async def gamification_activity(activity: GamificationActivityRequest, user: APIUser = Depends(get_current_user)):
            state = self.services.gamification_engine.record_activity(activity.player_id, activity.metrics)
            return {
                'player_id': state.player_id,
                'experience': state.experience,
                'level': state.level,
                'achievements': state.achievements_unlocked,
                'badges': state.badges_earned,
            }

        @self.app.post('/gamification/badges')
        async def gamification_badge(request: GamificationBadgeRequest, admin_user: APIUser = Depends(get_admin_user)):
            self.services.gamification_engine.award_badge(request.player_id, request.badge_id)
            state = self.services.gamification_engine.progress_snapshot(request.player_id)
            return {
                'player_id': request.player_id,
                'badges': state.badges_earned if state else [],
            }

        @self.app.get('/gamification/progress/{player_id}')
        async def gamification_progress(player_id: str, user: APIUser = Depends(get_current_user)):
            from .gamification import ProgressState  # Local import to avoid startup cost

            state = self.services.gamification_engine.progress.get(player_id)
            if not state:
                state = self.services.gamification_engine.progress.setdefault(player_id, ProgressState(player_id=player_id))
            return state.__dict__

        @self.app.get('/gamification/leaderboard')
        async def gamification_leaderboard(limit: int = 10, user: APIUser = Depends(get_current_user)):
            leaderboard = self.services.gamification_engine.leaderboard(top_n=min(limit, 50))
            return {
                'leaderboard': [state.__dict__ for state in leaderboard]
            }

        # Community endpoints
        @self.app.get('/community/posts')
        async def list_posts(user: APIUser = Depends(get_current_user)):
            return {'posts': [self.services.community_platform._serialize_post(post) for post in self.services.community_platform.posts.values()]}

        @self.app.post('/community/posts')
        async def create_post(request, post: CommunityPostRequest, user: APIUser = Depends(get_current_user)):
            from .community_features import ForumPost  # Local import to avoid startup cost

            post_id = f'post_{int(time.time()*1000)}'
            forum_post = ForumPost(
                post_id=post_id,
                author=user.username,
                title=post.title,
                content=post.content,
                tags=post.tags,
            )
            self.services.community_platform.create_post(forum_post)
            return {'post_id': post_id}

        @self.app.post('/community/posts/{post_id}/reply')
        async def reply_post(post_id: str, reply: CommunityReplyRequest, user: APIUser = Depends(get_current_user)):
            self.services.community_platform.reply_to_post(post_id, user.username, reply.message)
            return {'status': 'ok'}

        @self.app.get('/community/challenges')
        async def list_challenges(user: APIUser = Depends(get_current_user)):
            return {'challenges': [challenge.__dict__ for challenge in self.services.community_platform.challenges.values()]}

        @self.app.post('/community/challenges')
        async def join_challenge(request, payload: ChallengeParticipationRequest, user: APIUser = Depends(get_current_user)):
            self.services.community_platform.join_challenge(payload.challenge_id, user.user_id)
            return {'status': 'joined', 'challenge_id': payload.challenge_id}

        @self.app.get('/community/mentorships')
        async def list_mentorships(user: APIUser = Depends(get_current_user)):
            return {'mentorships': [pair.__dict__ for pair in self.services.community_platform.mentorships]}

        @self.app.get('/community/tournaments')
        async def list_tournaments(user: APIUser = Depends(get_current_user)):
            return {'tournaments': [tournament.__dict__ for tournament in self.services.community_platform.tournaments.values()]}

        @self.app.get('/community/articles')
        async def list_articles(category: Optional[str] = None, user: APIUser = Depends(get_current_user)):
            articles = self.services.community_platform.list_articles(category)
            return {'articles': [article.__dict__ for article in articles]}

        # Admin endpoints
        @self.app.get('/admin/users')
        async def list_users(admin_user: APIUser = Depends(get_admin_user)):
            return {
                'users': [
                    {
                        'user_id': u.user_id,
                        'username': u.username,
                        'role': u.role.value,
                        'is_active': u.is_active,
                        'last_active': u.last_active.isoformat()
                    }
                    for u in self.services.auth_service.users.values()
                ]
            }

        @self.app.get('/admin/system/stats')
        async def system_stats(admin_user: APIUser = Depends(get_admin_user)):
            # Get thread pool stats (if available)
            try:
                thread_stats = self.services.thread_pool.get_stats()
            except (AttributeError, Exception):
                # Fallback for standard ThreadPoolExecutor
                thread_stats = {
                    'type': 'ThreadPoolExecutor',
                    'max_workers': self.services.thread_pool._max_workers if hasattr(self.services.thread_pool, '_max_workers') else 'unknown'
                }

            db_stats = self.services.db.get_database_stats()

            # Get model cache metrics
            model_cache_stats = {}
            try:
                from pokertool.model_cache import get_model_cache
                model_cache = get_model_cache()
                model_cache_stats = model_cache.get_metrics()
            except Exception as e:
                logger.warning(f"Could not get model cache stats: {e}")

            return {
                'threading': thread_stats,
                'database': db_stats,
                'model_cache': model_cache_stats,
                'websockets': {
                    'active_connections': len(self.services.connection_manager.active_connections),
                    'users_connected': len(self.services.connection_manager.user_connections)
                },
                'api': {
                    'total_users': len(self.services.auth_service.users),
                    'active_sessions': len(self.services.auth_service.sessions)
                }
            }

        # Public WebSocket endpoint for detection events (no auth required)
        @self.app.websocket('/ws/detections')
        async def detections_websocket(websocket: WebSocket):
            """
            Public WebSocket endpoint for real-time poker table detection events.
            No authentication required - sends detection log messages.
            """
            logger.info('Detection WebSocket handshake from %s', websocket.client)
            await websocket.accept()
            connection_id = f'det_{int(time.time() * 1000)}'
            detection_manager = get_detection_ws_manager()

            try:
                # Register connection
                await detection_manager.connect(connection_id, websocket)

                # Send welcome message
                await websocket.send_json({
                    'type': 'system',
                    'severity': 'info',
                    'message': 'Connected to detection stream - ready to receive poker table events',
                    'timestamp': datetime.utcnow().isoformat(),
                })

                # Keep connection alive - detection events are broadcasted via broadcast_detection_event()
                while True:
                    try:
                        # Keep alive - receive any client messages (like ping)
                        data = await websocket.receive_text()

                        # Send pong response
                        if data == 'ping':
                            await websocket.send_json({
                                'type': 'pong',
                                'timestamp': datetime.utcnow().isoformat(),
                            })

                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f'Detection WebSocket error: {e}')
                        break

            except Exception as e:
                logger.error(f'Detection WebSocket setup error: {e}')
                try:
                    await websocket.close()
                except:
                    pass
            finally:
                # Unregister connection
                await detection_manager.disconnect(connection_id)

        # System Health WebSocket endpoint (register before dynamic '/ws/{user_id}' route)
        @self.app.websocket('/ws/system-health')
        async def system_health_websocket(websocket: WebSocket):
            """
            WebSocket endpoint for real-time system health updates.
            Pushes health status updates to connected clients whenever health checks complete.
            """
            await websocket.accept()
            connection_id = f'health_{int(time.time() * 1000)}'

            # Create a simple connection manager for health updates
            if not hasattr(self, '_health_ws_connections'):
                self._health_ws_connections = {}

            try:
                # Register connection
                self._health_ws_connections[connection_id] = websocket

                # Send welcome message
                await websocket.send_json({
                    'type': 'system',
                    'message': 'Connected to system health monitor',
                    'timestamp': datetime.utcnow().isoformat(),
                })

                # Send initial health status
                from pokertool.system_health_checker import get_health_checker
                checker = get_health_checker()
                summary = checker.get_summary()
                await websocket.send_json({
                    'type': 'health_update',
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': summary
                })

                # Keep connection alive - health updates are broadcast via health checker callback
                while True:
                    try:
                        # Keep alive - receive any client messages (like ping)
                        data = await websocket.receive_text()

                        # Send pong response
                        if data == 'ping':
                            await websocket.send_json({
                                'type': 'pong',
                                'timestamp': datetime.utcnow().isoformat(),
                            })
                        # Send current health status if requested
                        elif data == 'refresh':
                            summary = checker.get_summary()
                            await websocket.send_json({
                                'type': 'health_update',
                                'timestamp': datetime.utcnow().isoformat(),
                                'data': summary
                            })

                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f'System health WebSocket error: {e}')
                        break

            except Exception as e:
                logger.error(f'System health WebSocket setup error: {e}')
                try:
                    await websocket.close()
                except:
                    pass
            finally:
                # Unregister connection
                if connection_id in self._health_ws_connections:
                    del self._health_ws_connections[connection_id]

        # WebSocket endpoint
        @self.app.websocket('/ws/{user_id}')
        async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str):
            # Verify token
            user = self.services.auth_service.verify_token(token)
            if not user or user.user_id != user_id:
                await websocket.close(code=1008, reason='Invalid token')
                return

            connection_id = f'ws_{user_id}_{int(time.time() * 1000)}'

            try:
                await self.services.connection_manager.connect(websocket, connection_id, user_id)

                # Send welcome message
                await self.services.connection_manager.send_personal_message({
                    'type': 'welcome',
                    'message': f'Connected as {user.username}',
                    'connection_id': connection_id
                }, connection_id)

                # Keep connection alive
                while True:
                    try:
                        # Wait for messages from client
                        message = await websocket.receive_json()

                        # Echo back for now (could handle commands)
                        await self.services.connection_manager.send_personal_message({
                            'type': 'echo',
                            'data': message,
                            'timestamp': datetime.utcnow().isoformat()
                        }, connection_id)

                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        logger.error(f'WebSocket error: {e}')
                        break

            finally:
                self.services.connection_manager.disconnect(connection_id, user_id)

        # (moved) System Health WebSocket endpoint is registered earlier to avoid
        # path conflicts with the dynamic '/ws/{user_id}' route.

        # Setup health checker broadcast callback
        async def broadcast_health_update(health_data: Dict):
            """Broadcast health updates to all connected WebSocket clients."""
            if not hasattr(self, '_health_ws_connections'):
                return

            disconnected = []
            for conn_id, ws in self._health_ws_connections.items():
                try:
                    if ws.client_state == WebSocketState.CONNECTED:
                        await ws.send_json({
                            'type': 'health_update',
                            'timestamp': datetime.utcnow().isoformat(),
                            'updates': [status.to_dict() for status in health_data.values()]
                        })
                except Exception as e:
                    logger.error(f'Failed to broadcast health update to {conn_id}: {e}')
                    disconnected.append(conn_id)

            # Clean up disconnected clients
            for conn_id in disconnected:
                if conn_id in self._health_ws_connections:
                    del self._health_ws_connections[conn_id]

        # Set the broadcast callback on the health checker
        from pokertool.system_health_checker import get_health_checker
        health_checker = get_health_checker()
        health_checker.set_broadcast_callback(broadcast_health_update)

# Global API instance
_api_instance: Optional[PokerToolAPI] = None

def get_api() -> PokerToolAPI:
    """Get the global API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = PokerToolAPI()
    return _api_instance

def create_app() -> FastAPI:
    """Create FastAPI application."""
    if not FASTAPI_AVAILABLE:
        raise RuntimeError('FastAPI dependencies not available')

    api = get_api()
    return api.app

# Export app for uvicorn
app = create_app() if FASTAPI_AVAILABLE else None

# CLI runner
def run_api_server(host: str = '127.0.0.1', port: int = 8000, reload: bool = False):
    """Run the API server."""
    if not FASTAPI_AVAILABLE:
        message = 'FastAPI dependencies not available. Install with: pip install -r requirements.txt'
        logger.error(message)
        raise RuntimeError(message)

    try:
        import uvicorn
    except ImportError as exc:
        logger.error("uvicorn not available. Install with: pip install uvicorn")
        raise

    log_level = os.getenv('POKERTOOL_LOG_LEVEL', 'info')

    if reload:
        app_target: Union[str, Callable[..., Any]] = 'pokertool.api:create_app'
        factory = True
    else:
        app_target = create_app()
        factory = False

    logger.info(
        'Starting PokerTool API server on %s:%s (reload=%s, log_level=%s)',
        host,
        port,
        reload,
        log_level,
    )

    config = uvicorn.Config(
        app=app_target,
        host=host,
        port=port,
        reload=reload,
        factory=factory,
        log_level=log_level,
    )
    server = uvicorn.Server(config)
    return server.run()


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point used by the CLI to start the API server."""
    host = os.getenv('POKERTOOL_HOST', '127.0.0.1')
    port = int(os.getenv('POKERTOOL_PORT', '8000'))
    reload_flag = os.getenv('POKERTOOL_RELOAD', '').lower() in {'1', 'true', 'yes'}

    try:
        run_api_server(host=host, port=port, reload=reload_flag)
    except RuntimeError:
        return 1
    except Exception:  # pragma: no cover - defensive guard for CLI usage
        logger.exception('PokerTool API server crashed during startup')
        return 1

    return 0


# Backwards compatibility alias for older CLI integrations
run = main

if __name__ == '__main__':
    raise SystemExit(main())
