"""Entry point for AI Debate platform - run this file to start the server."""
import uvicorn
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Add current directory to path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Get log level from environment variable (default: DEBUG)
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()

# Create logs directory
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Configure logging to show all logs
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# File handler with rotation (max 10MB, keep 5 files)
file_handler = RotatingFileHandler(
    os.path.join(logs_dir, "app.log"),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(log_level)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# Set specific loggers to DEBUG
logging.getLogger("debate.engine").setLevel(log_level)
logging.getLogger("app.crud").setLevel(log_level)
logging.getLogger("app.main").setLevel(log_level)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="debug",
        reload_dirs=["app","frontend"]
    )
