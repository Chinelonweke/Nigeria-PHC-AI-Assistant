"""
Colored Logging System
Provides beautiful colored console and file logs
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import colorlog


# Color scheme
LOG_COLORS = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}

# Console format (with colors)
CONSOLE_FORMAT = (
    '%(log_color)s%(levelname)-8s%(reset)s '
    '%(green)s%(asctime)s%(reset)s '
    '%(blue)s[%(name)s]%(reset)s '
    '%(white)s%(message)s%(reset)s'
)

# File format (no colors)
FILE_FORMAT = '%(levelname)-8s %(asctime)s [%(name)s] %(message)s'


def setup_logger(
    name: str,
    log_level: str = "DEBUG",
    log_to_file: bool = True
) -> logging.Logger:
    """
    Setup colored logger
    
    Args:
        name: Logger name
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Save logs to file
    
    Returns:
        Configured logger
        
    Example:
        >>> logger = setup_logger("api")
        >>> logger.info("Server started")
        >>> logger.error("Connection failed")
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers = []  # Clear existing handlers
    
    # Console handler (colored)
    console = colorlog.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, log_level.upper()))
    console.setFormatter(
        colorlog.ColoredFormatter(
            CONSOLE_FORMAT,
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors=LOG_COLORS
        )
    )
    logger.addHandler(console)
    
    # File handler (no colors)
    if log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(
            logging.Formatter(FILE_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
        )
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create logger"""
    return setup_logger(name)


# Default app logger
app_logger = setup_logger("phc_assistant")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LOGGER TEST - Colored Output")
    print("=" * 60 + "\n")
    
    logger = setup_logger("test")
    logger.debug("🔍 DEBUG: Detailed information")
    logger.info("✅ INFO: General information")
    logger.warning("⚠️ WARNING: Warning message")
    logger.error("❌ ERROR: Error occurred")
    logger.critical("🚨 CRITICAL: Critical issue")
    
    print("\n" + "=" * 60)
    print(f"✅ Logs saved to: logs/test_{datetime.now().strftime('%Y%m%d')}.log")
    print("=" * 60 + "\n")