"""
Logging configuration for the application.
"""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    if level is None:
        level = logging.INFO
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger
