import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(name, log_file, level=logging.INFO):
    """Sets up a logger with both file rotation and terminal output."""
    # LOG_DIR = "logs"
    # os.makedirs(LOG_DIR, exist_ok=True)
    # File handler
    file_handler = RotatingFileHandler(os.path.join(LOG_DIR, log_file), maxBytes=50 * 1024 * 1024, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Stream handler for terminal output
    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Debug to verify handlers
    logger.debug(f"Logger '{name}' initialized with file handler '{log_file}' and stream handler.")
    
    return logger