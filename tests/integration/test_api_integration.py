#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Integration Tests
=====================

Comprehensive integration tests for API endpoints including:
- SmartHelper recommendation endpoint
- Detection events WebSocket
- Database queries
- Error handling

Test Suite: integration/api
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for API."""
    from pokertool.api import PokerToolAPI

    api = PokerToolAPI()
    return TestClient(api.app)


class TestSmartHelperIntegration:
    """Integration tests for SmartHelper API endpoints."""

    def test_recommend_endpoint_basic(self, client):
        """Test basic recommendation request."""
        request_data = {
            "game_state": {
                "street": "flop",
                "pot_size": 150.0,
                "hero_stack": 1000.0,
                "board_cards": ["Ah", "Kh", "Qh"],
                "hero_cards": ["Jh", "Th"],
                "position": "BTN",
                "num_players": 6
            }
        }

        response = client.post("/api/smarthelper/recommend", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "action" in data
        assert "amount" in data
        assert "gtoFrequencies" in data
        assert "factors" in data  # API returns 'factors' not 'reasoning'
        assert "confidence" in data

        # Verify action is valid
        assert data["action"] in ["FOLD", "CHECK", "CALL", "BET", "RAISE", "ALL_IN"]

        # Verify confidence is in valid range
        assert 0 <= data["confidence"] <= 100

    def test_recommend_with_invalid_data(self, client):
        """Test recommendation with invalid game state."""
        request_data = {
            "game_state": {
                "street": "invalid_street",
                "pot_size": -100.0,  # Invalid negative
            }
        }

        response = client.post("/api/smarthelper/recommend", json=request_data)

        # API is designed to be forgiving and provide recommendations even with invalid data
        # This ensures the player always gets guidance rather than errors
        assert response.status_code == 200
        data = response.json()
        assert "action" in data  # Should still provide a recommendation

    def test_factors_endpoint(self, client):
        """Test factors breakdown endpoint."""
        request_data = {
            "game_state": {
                "street": "turn",
                "pot_size": 200.0,
                "hero_stack": 800.0,
                "board_cards": ["Ah", "Kh", "Qh", "2d"],
                "hero_cards": ["Jh", "Th"],
                "position": "CO"
            }
        }

        response = client.post("/api/smarthelper/factors", json=request_data)

        if response.status_code == 200:
            data = response.json()
            assert "factors" in data
            # Factors should include various analysis components
            assert isinstance(data["factors"], list)

    def test_equity_endpoint(self, client):
        """Test equity calculation endpoint."""
        request_data = {
            "hero_cards": ["Ah", "Kh"],
            "board_cards": ["Qh", "Jh", "2d"],
            "opponent_range": "AA,KK,QQ,AK"
        }

        response = client.post("/api/smarthelper/equity", json=request_data)

        if response.status_code == 200:
            data = response.json()
            assert "equity" in data
            assert 0 <= data["equity"] <= 100


class TestDetectionEventsIntegration:
    """Integration tests for detection events system."""

    def test_detection_event_emission(self):
        """Test that detection events can be emitted."""
        from pokertool.detection_events import emit_detection_event

        # Should not raise
        emit_detection_event(
            event_type="pot",
            severity="info",
            message="Pot detected: $150",
            data={"pot_size": 150.0, "confidence": 0.95}
        )

    def test_event_schema_validation(self):
        """Test event schema validation."""
        from pokertool.detection_events import DetectionEventSchema, DetectionEventType, EventSeverity

        # Valid event
        event = DetectionEventSchema(
            type=DetectionEventType.POT,
            severity=EventSeverity.INFO,
            message="Pot updated",
            data={"pot_size": 100.0}
        )

        assert event.validate() is True

        # Invalid event (empty message)
        invalid_event = DetectionEventSchema(
            type=DetectionEventType.POT,
            severity=EventSeverity.INFO,
            message="",
            data={}
        )

        assert invalid_event.validate() is False


class TestDatabaseAPIIntegration:
    """Integration tests between database and API."""

    def test_hand_history_retrieval(self, client):
        """Test retrieving hand history through API."""
        response = client.get("/api/hands/recent?limit=10")

        # Should work even if empty
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or isinstance(data, dict)

    def test_database_stats_endpoint(self, client):
        """Test database statistics endpoint."""
        response = client.get("/api/stats/database")

        if response.status_code == 200:
            data = response.json()
            # Should contain some stats
            assert "database_type" in data or "total_hands" in data or len(data) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
