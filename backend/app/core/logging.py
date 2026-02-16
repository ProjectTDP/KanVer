"""
Logging configuration for KanVer application
"""

import logging
import os
from pathlib import Path


def setup_logging():
    """
    Configure logging for the application.
    Sets up console and file handlers with appropriate formatters.
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Determine log level based on environment
    debug_mode = os.getenv("DEBUG", "True").lower() == "true"
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # Create formatter
    log_format = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for all logs
    app_log_file = logs_dir / "app.log"
    file_handler = logging.FileHandler(app_log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # File handler for errors only
    error_log_file = logs_dir / "error.log"
    error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {logging.getLevelName(log_level)}")
    logger.info(f"App logs: {app_log_file}")
    logger.info(f"Error logs: {error_log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
