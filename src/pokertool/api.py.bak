# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/pokertool/api.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
RESTful API Module
Provides HTTP API endpoints for external integration with authentication, 
rate limiting, and WebSocket support for real-time updates.
"""

import json
import time
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from functools import wraps

# Try to import FastAPI dependencies
try:
    from fastapi import FastAPI, HTTPException, Depends, Security, WebSocket, WebSocketDisconnect, BackgroundTasks
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

from .production_database import get_production_db, ProductionDatabase, DatabaseConfig, initialize_production_db
from .scrape import get_scraper_status, run_screen_scraper, stop_screen_scraper
from .threading import get_thread_pool, TaskPriority, get_poker_concurrency_manager
from .error_handling import SecurityError, retry_on_failure
from .hud_overlay import start_hud_overlay, stop_hud_overlay, update_hud_state, is_hud_running

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

    class UserCreate(BaseModel):
        """User creation model."""
        username: str = Field(..., min_length=3, max_length=50)
        email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
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
        """Verify and decode JWT token."""
        try:
            if not jwt:
                # Fallback verification
                user_id = self.sessions.get(token)
                if user_id:
                    user = self.users.get(user_id)
                    if user and user.is_active:
                        user.last_active = datetime.utcnow()
                        return user
                return None

            payload = jwt.decode(token, API_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('sub')

            if user_id not in self.users:
                return None

            user = self.users[user_id]
            if not user.is_active:
                return None

            user.last_active = datetime.utcnow()
            return user

        except Exception:
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

class APIServices:
    """Container for API services with dependency injection."""
    
    def __init__(self):
        self.auth_service = AuthenticationService()
        self.connection_manager = ConnectionManager()
        self.db = get_production_db()
        self.thread_pool = get_thread_pool()
        
        # Setup rate limiter with fallback
        try:
            self.limiter = Limiter(key_func=get_remote_address, storage_url=RATE_LIMIT_STORAGE_URL)
        except Exception:
            self.limiter = Limiter(key_func=get_remote_address)
        
        # Cache for frequently accessed data
        self._user_cache = {}
        self._cache_ttl = 300  # 5 minutes

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
            description='RESTful API for poker analysis and screen scraping',
            version='1.0.0'
        )

        self._setup_middleware()
        self._setup_routes()
        self._setup_background_tasks()

        logger.info('PokerTool API initialized with optimized architecture')

    def _setup_background_tasks(self):
        """Setup background cleanup tasks."""
        import asyncio
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            cleanup_task = asyncio.create_task(self._periodic_cleanup())
            yield
            # Shutdown
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

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
        self.app.add_middleware(SlowAPIMiddleware)
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],  # In production, specify actual origins
            allow_credentials=True,
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
        @self.app.get('/health')
        async def health_check():
            return {'status': 'healthy', 'timestamp': datetime.utcnow()}

        # Authentication endpoints
        @self.app.post('/auth/token', response_model=Token)
        @self.services.limiter.limit('10/minute')
        async def login(request, username: str, password: str):
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

        # Database endpoints
        @self.app.get('/hands/recent')
        @self.services.limiter.limit('50/minute')
        async def get_recent_hands(limit: int = 10, offset: int = 0, 
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
            thread_stats = self.services.thread_pool.get_stats()
            db_stats = self.services.db.get_database_stats()

            return {
                'threading': thread_stats,
                'database': db_stats,
                'websockets': {
                    'active_connections': len(self.services.connection_manager.active_connections),
                    'users_connected': len(self.services.connection_manager.user_connections)
                },
                'api': {
                    'total_users': len(self.services.auth_service.users),
                    'active_sessions': len(self.services.auth_service.sessions)
                }
            }

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

# CLI runner
def run_api_server(host: str = '127.0.0.1', port: int = 8000, reload: bool = False):
    """Run the API server."""
    try:
        import uvicorn
        app = create_app()

        logger.info(f'Starting PokerTool API server on {host}:{port}')
        uvicorn.run('src.pokertool.api:create_app', host=host, port=port, reload=reload, factory=True)

    except ImportError:
        logger.error("uvicorn not available. Install with: pip install uvicorn")
        raise

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        run_api_server(reload=True)
    else:
        # Test basic functionality
        if FASTAPI_AVAILABLE:
            api = get_api()
            print(f"API created with {len(api.auth_service.users)} users")
            print('Default admin token available for testing')
        else:
            print('FastAPI dependencies not available')
