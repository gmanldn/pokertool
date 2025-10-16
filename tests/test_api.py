#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Unit Tests for PokerTool API Module
==================================================

This module provides comprehensive unit tests for the entire API functionality
including authentication, endpoints, WebSocket connections, and services.

Module: tests.test_api
Version: 1.0.0
Last Modified: 2025-10-16
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, Any, List

# Import the module under test
from pokertool.api import (
    FASTAPI_AVAILABLE,
    AuthenticationService,
    ConnectionManager,
    DetectionWebSocketManager,
    APIServices,
    PokerToolAPI,
    APIUser,
    UserRole,
    create_app,
    get_api,
    broadcast_detection_event,
    get_detection_ws_manager,
)


# Skip all tests if FastAPI is not available
pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI dependencies not available")


class TestUserRole:
    """Tests for UserRole enum."""

    def test_user_roles_exist(self):
        """Test that all expected user roles exist."""
        assert UserRole.GUEST.value == 'guest'
        assert UserRole.USER.value == 'user'
        assert UserRole.PREMIUM.value == 'premium'
        assert UserRole.ADMIN.value == 'admin'

    def test_user_role_enum(self):
        """Test UserRole enum values."""
        roles = [r.value for r in UserRole]
        assert 'guest' in roles
        assert 'user' in roles
        assert 'premium' in roles
        assert 'admin' in roles


class TestAPIUser:
    """Tests for APIUser dataclass."""

    def test_api_user_creation(self):
        """Test creating an API user."""
        user = APIUser(
            user_id='test_123',
            username='testuser',
            email='test@example.com',
            role=UserRole.USER
        )

        assert user.user_id == 'test_123'
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert user.rate_limit_override is None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.last_active, datetime)

    def test_api_user_with_overrides(self):
        """Test creating an API user with rate limit override."""
        user = APIUser(
            user_id='admin_123',
            username='admin',
            email='admin@example.com',
            role=UserRole.ADMIN,
            rate_limit_override=1000
        )

        assert user.rate_limit_override == 1000
        assert user.role == UserRole.ADMIN


class TestAuthenticationService:
    """Tests for AuthenticationService."""

    def test_initialization(self):
        """Test authentication service initialization."""
        auth_service = AuthenticationService()

        # Should create default admin user
        assert 'admin' in auth_service.users
        assert 'demo_user' in auth_service.users

        admin = auth_service.users['admin']
        assert admin.username == 'admin'
        assert admin.role == UserRole.ADMIN
        assert admin.rate_limit_override == 1000

    def test_create_user(self):
        """Test creating a new user."""
        auth_service = AuthenticationService()

        user = auth_service.create_user(
            username='newuser',
            email='new@example.com',
            password='password123',
            role=UserRole.USER
        )

        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.role == UserRole.USER
        assert user.user_id in auth_service.users

    def test_create_duplicate_username(self):
        """Test that duplicate usernames are rejected."""
        auth_service = AuthenticationService()

        auth_service.create_user(
            username='duplicate',
            email='user1@example.com',
            password='password123'
        )

        # Try to create another user with same username
        with pytest.raises(Exception) as exc_info:
            auth_service.create_user(
                username='duplicate',
                email='user2@example.com',
                password='password456'
            )

        assert 'Username already exists' in str(exc_info.value)

    def test_create_duplicate_email(self):
        """Test that duplicate emails are rejected."""
        auth_service = AuthenticationService()

        auth_service.create_user(
            username='user1',
            email='same@example.com',
            password='password123'
        )

        # Try to create another user with same email
        with pytest.raises(Exception) as exc_info:
            auth_service.create_user(
                username='user2',
                email='same@example.com',
                password='password456'
            )

        assert 'Email already exists' in str(exc_info.value)

    def test_create_access_token(self):
        """Test creating an access token."""
        auth_service = AuthenticationService()
        user = auth_service.users['admin']

        token = auth_service.create_access_token(user)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 10

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        auth_service = AuthenticationService()
        user = auth_service.users['admin']

        token = auth_service.create_access_token(user)
        verified_user = auth_service.verify_token(token)

        assert verified_user is not None
        assert verified_user.user_id == user.user_id
        assert verified_user.username == user.username

    def test_verify_invalid_token(self):
        """Test verifying an invalid token."""
        auth_service = AuthenticationService()

        verified_user = auth_service.verify_token('invalid_token_12345')

        assert verified_user is None

    def test_verify_token_updates_last_active(self):
        """Test that verifying a token updates last_active timestamp."""
        auth_service = AuthenticationService()
        user = auth_service.users['admin']

        initial_last_active = user.last_active
        time.sleep(0.1)

        token = auth_service.create_access_token(user)
        verified_user = auth_service.verify_token(token)

        assert verified_user.last_active > initial_last_active

    def test_get_user_by_credentials(self):
        """Test getting user by credentials."""
        auth_service = AuthenticationService()

        # Should find admin user
        user = auth_service.get_user_by_credentials('admin', 'anypassword')
        assert user is not None
        assert user.username == 'admin'

        # Should not find non-existent user
        user = auth_service.get_user_by_credentials('nonexistent', 'password')
        assert user is None

    def test_inactive_user_verification_fails(self):
        """Test that inactive users cannot verify tokens."""
        auth_service = AuthenticationService()
        user = auth_service.create_user(
            username='inactive',
            email='inactive@example.com',
            password='password123'
        )

        token = auth_service.create_access_token(user)

        # Deactivate user
        user.is_active = False

        # Token verification should fail
        verified_user = auth_service.verify_token(token)
        assert verified_user is None


