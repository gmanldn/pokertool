#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenTelemetry Tracing Integration
===================================

Provides distributed tracing for PokerTool API with correlation ID propagation.

Module: pokertool.tracing
Version: 1.0.0
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry dependencies
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.trace import Status, StatusCode, SpanKind
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.info("OpenTelemetry not available - install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi")

# Global tracer instance
_tracer: Optional[Any] = None


def initialize_tracing(
    service_name: str = "pokertool-api",
    enable_console_export: bool = False,
    export_endpoint: Optional[str] = None
) -> bool:
    """
    Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service for tracing
        enable_console_export: Whether to export traces to console (for debugging)
        export_endpoint: Optional OTLP endpoint for exporting traces

    Returns:
        True if tracing was initialized successfully, False otherwise
    """
    global _tracer

    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available - tracing disabled")
        return False

    try:
        # Create resource with service name
        resource = Resource(attributes={
            SERVICE_NAME: service_name,
            "service.version": os.getenv("POKERTOOL_VERSION", "unknown"),
            "deployment.environment": os.getenv("POKERTOOL_ENV", "development"),
        })

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Add console exporter if enabled (useful for development)
        if enable_console_export:
            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            provider.add_span_processor(console_processor)

        # Add OTLP exporter if endpoint provided
        if export_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                otlp_exporter = OTLPSpanExporter(endpoint=export_endpoint)
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                provider.add_span_processor(otlp_processor)
                logger.info(f"OTLP exporter configured for endpoint: {export_endpoint}")
            except ImportError:
                logger.warning("OTLP exporter not available - install with: pip install opentelemetry-exporter-otlp")

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        _tracer = trace.get_tracer(__name__)

        logger.info(f"OpenTelemetry tracing initialized for service: {service_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        return False


def instrument_fastapi(app: Any) -> bool:
    """
    Instrument FastAPI application with OpenTelemetry.

    Args:
        app: FastAPI application instance

    Returns:
        True if instrumentation succeeded, False otherwise
    """
    if not OTEL_AVAILABLE or not _tracer:
        logger.warning("Tracing not initialized - skipping FastAPI instrumentation")
        return False

    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")
        return False


@contextmanager
def trace_operation(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
):
    """
    Context manager for tracing an operation with a span.

    Usage:
        with trace_operation("analyze_hand", {"hand": "AsKh"}):
            # Your code here
            result = analyze_hand()

    Args:
        operation_name: Name of the operation being traced
        attributes: Optional dict of attributes to add to span
        correlation_id: Optional correlation ID to add to span
    """
    if not OTEL_AVAILABLE or not _tracer:
        # Tracing not available - just yield without creating span
        yield None
        return

    try:
        with _tracer.start_as_current_span(
            operation_name,
            kind=SpanKind.INTERNAL
        ) as span:
            # Add correlation ID if provided
            if correlation_id:
                span.set_attribute("correlation_id", correlation_id)

            # Add custom attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

            try:
                yield span
            except Exception as e:
                # Mark span as error
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    except Exception as e:
        logger.error(f"Error in trace_operation: {e}")
        yield None


def add_span_event(event_name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Add an event to the current span.

    Args:
        event_name: Name of the event
        attributes: Optional attributes for the event
    """
    if not OTEL_AVAILABLE:
        return

    try:
        span = trace.get_current_span()
        if span:
            span.add_event(event_name, attributes=attributes or {})
    except Exception as e:
        logger.error(f"Failed to add span event: {e}")


def set_span_attribute(key: str, value: Any):
    """
    Set an attribute on the current span.

    Args:
        key: Attribute key
        value: Attribute value
    """
    if not OTEL_AVAILABLE:
        return

    try:
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, str(value))
    except Exception as e:
        logger.error(f"Failed to set span attribute: {e}")


def get_trace_context() -> Dict[str, str]:
    """
    Get current trace context for propagation to external services.

    Returns:
        Dict containing W3C trace context headers
    """
    if not OTEL_AVAILABLE:
        return {}

    try:
        propagator = TraceContextTextMapPropagator()
        carrier = {}
        propagator.inject(carrier)
        return carrier
    except Exception as e:
        logger.error(f"Failed to get trace context: {e}")
        return {}


# Convenience decorator for traced functions
def traced(operation_name: Optional[str] = None):
    """
    Decorator to automatically trace a function.

    Usage:
        @traced("my_operation")
        def my_function(arg1, arg2):
            # Function code
            pass

    Args:
        operation_name: Optional name for the operation (defaults to function name)
    """
    def decorator(func):
        import functools

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            with trace_operation(name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            with trace_operation(name):
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled and initialized."""
    return OTEL_AVAILABLE and _tracer is not None
