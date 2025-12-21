"""
Centralized logging system for Eyeguard application.
Provides structured logging with file rotation and multiple output handlers.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from ..config.config import LOGS_DIR, VERBOSE_LOGGING, DEBUG_MODE


class EyeguardLogger:
    """Singleton logger for the Eyeguard application."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger('Eyeguard')
        
        # Set base level
        if DEBUG_MODE:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            fmt='%(levelname)s: %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO if not VERBOSE_LOGGING else logging.DEBUG)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = LOGS_DIR / f"eyeguard_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_log_file = LOGS_DIR / f"eyeguard_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
    
    def get_logger(self):
        """Get the logger instance."""
        return self.logger


# Global logger instance
_logger_instance = EyeguardLogger()
logger = _logger_instance.get_logger()


def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name: Optional name for child logger
        
    Returns:
        logging.Logger instance
    """
    if name:
        return logger.getChild(name)
    return logger


# Convenience functions
def debug(msg, *args, **kwargs):
    """Log debug message."""
    logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log info message."""
    logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log warning message."""
    logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log error message."""
    logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log critical message."""
    logger.critical(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    """Log exception with traceback."""
    logger.exception(msg, *args, **kwargs)


if __name__ == "__main__":
    # Test logging
    info("Logger initialized successfully")
    debug("This is a debug message")
    warning("This is a warning")
    error("This is an error")
    try:
        raise ValueError("Test exception")
    except Exception:
        exception("Exception occurred")
