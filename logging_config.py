import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
def setup_logger(name="application", log_file="application.log", level=logging.INFO):
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, log_file), maxBytes=5 * 1024 * 1024, backupCount=5
    )
    handler.setFormatter(log_formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger