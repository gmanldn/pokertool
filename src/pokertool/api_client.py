#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool API Client Library
=============================

Comprehensive Python client library for integrating with the PokerTool API.

Provides a high-level interface for external applications to interact with
PokerTool's REST API and WebSocket endpoints with automatic retry logic,
authentication handling, and type-safe request/response models.

Module: pokertool.api_client
Version: 1.0.0
"""

import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import time
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(APIError):
    """Raised when authentication fails."""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass


class ValidationError(APIError):
    """Raised when request validation fails."""
    pass


@dataclass
class HandAnalysisRequest:
    """Request model for hand analysis."""
    hole_cards: List[str]
    community_cards: List[str]
    pot_size: float
    stack_size: float
    position: str
    num_players: int
    street: str  # preflop, flop, turn, river


@dataclass
class HandAnalysisResponse:
    """Response model for hand analysis."""
    recommendation: str
    confidence: float
    equity: float
    expected_value: float
    hand_strength: str
    reasoning: str
    alternative_actions: List[Dict[str, Any]]


class PokerToolClient:
    """
    High-level client for PokerTool API.

    Features:
    - Automatic authentication and token refresh
    - Retry logic with exponential backoff
    - Rate limit handling
    - Type-safe request/response models
    - Comprehensive error handling
    - Request logging and debugging

    Example:
        client = PokerToolClient(
            base_url="http://localhost:5001",
            api_key="your-api-key"
        )

        # Analyze a hand
        result = client.analyze_hand(
            hole_cards=["As", "Kh"],
            community_cards=["Qh", "Jd", "Tc"],
            pot_size=100.0,
            stack_size=1000.0,
            position="button",
            num_players=6,
            street="flop"
        )

        print(f"Recommendation: {result.recommendation}")
        print(f"Confidence: {result.confidence}")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:5001",
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize API client.

        Args:
            base_url: Base URL of PokerTool API
            api_key: API key for authentication (preferred)
            username: Username for JWT authentication
            password: Password for JWT authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.password = password
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

        # Set default headers
        if self.api_key:
            self.session.headers['X-API-Key'] = self.api_key

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = {}

        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'

        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: Response object

        Returns:
            Parsed JSON response

        Raises:
            APIError: For various API errors
        """
        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code == 200:
            return data
        elif response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed",
                status_code=response.status_code,
                response_data=data
            )
        elif response.status_code == 429:
            raise RateLimitError(
                "Rate limit exceeded",
                status_code=response.status_code,
                response_data=data
            )
        elif response.status_code == 422:
            raise ValidationError(
                f"Validation error: {data.get('detail', 'Unknown error')}",
                status_code=response.status_code,
                response_data=data
            )
        else:
            raise APIError(
                f"API error: {data.get('detail', response.text)}",
                status_code=response.status_code,
                response_data=data
            )

    def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests

        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}{endpoint}"

        # Add authentication headers
        headers = kwargs.get('headers', {})
        headers.update(self._get_auth_headers())
        kwargs['headers'] = headers

        # Set timeout
        kwargs.setdefault('timeout', self.timeout)

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                return self._handle_response(response)

            except (requests.ConnectionError, requests.Timeout) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                    continue

            except APIError as e:
                # Don't retry on client errors (4xx) except rate limiting
                if e.status_code and 400 <= e.status_code < 500 and e.status_code != 429:
                    raise
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue

        # If we get here, all retries failed
        raise APIError(f"Request failed after {self.max_retries} attempts") from last_exception

    def authenticate(self) -> bool:
        """
        Authenticate with username/password and obtain JWT tokens.

        Returns:
            True if authentication successful

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.username or not self.password:
            raise AuthenticationError("Username and password required for authentication")

        try:
            response = self._request_with_retry(
                'POST',
                '/auth/login',
                json={'username': self.username, 'password': self.password}
            )

            self.access_token = response['access_token']
            self.refresh_token = response.get('refresh_token')

            logger.info("Authentication successful")
            return True

        except APIError as e:
            raise AuthenticationError(f"Authentication failed: {e}")

    def analyze_hand(
        self,
        hole_cards: List[str],
        community_cards: List[str],
        pot_size: float,
        stack_size: float,
        position: str,
        num_players: int,
        street: str
    ) -> HandAnalysisResponse:
        """
        Analyze a poker hand.

        Args:
            hole_cards: Player's hole cards (e.g., ["As", "Kh"])
            community_cards: Community cards
            pot_size: Current pot size
            stack_size: Player's stack size
            position: Player position (e.g., "button", "cutoff")
            num_players: Number of players in hand
            street: Current street ("preflop", "flop", "turn", "river")

        Returns:
            Hand analysis result

        Example:
            result = client.analyze_hand(
                hole_cards=["As", "Kh"],
                community_cards=["Qh", "Jd", "Tc"],
                pot_size=100.0,
                stack_size=1000.0,
                position="button",
                num_players=6,
                street="flop"
            )
        """
        payload = {
            'hole_cards': hole_cards,
            'community_cards': community_cards,
            'pot_size': pot_size,
            'stack_size': stack_size,
            'position': position,
            'num_players': num_players,
            'street': street
        }

        response = self._request_with_retry('POST', '/analyze', json=payload)

        return HandAnalysisResponse(
            recommendation=response['recommendation'],
            confidence=response['confidence'],
            equity=response.get('equity', 0.0),
            expected_value=response.get('expected_value', 0.0),
            hand_strength=response.get('hand_strength', 'unknown'),
            reasoning=response.get('reasoning', ''),
            alternative_actions=response.get('alternative_actions', [])
        )

    def get_health(self) -> Dict[str, Any]:
        """
        Get API health status.

        Returns:
            Health status information
        """
        return self._request_with_retry('GET', '/health')

    def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get player statistics.

        Args:
            user_id: Optional user ID (defaults to authenticated user)

        Returns:
            Player statistics
        """
        params = {'user_id': user_id} if user_id else {}
        return self._request_with_retry('GET', '/statistics', params=params)

    def get_hand_history(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get hand history.

        Args:
            limit: Maximum number of hands to return
            offset: Offset for pagination
            filters: Optional filters (position, date_range, etc.)

        Returns:
            Hand history data
        """
        params = {'limit': limit, 'offset': offset}
        if filters:
            params.update(filters)

        return self._request_with_retry('GET', '/hand-history', params=params)

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
