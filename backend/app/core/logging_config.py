"""
Logging configuration for Deep Research application.

This module configures structured logging using structlog with Azure integration.
Includes proper log formatting, correlation IDs, and Azure Monitor integration.
"""

import json
import logging
import sys
from typing import Any, Dict

import structlog
from azure.monitor.opentelemetry import configure_azure_monitor

from app.core.config import get_settings


def configure_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up:
    - Structured logging with JSON output
    - Log levels based on environment
    - Azure Monitor integration for production
    - Request correlation tracking
    """
    settings = get_settings()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )
    
    # Configure Azure Monitor for production
    if settings.ENVIRONMENT == "production" and settings.AZURE_SUBSCRIPTION_ID:
        try:
            configure_azure_monitor(
                connection_string=f"InstrumentationKey={settings.AZURE_SUBSCRIPTION_ID}"
            )
        except Exception as e:
            # Fallback to standard logging if Azure Monitor fails
            logging.warning(f"Failed to configure Azure Monitor: {e}")
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add correlation ID processor
            add_correlation_id,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add log level
            structlog.stdlib.add_log_level,
            # Stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.dev.set_exc_info,
            # JSON formatting for production, pretty printing for development
            json_formatter if settings.ENVIRONMENT == "production" else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            min_level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_correlation_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add correlation ID to log entries for request tracing.
    
    Args:
        logger: Logger instance
        method_name: Logging method name
        event_dict: Log event dictionary
        
    Returns:
        Updated event dictionary with correlation ID
    """
    # Try to get correlation ID from context (set by middleware)
    import contextvars
    
    correlation_id = getattr(contextvars, 'correlation_id', None)
    if correlation_id and hasattr(correlation_id, 'get'):
        try:
            event_dict['correlation_id'] = correlation_id.get()
        except LookupError:
            # No correlation ID in context
            pass
    
    return event_dict


def json_formatter(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> str:
    """
    Format log entries as JSON for production environments.
    
    Args:
        logger: Logger instance
        method_name: Logging method name
        event_dict: Log event dictionary
        
    Returns:
        JSON formatted log string
    """
    return json.dumps(event_dict, default=str, ensure_ascii=False)


class RequestLoggingMiddleware:
    """
    ASGI middleware for request/response logging and correlation tracking.
    
    Adds structured logging for all HTTP requests with:
    - Request/response timing
    - Correlation IDs
    - Error tracking
    - Performance metrics
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger(__name__)
    
    async def __call__(self, scope, receive, send):
        """ASGI application callable."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        import time
        import uuid
        import contextvars
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        correlation_context = contextvars.ContextVar('correlation_id')
        correlation_context.set(correlation_id)
        
        # Extract request details
        method = scope["method"]
        path = scope["path"]
        query_string = scope.get("query_string", b"").decode()
        client_ip = self._get_client_ip(scope)
        
        start_time = time.time()
        
        # Log request start
        self.logger.info(
            "Request started",
            method=method,
            path=path,
            query_string=query_string,
            client_ip=client_ip,
            correlation_id=correlation_id
        )
        
        # Track response details
        response_status = None
        response_size = 0
        
        async def send_wrapper(message):
            nonlocal response_status, response_size
            
            if message["type"] == "http.response.start":
                response_status = message["status"]
            elif message["type"] == "http.response.body":
                response_size += len(message.get("body", b""))
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            
            # Log successful request completion
            duration = time.time() - start_time
            self.logger.info(
                "Request completed",
                method=method,
                path=path,
                status_code=response_status,
                duration_ms=round(duration * 1000, 2),
                response_size_bytes=response_size,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            # Log request error
            duration = time.time() - start_time
            self.logger.error(
                "Request failed",
                method=method,
                path=path,
                error=str(e),
                duration_ms=round(duration * 1000, 2),
                correlation_id=correlation_id,
                exc_info=True
            )
            raise
    
    def _get_client_ip(self, scope) -> str:
        """Extract client IP from ASGI scope."""
        # Check for forwarded headers (behind load balancer)
        headers = dict(scope.get("headers", []))
        
        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            return forwarded_for.decode().split(",")[0].strip()
        
        real_ip = headers.get(b"x-real-ip")
        if real_ip:
            return real_ip.decode()
        
        # Fallback to direct client IP
        client = scope.get("client")
        if client:
            return client[0]
        
        return "unknown"


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
