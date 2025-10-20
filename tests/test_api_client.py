#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite for API Client Library
==================================

Comprehensive tests for PokerTool API client with retry logic, authentication, and error handling.

Module: tests.test_api_client
Version: 1.0.0
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
import requests
from requests.exceptions import ConnectionError, Timeout

from pokertool.api_client import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    HandAnalysisRequest,
    HandAnalysisResponse,
    PokerToolClient
)


class TestAPIExceptions:
    """Test API exception classes."""

    def test_api_error_creation(self):
        """Test creating API error with message and status code."""
        error = APIError("Test error", status_code=500, response_data={"detail": "Server error"})

        assert str(error) == "Test error"
        assert error.status_code == 500
        assert error.response_data == {"detail": "Server error"}

    def test_authentication_error_inherits_from_api_error(self):
        """Test AuthenticationError inherits from APIError."""
        error = AuthenticationError("Auth failed", status_code=401)

        assert isinstance(error, APIError)
        assert error.status_code == 401

    def test_rate_limit_error_inherits_from_api_error(self):
        """Test RateLimitError inherits from APIError."""
        error = RateLimitError("Too many requests", status_code=429)

        assert isinstance(error, APIError)
        assert error.status_code == 429

    def test_validation_error_inherits_from_api_error(self):
        """Test ValidationError inherits from APIError."""
        error = ValidationError("Invalid input", status_code=422)

        assert isinstance(error, APIError)
        assert error.status_code == 422


class TestHandAnalysisModels:
    """Test request and response models."""

    def test_hand_analysis_request_creation(self):
        """Test creating hand analysis request."""
        request = HandAnalysisRequest(
            hole_cards=["As", "Kh"],
            community_cards=["Qh", "Jd", "Tc"],
            pot_size=100.0,
            stack_size=1000.0,
            position="button",
            num_players=6,
            street="flop"
        )

        assert request.hole_cards == ["As", "Kh"]
        assert request.community_cards == ["Qh", "Jd", "Tc"]
        assert request.pot_size == 100.0
        assert request.stack_size == 1000.0
        assert request.position == "button"
        assert request.num_players == 6
        assert request.street == "flop"

    def test_hand_analysis_response_creation(self):
        """Test creating hand analysis response."""
        response = HandAnalysisResponse(
            recommendation="raise",
            confidence=0.85,
            equity=0.65,
            expected_value=25.5,
            hand_strength="strong",
            reasoning="You have a strong straight draw",
            alternative_actions=[{"action": "call", "ev": 20.0}]
        )

        assert response.recommendation == "raise"
        assert response.confidence == 0.85
        assert response.equity == 0.65
        assert response.expected_value == 25.5
        assert response.hand_strength == "strong"
        assert response.reasoning == "You have a strong straight draw"
        assert len(response.alternative_actions) == 1


