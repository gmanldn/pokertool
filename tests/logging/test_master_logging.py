#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for structured master logging output."""

import io
import json
import logging

from pokertool.master_logging import MasterLogger, LogCategory


def test_master_logger_outputs_structured_json():
    """Master logger should emit JSON payloads with consistent fields."""
    logger = MasterLogger.get_instance()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logger._get_json_formatter())
    logger.master_logger.addHandler(handler)

    try:
        logger.info("Structured logging test", category=LogCategory.API, correlation_id='cid-123')
        handler.flush()
        payloads = [line for line in stream.getvalue().splitlines() if line.strip()]
        assert payloads, "No log output captured"

        data = json.loads(payloads[-1])
        assert data['application'] == 'pokertool'
        assert data['session_id'] == logger.session_id
        assert 'environment' in data
        assert data['level'] == 'INFO'
        assert data['category'] == 'api'
        assert data['correlation_id'] == 'cid-123'
        assert 'timestamp' in data
        assert 'message' in data
    finally:
        logger.master_logger.removeHandler(handler)
