"""Centralized logging configuration for InstaBridge.

This module sets up structured logging with appropriate formatters and handlers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "instabridge",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_json: bool = False,
) -> logging.Logger:
    """Set up and configure logger.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging to file
        format_json: If True, use JSON formatting (for production)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler with color support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if format_json:
        # JSON format for production/parsing
        console_formatter = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","module":"%(module)s","message":"%(message)s"}'
        )
    else:
        # Human-readable format for development
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        # Always use detailed format for files
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s.%(module)s:%(lineno)d | %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "instabridge") -> logging.Logger:
    """Get logger instance.

    If logger doesn't exist, creates it with default settings.

    Args:
        name: Logger name (typically module name)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Set up with defaults if not configured
        return setup_logger(name)
    return logger


# Module-level convenience functions
def debug(msg: str, *args, **kwargs):
    """Log debug message."""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """Log info message."""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """Log warning message."""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """Log error message."""
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """Log critical message."""
    get_logger().critical(msg, *args, **kwargs)


# Default logger setup
_default_logger = setup_logger()