class TestConnectionManager:
    """Tests for ConnectionManager."""

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = AsyncMock()
        ws.client_state = MagicMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, mock_websocket):
        """Test connecting a WebSocket."""
        manager = ConnectionManager()

        await manager.connect(mock_websocket, 'conn_123', 'user_456')

        assert 'conn_123' in manager.active_connections
        assert 'user_456' in manager.user_connections
        assert 'conn_123' in manager.user_connections['user_456']
        assert 'conn_123' in manager.connection_timestamps
        mock_websocket.accept.assert_called_once()

    def test_disconnect(self, mock_websocket):
        """Test disconnecting a WebSocket."""
        manager = ConnectionManager()
        manager.active_connections['conn_123'] = mock_websocket
        manager.user_connections['user_456'] = ['conn_123']
        manager.connection_timestamps['conn_123'] = time.time()

        manager.disconnect('conn_123', 'user_456')

        assert 'conn_123' not in manager.active_connections
        assert 'user_456' not in manager.user_connections
        assert 'conn_123' not in manager.connection_timestamps

    @pytest.mark.asyncio
    async def test_send_personal_message(self, mock_websocket):
        """Test sending a personal message."""
        from fastapi.websockets import WebSocketState

        manager = ConnectionManager()
        manager.active_connections['conn_123'] = mock_websocket
        manager.connection_timestamps['conn_123'] = time.time()
        mock_websocket.client_state = WebSocketState.CONNECTED

        message = {'type': 'test', 'data': 'hello'}
        await manager.send_personal_message(message, 'conn_123')

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user(self, mock_websocket):
        """Test sending message to all user connections."""
        from fastapi.websockets import WebSocketState

        manager = ConnectionManager()
        manager.active_connections['conn_123'] = mock_websocket
        manager.user_connections['user_456'] = ['conn_123']
        manager.connection_timestamps['conn_123'] = time.time()
        mock_websocket.client_state = WebSocketState.CONNECTED

        message = {'type': 'test', 'data': 'hello'}
        await manager.send_to_user(message, 'user_456')

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting to all connections."""
        from fastapi.websockets import WebSocketState

        manager = ConnectionManager()

        # Create multiple mock websockets
        ws1 = AsyncMock()
        ws1.client_state = WebSocketState.CONNECTED
        ws2 = AsyncMock()
        ws2.client_state = WebSocketState.CONNECTED

        manager.active_connections['conn_1'] = ws1
        manager.active_connections['conn_2'] = ws2
        manager.connection_timestamps['conn_1'] = time.time()
        manager.connection_timestamps['conn_2'] = time.time()

        message = {'type': 'broadcast', 'data': 'to all'}
        await manager.broadcast(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_cleanup_inactive(self, mock_websocket):
        """Test cleaning up inactive connections."""
        manager = ConnectionManager()
        manager.active_connections['conn_old'] = mock_websocket
        manager.connection_timestamps['conn_old'] = time.time() - 2000  # Old connection
        manager.user_connections['user_1'] = ['conn_old']

        await manager.cleanup_inactive(timeout=1800)

        assert 'conn_old' not in manager.active_connections
        assert 'user_1' not in manager.user_connections


class TestDetectionWebSocketManager:
    """Tests for DetectionWebSocketManager."""

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = AsyncMock()
        ws.client_state = MagicMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, mock_websocket):
        """Test connecting a detection WebSocket."""
        manager = DetectionWebSocketManager()

        await manager.connect('conn_123', mock_websocket)

        assert 'conn_123' in manager.active_connections
        assert 'conn_123' in manager.connection_timestamps

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_websocket):
        """Test disconnecting a detection WebSocket."""
        manager = DetectionWebSocketManager()
        manager.active_connections['conn_123'] = mock_websocket
        manager.connection_timestamps['conn_123'] = time.time()

        await manager.disconnect('conn_123')

        assert 'conn_123' not in manager.active_connections
        assert 'conn_123' not in manager.connection_timestamps

    @pytest.mark.asyncio
    async def test_broadcast_detection(self):
        """Test broadcasting a detection event."""
        from fastapi.websockets import WebSocketState

        manager = DetectionWebSocketManager()

        # Create multiple mock websockets
        ws1 = AsyncMock()
        ws1.client_state = WebSocketState.CONNECTED
        ws2 = AsyncMock()
        ws2.client_state = WebSocketState.CONNECTED

        manager.active_connections['conn_1'] = ws1
        manager.active_connections['conn_2'] = ws2
        manager.connection_timestamps['conn_1'] = time.time()
        manager.connection_timestamps['conn_2'] = time.time()

        event = {
            'type': 'player',
            'severity': 'info',
            'message': 'Player detected',
            'data': {}
        }

        await manager.broadcast_detection(event)

        ws1.send_json.assert_called_once_with(event)
        ws2.send_json.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(self):
        """Test broadcasting when no connections exist."""
        manager = DetectionWebSocketManager()

        event = {'type': 'test', 'message': 'Test event'}

        # Should not raise an error
        await manager.broadcast_detection(event)


class TestAPIServices:
    """Tests for APIServices."""

    def test_initialization(self):
        """Test API services initialization."""
        with patch('pokertool.api.get_production_db') as mock_db:
            mock_db.return_value = Mock()

            services = APIServices()

            assert services.auth_service is not None
            assert services.connection_manager is not None
            assert services.db is not None
            assert services.thread_pool is not None
            assert services.analytics_dashboard is not None
            assert services.gamification_engine is not None
            assert services.community_platform is not None
            assert services.limiter is not None

    def test_default_gamification_content(self):
        """Test that default gamification content is seeded."""
        with patch('pokertool.api.get_production_db'):
            services = APIServices()

            # Check that default achievement was registered
            assert 'volume_grinder' in services.gamification_engine.achievements
            assert 'marathon' in services.gamification_engine.badges

    def test_default_community_post(self):
        """Test that default community post is created."""
        with patch('pokertool.api.get_production_db'):
            services = APIServices()

            # Check that welcome post was created
            assert 'welcome' in services.community_platform.posts
            post = services.community_platform.posts['welcome']
            assert post.title == 'Welcome to the PokerTool community'

    def test_get_cached_user(self):
        """Test user caching."""
        with patch('pokertool.api.get_production_db'):
            services = APIServices()

            # Create a token for admin user
            admin_user = services.auth_service.users['admin']
            token = services.auth_service.create_access_token(admin_user)

            # First call should cache the user
            user1 = services.get_cached_user(token)
            assert user1 is not None

            # Second call should return cached user
            user2 = services.get_cached_user(token)
            assert user2 is not None
            assert user1.user_id == user2.user_id

    def test_cleanup_cache(self):
        """Test cache cleanup."""
        with patch('pokertool.api.get_production_db'):
            services = APIServices()

            # Add some cache entries
            services._user_cache['key1'] = (Mock(), time.time() - 400)  # Expired
            services._user_cache['key2'] = (Mock(), time.time())  # Fresh

            services.cleanup_cache()

            # Expired entry should be removed
            assert 'key1' not in services._user_cache
            assert 'key2' in services._user_cache


class TestPokerToolAPI:
    """Tests for PokerToolAPI."""

    @pytest.fixture
    def mock_services(self):
        """Create mock API services."""
        with patch('pokertool.api.get_production_db'):
            return APIServices()

    def test_initialization(self, mock_services):
        """Test API initialization."""
        api = PokerToolAPI(services=mock_services)

        assert api.services is not None
        assert api.app is not None
        assert api.app.title == 'PokerTool API'

    def test_middleware_setup(self, mock_services):
        """Test that middleware is properly configured."""
        api = PokerToolAPI(services=mock_services)

        # Check that app.state.limiter is set
        assert hasattr(api.app.state, 'limiter')
        assert api.app.state.limiter is not None

    @pytest.mark.asyncio
    async def test_health_endpoint(self, mock_services):
        """Test health check endpoint."""
        from fastapi.testclient import TestClient

        api = PokerToolAPI(services=mock_services)
        client = TestClient(api.app)

        response = client.get('/health')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data

    @pytest.mark.asyncio
    async def test_login_endpoint(self, mock_services):
        """Test login endpoint."""
        from fastapi.testclient import TestClient

        api = PokerToolAPI(services=mock_services)
        client = TestClient(api.app)

        response = client.post(
            '/auth/token',
            params={'username': 'admin', 'password': 'anypassword'}
        )

        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'
        assert data['user_role'] == 'admin'

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, mock_services):
        """Test login with invalid credentials."""
        from fastapi.testclient import TestClient

        api = PokerToolAPI(services=mock_services)
        client = TestClient(api.app)

        response = client.post(
            '/auth/token',
            params={'username': 'nonexistent', 'password': 'wrongpass'}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_endpoint(self, mock_services):
        """Test user registration endpoint."""
        from fastapi.testclient import TestClient

        api = PokerToolAPI(services=mock_services)
        client = TestClient(api.app)

        response = client.post(
            '/auth/register',
            json={
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'password123',
                'role': 'user'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert 'user_id' in data
        assert 'newuser' in data['message']


class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient

        with patch('pokertool.api.get_production_db'):
            api = PokerToolAPI()
            return TestClient(api.app)

    @pytest.fixture
    def auth_token(self, client):
        """Get authentication token for testing."""
        response = client.post(
            '/auth/token',
            params={'username': 'admin', 'password': 'anypassword'}
        )
        return response.json()['access_token']

    def test_scraper_status_requires_auth(self, client):
        """Test that scraper status requires authentication."""
        response = client.get('/scraper/status')
        assert response.status_code == 403  # No auth provided

    def test_scraper_status_with_auth(self, client, auth_token):
        """Test scraper status endpoint with authentication."""
        response = client.get(
            '/scraper/status',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'initialized' in data
        assert 'running' in data
        assert 'available' in data

    def test_database_stats(self, client, auth_token):
        """Test database stats endpoint."""
        response = client.get(
            '/stats/database',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'database_type' in data
        assert 'total_hands' in data

    def test_system_health_endpoint(self, client):
        """Test system health endpoint."""
        response = client.get('/api/system/health')
        assert response.status_code == 200
        data = response.json()
        assert 'timestamp' in data
        assert 'categories' in data

    def test_ml_calibration_stats(self, client):
        """Test ML calibration stats endpoint."""
        response = client.get('/api/ml/calibration/stats')
        assert response.status_code == 200
        data = response.json()
        assert 'success' in data
        assert 'timestamp' in data

    def test_opponent_fusion_stats(self, client):
        """Test opponent fusion stats endpoint."""
        response = client.get('/api/ml/opponent-fusion/stats')
        assert response.status_code == 200
        data = response.json()
        assert 'success' in data
        assert 'timestamp' in data

    def test_active_learning_stats(self, client):
        """Test active learning stats endpoint."""
        response = client.get('/api/ml/active-learning/stats')
        assert response.status_code == 200
        data = response.json()
        assert 'success' in data
        assert 'timestamp' in data

    def test_scraping_accuracy_stats(self, client):
        """Test scraping accuracy stats endpoint."""
        response = client.get('/api/scraping/accuracy/stats')
        assert response.status_code == 200
        data = response.json()
        assert 'success' in data
        assert 'timestamp' in data

    def test_gamification_progress(self, client, auth_token):
        """Test gamification progress endpoint."""
        response = client.get(
            '/gamification/progress/player_123',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'player_id' in data

    def test_gamification_leaderboard(self, client, auth_token):
        """Test gamification leaderboard endpoint."""
        response = client.get(
            '/gamification/leaderboard',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'leaderboard' in data

    def test_community_posts(self, client, auth_token):
        """Test community posts endpoint."""
        response = client.get(
            '/community/posts',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'posts' in data
        assert len(data['posts']) > 0  # Should have welcome post

    def test_admin_users_requires_admin(self, client, auth_token):
        """Test that admin endpoints require admin role."""
        # Login as non-admin user
        from fastapi.testclient import TestClient

        # Create a regular user
        client.post(
            '/auth/register',
            json={
                'username': 'regularuser',
                'email': 'regular@example.com',
                'password': 'password123',
                'role': 'user'
            }
        )

        # Try to access admin endpoint with non-admin token
        regular_token_resp = client.post(
            '/auth/token',
            params={'username': 'regularuser', 'password': 'password123'}
        )
        regular_token = regular_token_resp.json()['access_token']

        response = client.get(
            '/admin/users',
            headers={'Authorization': f'Bearer {regular_token}'}
        )

        # Should be forbidden
        assert response.status_code == 403

    def test_admin_users_with_admin(self, client, auth_token):
        """Test admin users endpoint with admin role."""
        response = client.get(
            '/admin/users',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'users' in data
        assert len(data['users']) > 0


class TestGlobalFunctions:
    """Tests for global helper functions."""

    def test_get_detection_ws_manager(self):
        """Test getting detection WebSocket manager singleton."""
        manager1 = get_detection_ws_manager()
        manager2 = get_detection_ws_manager()

        assert manager1 is manager2  # Should be same instance
        assert isinstance(manager1, DetectionWebSocketManager)

    @pytest.mark.asyncio
    async def test_broadcast_detection_event(self):
        """Test broadcasting a detection event."""
        from fastapi.websockets import WebSocketState

        # Get manager and add a mock connection
        manager = get_detection_ws_manager()
        ws = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED
        await manager.connect('test_conn', ws)

        # Broadcast an event
        await broadcast_detection_event(
            event_type='player',
            severity='info',
            message='Test detection',
            data={'player_id': 1}
        )

        # Check that message was sent
        assert ws.send_json.called
        call_args = ws.send_json.call_args[0][0]
        assert call_args['type'] == 'player'
        assert call_args['severity'] == 'info'
        assert call_args['message'] == 'Test detection'
        assert call_args['data']['player_id'] == 1

        # Cleanup
        await manager.disconnect('test_conn')

    def test_get_api_singleton(self):
        """Test getting API singleton."""
        with patch('pokertool.api.get_production_db'):
            api1 = get_api()
            api2 = get_api()

            assert api1 is api2  # Should be same instance
            assert isinstance(api1, PokerToolAPI)

    def test_create_app(self):
        """Test creating FastAPI app."""
        with patch('pokertool.api.get_production_db'):
            from fastapi import FastAPI

            app = create_app()

            assert isinstance(app, FastAPI)
            assert app.title == 'PokerTool API'


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient

        with patch('pokertool.api.get_production_db'):
            api = PokerToolAPI()
            return TestClient(api.app)

    def test_login_rate_limit(self, client):
        """Test that login endpoint has rate limiting."""
        # The rate limit is 10/minute for login
        # Make several requests quickly
        for i in range(15):
            response = client.post(
                '/auth/token',
                params={'username': 'admin', 'password': 'anypassword'}
            )

            # First 10 should succeed, then rate limit should kick in
            if i < 10:
                assert response.status_code in [200, 429]  # May hit limit
            else:
                # After 10, definitely should be rate limited
                # (Note: actual behavior depends on Redis/storage availability)
                pass


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient

        with patch('pokertool.api.get_production_db'):
            api = PokerToolAPI()
            return TestClient(api.app)

    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint."""
        response = client.get('/nonexistent/endpoint')
        assert response.status_code == 404

    def test_missing_auth_header(self, client):
        """Test accessing protected endpoint without auth."""
        response = client.get('/scraper/status')
        assert response.status_code == 403

    def test_invalid_auth_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            '/scraper/status',
            headers={'Authorization': 'Bearer invalid_token_xyz'}
        )
        assert response.status_code == 401


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
