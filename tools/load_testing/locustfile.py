#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Locust load test script for PokerTool API.

Run with:
    locust -f tools/load_testing/locustfile.py
"""

from __future__ import annotations

from locust import HttpUser, TaskSet, between, events, task
import logging
import os
from typing import Dict, Optional


logger = logging.getLogger(__name__)

MAX_AVG_RESPONSE_MS = float(os.getenv('POKERTOOL_LOADTEST_MAX_AVG_MS', '500'))
MAX_FAIL_RATIO = float(os.getenv('POKERTOOL_LOADTEST_MAX_FAILURE_RATIO', '0.01'))


class PokerToolTasks(TaskSet):
    """Collection of high-value API scenarios."""

    token: Optional[str] = None

    def on_start(self) -> None:
        self._authenticate()

    # Authentication -------------------------------------------------
    def _authenticate(self) -> None:
        username = os.getenv('POKERTOOL_LOADTEST_USERNAME', 'admin')
        password = os.getenv('POKERTOOL_LOADTEST_PASSWORD', 'pokertool')

        with self.client.post(
            "/auth/token",
            params={'username': username, 'password': password},
            name="/auth/token",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    payload = response.json()
                    self.token = payload.get('access_token')
                    if not self.token:
                        response.failure("Missing access_token in response")
                    else:
                        response.success()
                except Exception as exc:
                    response.failure(f"Failed to parse auth response: {exc}")
            else:
                response.failure(f"Login failed ({response.status_code})")

    def _headers(self) -> Dict[str, str]:
        if not self.token:
            return {}
        return {'Authorization': f"Bearer {self.token}"}

    # Tasks ----------------------------------------------------------
    @task(5)
    def system_health(self) -> None:
        self.client.get("/api/system/health", headers=self._headers(), name="/api/system/health")

    @task(2)
    def health_history(self) -> None:
        self.client.get(
            "/api/system/health/history?hours=24",
            headers=self._headers(),
            name="/api/system/health/history?hours=24",
        )

    @task(2)
    def health_trends(self) -> None:
        self.client.get(
            "/api/system/health/trends?hours=24",
            headers=self._headers(),
            name="/api/system/health/trends?hours=24",
        )

    @task(1)
    def hud_metrics(self) -> None:
        self.client.get(
            "/api/scraping/accuracy/metrics",
            headers=self._headers(),
            name="/api/scraping/accuracy/metrics",
        )

    @task(1)
    def trigger_health_check(self) -> None:
        with self.client.post(
            "/api/system/health/run",
            headers=self._headers(),
            name="/api/system/health/run",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 202):
                response.failure(f"Unexpected status {response.status_code}")
            else:
                response.success()


class PokerToolUser(HttpUser):
    """Main Locust user class."""

    tasks = [PokerToolTasks]
    wait_time = between(1.0, 3.0)
    host = os.getenv('POKERTOOL_LOADTEST_HOST', 'http://localhost:5001')


@events.test_stop.add_listener
def enforce_thresholds(environment, **_kwargs) -> None:
    """Fail the run if aggregate thresholds are exceeded."""
    stats = environment.stats.total
    avg_ms = stats.avg_response_time or 0.0
    fail_ratio = stats.fail_ratio or 0.0

    logger.info(
        "Load test complete: avg=%.2fms, fail_ratio=%.4f",
        avg_ms,
        fail_ratio,
    )

    if avg_ms > MAX_AVG_RESPONSE_MS or fail_ratio > MAX_FAIL_RATIO:
        logger.error(
            "Threshold breach detected (avg=%.2fms, fail_ratio=%.4f). "
            "Set tighter env vars or investigate regressions.",
            avg_ms,
            fail_ratio,
        )
        environment.process_exit_code = 1
