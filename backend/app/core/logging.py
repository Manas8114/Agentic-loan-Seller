"""
Structured Logging Configuration

Uses structlog for JSON-formatted, structured logging.
Integrates with PII masking for safe log output.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import Processor

from app.config import settings


def add_app_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add application context to log events."""
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    return event_dict


def mask_pii_processor(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Mask PII in log events."""
    from app.core.pii_masking import pii_masker
    return pii_masker.mask_dict(event_dict)


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    Sets up:
    - JSON formatting for production
    - Console formatting for development
    - PII masking processor
    - Standard library integration
    """
    
    # Determine if we're in development mode
    is_dev = settings.debug
    
    # Common processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        mask_pii_processor,  # Mask PII before output
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if is_dev:
        # Development: colored console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Production: JSON output for ELK/Loki
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if is_dev else logging.INFO,
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if is_dev else logging.WARNING
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically module __name__).
    
    Returns:
        BoundLogger: Configured structlog logger.
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", customer_id="123", amount=50000)
    """
    return structlog.get_logger(name)


# Initialize logging on module import
setup_logging()

# Default logger
logger = get_logger("app")
