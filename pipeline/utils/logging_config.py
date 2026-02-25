"""
Shared logging configuration for pipeline scripts.

Provides console handler (INFO) + rotating file handler (DEBUG).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_file: str,
    log_level: str = "INFO",
    workspace: Path = None
) -> logging.Logger:
    """
    Set up logging with console and file handlers.

    Args:
        log_file: Name of log file (e.g., '03_extract.log')
        log_level: Logging level for console (DEBUG/INFO/WARNING)
        workspace: Optional workspace path for log file location

    Returns:
        Configured logger instance
    """
    # Determine log file path
    if workspace:
        log_path = workspace / log_file
    else:
        log_path = Path(log_file)

    # Create logger
    logger = logging.getLogger(log_file.replace('.log', ''))
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler - user specified level
    console_handler = logging.StreamHandler(sys.stdout)
    console_level = getattr(logging, log_level.upper(), logging.INFO)
    console_handler.setLevel(console_level)
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler - always DEBUG for full details
    # Rotating: 5MB max, keep 3 backups
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger
