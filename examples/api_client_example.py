#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool API Client Usage Examples
====================================

This script demonstrates various usage patterns for the PokerTool API Client Library.

Run this script:
    python examples/api_client_example.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pokertool.api_client import (
    PokerToolClient,
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)


def example_basic_usage():
    """Example 1: Basic API client usage with API key."""
    print("\n=== Example 1: Basic Usage with API Key ===\n")

    # Initialize client with API key
    client = PokerToolClient(
        base_url="http://localhost:5001",
        api_key="your-api-key-here",
        timeout=30
    )

    try:
        # Check API health
        health = client.get_health()
        print(f"✓ API Status: {health}")

    except APIError as e:
        print(f"✗ API Error: {e}")


def example_context_manager():
    """Example 2: Using client as context manager."""
    print("\n=== Example 2: Context Manager Usage ===\n")

    # Automatic session cleanup with context manager
    with PokerToolClient(base_url="http://localhost:5001", api_key="key") as client:
        try:
            # Get health status
            health = client.get_health()
            print(f"✓ Health check: {health.get('status')}")

        except APIError as e:
            print(f"✗ Error: {e}")

    print("✓ Session automatically closed")


def example_hand_analysis():
    """Example 3: Analyzing a poker hand."""
    print("\n=== Example 3: Hand Analysis ===\n")

    client = PokerToolClient(
        base_url="http://localhost:5001",
        api_key="your-api-key"
    )

    try:
        # Analyze a specific hand scenario
        result = client.analyze_hand(
            hole_cards=["As", "Kh"],                    # Ace of spades, King of hearts
            community_cards=["Qh", "Jd", "Tc"],         # Queen-Jack-Ten flop
            pot_size=100.0,
            stack_size=1000.0,
            position="button",
            num_players=6,
            street="flop"
        )

        print(f"✓ Hand Analysis Results:")
        print(f"  Recommendation: {result.recommendation}")
        print(f"  Confidence: {result.confidence:.2%}")
        print(f"  Equity: {result.equity:.2%}")
        print(f"  Expected Value: ${result.expected_value:.2f}")
        print(f"  Hand Strength: {result.hand_strength}")
        print(f"  Reasoning: {result.reasoning}")

        if result.alternative_actions:
            print(f"\n  Alternative Actions:")
            for action in result.alternative_actions:
                print(f"    - {action['action']}: EV ${action.get('ev', 0):.2f}")

    except ValidationError as e:
        print(f"✗ Invalid input: {e}")
        print(f"  Details: {e.response_data}")

    except APIError as e:
        print(f"✗ API error: {e}")


def example_jwt_authentication():
    """Example 4: JWT authentication flow."""
    print("\n=== Example 4: JWT Authentication ===\n")

    # Initialize client with credentials
    client = PokerToolClient(
        base_url="http://localhost:5001",
        username="testuser",
        password="securepassword123"
    )

    try:
        # Authenticate and get JWT tokens
        print("Authenticating...")
        success = client.authenticate()

        if success:
            print(f"✓ Authentication successful")
            print(f"  Access Token: {client.access_token[:20]}...")

            # Now you can make authenticated requests
            health = client.get_health()
            print(f"✓ Authenticated request successful: {health}")

    except AuthenticationError as e:
        print(f"✗ Authentication failed: {e}")


def example_error_handling():
    """Example 5: Comprehensive error handling."""
    print("\n=== Example 5: Error Handling ===\n")

    client = PokerToolClient(
        base_url="http://localhost:5001",
        api_key="invalid-key",
        max_retries=2
    )

    try:
        # This will likely fail with invalid key
        result = client.analyze_hand(
            hole_cards=["As", "Kh"],
            community_cards=["Qh", "Jd", "Tc"],
            pot_size=100.0,
            stack_size=1000.0,
            position="button",
            num_players=6,
            street="flop"
        )

    except AuthenticationError as e:
        print(f"✗ Authentication Error (401):")
        print(f"  Message: {e}")
        print(f"  Status Code: {e.status_code}")

    except RateLimitError as e:
        print(f"✗ Rate Limit Exceeded (429):")
        print(f"  Message: {e}")
        print(f"  Retry after cooldown period")

    except ValidationError as e:
        print(f"✗ Validation Error (422):")
        print(f"  Message: {e}")
        print(f"  Invalid fields: {e.response_data}")

    except APIError as e:
        print(f"✗ General API Error:")
        print(f"  Message: {e}")
        print(f"  Status Code: {e.status_code}")

    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def example_statistics_and_history():
    """Example 6: Getting statistics and hand history."""
    print("\n=== Example 6: Statistics and History ===\n")

    with PokerToolClient(base_url="http://localhost:5001", api_key="key") as client:
        try:
            # Get player statistics
            print("Fetching user statistics...")
            stats = client.get_statistics(user_id="user_123")

            print(f"✓ User Statistics:")
            print(f"  Hands Played: {stats.get('hands_played', 0)}")
            print(f"  Win Rate: {stats.get('win_rate', 0):.2%}")

            # Get hand history
            print("\nFetching hand history...")
            history = client.get_hand_history(limit=10, offset=0)

            print(f"✓ Hand History:")
            print(f"  Total hands: {history.get('total', 0)}")
            print(f"  Returned: {len(history.get('hands', []))}")

            for i, hand in enumerate(history.get('hands', [])[:3], 1):
                print(f"  {i}. Hand ID: {hand.get('id')}")

        except APIError as e:
            print(f"✗ Error: {e}")


def example_retry_logic():
    """Example 7: Automatic retry with exponential backoff."""
    print("\n=== Example 7: Retry Logic ===\n")

    # Configure client with custom retry settings
    client = PokerToolClient(
        base_url="http://localhost:5001",
        api_key="your-key",
        max_retries=5,
        retry_delay=1.0  # Start with 1 second delay
    )

    print("Client configured with:")
    print(f"  Max Retries: {client.max_retries}")
    print(f"  Initial Delay: {client.retry_delay}s")
    print(f"  Backoff Strategy: Exponential (2^n)")

    try:
        # This will retry on connection errors
        result = client.get_health()
        print(f"✓ Request successful: {result}")

    except APIError as e:
        print(f"✗ Request failed after {client.max_retries} retries: {e}")


def example_custom_configuration():
    """Example 8: Custom client configuration."""
    print("\n=== Example 8: Custom Configuration ===\n")

    # Custom configuration for specific use case
    client = PokerToolClient(
        base_url="https://api.pokertool.com",  # Production URL
        api_key=os.getenv("POKERTOOL_API_KEY"),  # From environment
        timeout=60,  # Longer timeout for complex operations
        max_retries=3,
        retry_delay=2.0
    )

    print("✓ Client configured with custom settings:")
    print(f"  Base URL: {client.base_url}")
    print(f"  Timeout: {client.timeout}s")
    print(f"  Max Retries: {client.max_retries}")
    print(f"  Retry Delay: {client.retry_delay}s")


def main():
    """Run all examples."""
    print("=" * 70)
    print("PokerTool API Client - Usage Examples")
    print("=" * 70)

    examples = [
        ("Basic Usage", example_basic_usage),
        ("Context Manager", example_context_manager),
        ("Hand Analysis", example_hand_analysis),
        ("JWT Authentication", example_jwt_authentication),
        ("Error Handling", example_error_handling),
        ("Statistics & History", example_statistics_and_history),
        ("Retry Logic", example_retry_logic),
        ("Custom Configuration", example_custom_configuration)
    ]

    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