class TestPokerToolClientInitialization:
    """Test API client initialization."""

    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key."""
        client = PokerToolClient(
            base_url="http://localhost:5001",
            api_key="test-api-key-123"
        )

        assert client.base_url == "http://localhost:5001"
        assert client.api_key == "test-api-key-123"
        assert client.session.headers['X-API-Key'] == "test-api-key-123"

    def test_client_initialization_with_username_password(self):
        """Test client initialization with username and password."""
        client = PokerToolClient(
            base_url="http://localhost:5001",
            username="testuser",
            password="testpass"
        )

        assert client.username == "testuser"
        assert client.password == "testpass"

    def test_client_initialization_defaults(self):
        """Test client initialization with default values."""
        client = PokerToolClient()

        assert client.base_url == "http://localhost:5001"
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.retry_delay == 1.0

    def test_client_initialization_custom_settings(self):
        """Test client initialization with custom settings."""
        client = PokerToolClient(
            base_url="https://api.example.com",
            timeout=60,
            max_retries=5,
            retry_delay=2.0
        )

        assert client.base_url == "https://api.example.com"
        assert client.timeout == 60
        assert client.max_retries == 5
        assert client.retry_delay == 2.0

    def test_base_url_trailing_slash_removed(self):
        """Test trailing slash is removed from base URL."""
        client = PokerToolClient(base_url="http://localhost:5001/")

        assert client.base_url == "http://localhost:5001"


class TestPokerToolClientAuthentication:
    """Test API client authentication."""

    @patch('pokertool.api_client.PokerToolClient._request_with_retry')
    def test_authenticate_success(self, mock_request):
        """Test successful authentication."""
        mock_request.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token'
        }

        client = PokerToolClient(username="testuser", password="testpass")
        result = client.authenticate()

        assert result is True
        assert client.access_token == 'test_access_token'
        assert client.refresh_token == 'test_refresh_token'

        mock_request.assert_called_once_with(
            'POST',
            '/auth/login',
            json={'username': 'testuser', 'password': 'testpass'}
        )

    def test_authenticate_without_credentials_raises_error(self):
        """Test authentication without credentials raises error."""
        client = PokerToolClient()

        with pytest.raises(AuthenticationError, match="Username and password required"):
            client.authenticate()

    @patch('pokertool.api_client.PokerToolClient._request_with_retry')
    def test_authenticate_failure_raises_error(self, mock_request):
        """Test authentication failure raises error."""
        mock_request.side_effect = APIError("Authentication failed", status_code=401)

        client = PokerToolClient(username="testuser", password="wrongpass")

        with pytest.raises(AuthenticationError):
            client.authenticate()


class TestPokerToolClientRequests:
    """Test API client request handling."""

    @patch('pokertool.api_client.requests.Session.request')
    def test_successful_request(self, mock_request):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response

        client = PokerToolClient()
        result = client._request_with_retry('GET', '/health')

        assert result == {"status": "ok"}
        mock_request.assert_called_once()

    @patch('pokertool.api_client.requests.Session.request')
    def test_request_with_authentication_header(self, mock_request):
        """Test request includes authentication header."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response

        client = PokerToolClient()
        client.access_token = "test_token"

        client._request_with_retry('GET', '/test')

        # Check that Authorization header was added
        call_args = mock_request.call_args
        headers = call_args.kwargs['headers']
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer test_token'

    @patch('pokertool.api_client.requests.Session.request')
    def test_request_timeout_setting(self, mock_request):
        """Test request uses configured timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response

        client = PokerToolClient(timeout=60)
        client._request_with_retry('GET', '/test')

        call_args = mock_request.call_args
        assert call_args.kwargs['timeout'] == 60

    @patch('pokertool.api_client.requests.Session.request')
    def test_request_retry_on_connection_error(self, mock_request):
        """Test request retries on connection error."""
        # First two attempts fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}

        mock_request.side_effect = [
            ConnectionError("Connection failed"),
            ConnectionError("Connection failed"),
            mock_response
        ]

        client = PokerToolClient(max_retries=3, retry_delay=0.1)

        result = client._request_with_retry('GET', '/test')

        assert result == {"status": "ok"}
        assert mock_request.call_count == 3

    @patch('pokertool.api_client.requests.Session.request')
    def test_request_retry_with_exponential_backoff(self, mock_request):
        """Test request uses exponential backoff."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}

        mock_request.side_effect = [
            Timeout("Request timeout"),
            Timeout("Request timeout"),
            mock_response
        ]

        client = PokerToolClient(max_retries=3, retry_delay=0.1)

        start_time = time.time()
        result = client._request_with_retry('GET', '/test')
        duration = time.time() - start_time

        # Should have delays: 0.1s, 0.2s (exponential)
        # Total should be at least 0.3s
        assert duration >= 0.3
        assert result == {"status": "ok"}

    @patch('pokertool.api_client.requests.Session.request')
    def test_request_exhausts_retries_raises_error(self, mock_request):
        """Test request raises error after exhausting retries."""
        mock_request.side_effect = ConnectionError("Connection failed")

        client = PokerToolClient(max_retries=3, retry_delay=0.1)

        with pytest.raises(APIError, match="Request failed after 3 attempts"):
            client._request_with_retry('GET', '/test')

        assert mock_request.call_count == 3


class TestPokerToolClientErrorHandling:
    """Test API client error handling."""

    @patch('pokertool.api_client.requests.Session.request')
    def test_handle_401_authentication_error(self, mock_request):
        """Test handling of 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Unauthorized"}
        mock_request.return_value = mock_response

        client = PokerToolClient()

        with pytest.raises(AuthenticationError) as exc_info:
            client._request_with_retry('GET', '/test')

        assert exc_info.value.status_code == 401

    @patch('pokertool.api_client.requests.Session.request')
    def test_handle_429_rate_limit_error(self, mock_request):
        """Test handling of 429 rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"detail": "Too many requests"}
        mock_request.return_value = mock_response

        client = PokerToolClient(max_retries=1)

        with pytest.raises(RateLimitError) as exc_info:
            client._request_with_retry('GET', '/test')

        assert exc_info.value.status_code == 429

    @patch('pokertool.api_client.requests.Session.request')
    def test_handle_422_validation_error(self, mock_request):
        """Test handling of 422 validation error."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": "Validation failed"}
        mock_request.return_value = mock_response

        client = PokerToolClient()

        with pytest.raises(ValidationError) as exc_info:
            client._request_with_retry('GET', '/test')

        assert exc_info.value.status_code == 422
        assert "Validation failed" in str(exc_info.value)

    @patch('pokertool.api_client.requests.Session.request')
    def test_handle_generic_error(self, mock_request):
        """Test handling of generic API error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_request.return_value = mock_response

        client = PokerToolClient()

        with pytest.raises(APIError) as exc_info:
            client._request_with_retry('GET', '/test')

        assert exc_info.value.status_code == 500


class TestPokerToolClientAPIEndpoints:
    """Test API client endpoint methods."""

    @patch('pokertool.api_client.PokerToolClient._request_with_retry')
    def test_analyze_hand(self, mock_request):
        """Test analyze_hand endpoint."""
        mock_request.return_value = {
            'recommendation': 'raise',
            'confidence': 0.85,
            'equity': 0.65,
            'expected_value': 25.5,
            'hand_strength': 'strong',
            'reasoning': 'You have a strong straight draw',
            'alternative_actions': [{'action': 'call', 'ev': 20.0}]
        }

        client = PokerToolClient()
        result = client.analyze_hand(
            hole_cards=["As", "Kh"],
            community_cards=["Qh", "Jd", "Tc"],
            pot_size=100.0,
            stack_size=1000.0,
            position="button",
            num_players=6,
            street="flop"
        )

        assert isinstance(result, HandAnalysisResponse)
        assert result.recommendation == 'raise'
        assert result.confidence == 0.85
        assert result.equity == 0.65

        # Verify request was made with correct payload
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        payload = call_args.kwargs['json']
        assert payload['hole_cards'] == ["As", "Kh"]
        assert payload['pot_size'] == 100.0

    @patch('pokertool.api_client.PokerToolClient._request_with_retry')
    def test_get_health(self, mock_request):
        """Test get_health endpoint."""
        mock_request.return_value = {"status": "healthy", "version": "1.0.0"}

        client = PokerToolClient()
        result = client.get_health()

        assert result["status"] == "healthy"
        mock_request.assert_called_once_with('GET', '/health')

    @patch('pokertool.api_client.PokerToolClient._request_with_retry')
    def test_get_statistics(self, mock_request):
        """Test get_statistics endpoint."""
        mock_request.return_value = {
            "hands_played": 1000,
            "win_rate": 0.55
        }

        client = PokerToolClient()
        result = client.get_statistics(user_id="user123")

        assert result["hands_played"] == 1000
        mock_request.assert_called_once_with('GET', '/statistics', params={'user_id': 'user123'})

    @patch('pokertool.api_client.PokerToolClient._request_with_retry')
    def test_get_hand_history(self, mock_request):
        """Test get_hand_history endpoint."""
        mock_request.return_value = {
            "hands": [{"id": 1}, {"id": 2}],
            "total": 2
        }

        client = PokerToolClient()
        result = client.get_hand_history(limit=100, offset=0)

        assert len(result["hands"]) == 2
        mock_request.assert_called_once()


class TestPokerToolClientContextManager:
    """Test API client as context manager."""

    def test_context_manager_usage(self):
        """Test client can be used as context manager."""
        with PokerToolClient() as client:
            assert client.session is not None

        # Session should be closed after context exit
        # (In real implementation, session.close() would be called)

    @patch('pokertool.api_client.requests.Session.close')
    def test_context_manager_closes_session(self, mock_close):
        """Test context manager closes session on exit."""
        with PokerToolClient() as client:
            pass

        mock_close.assert_called_once()


class TestPokerToolClientEdgeCases:
    """Test edge cases and error scenarios."""

    @patch('pokertool.api_client.requests.Session.request')
    def test_request_with_non_json_response(self, mock_request):
        """Test handling of non-JSON response."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response

        client = PokerToolClient()

        with pytest.raises(APIError) as exc_info:
            client._request_with_retry('GET', '/test')

        # Should handle non-JSON response gracefully
        assert exc_info.value.status_code == 500

    @patch('pokertool.api_client.requests.Session.request')
    def test_client_error_no_retry(self, mock_request):
        """Test client errors (4xx) don't retry except rate limiting."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}
        mock_request.return_value = mock_response

        client = PokerToolClient(max_retries=3)

        with pytest.raises(APIError):
            client._request_with_retry('GET', '/test')

        # Should only be called once (no retry for 4xx except 429)
        assert mock_request.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
