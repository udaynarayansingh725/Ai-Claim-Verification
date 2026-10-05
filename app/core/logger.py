import os
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import re

# ANSI Escape sequences
COLORS = { 
    'DEBUG': '\033[36m',      # Cyan
    'INFO': '\033[32m',       # Green
    'WARNING': '\033[33m',    # Yellow
    'ERROR': '\033[31m',      # Red
    'CRITICAL': '\033[41m',   # Red Background
}
RESET = '\033[0m'
KEYWORD_COLOR = '\033[35m'    # Magenta for keywords

KEYWORDS = ["scraping", "extracting", "searching", "verifying", "done"]
KEYWORD_PATTERN = re.compile(rf"\b({'|'.join(KEYWORDS)})\b", re.IGNORECASE)

class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt: str, use_color: bool = True):
        super().__init__(fmt, datefmt="%H:%M:%S")
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        # Save original msg and levelname
        original_msg = str(record.msg)
        original_levelname = record.levelname
        
        if self.use_color:
            color = COLORS.get(record.levelname, RESET)
            record.levelname = f"{color}{record.levelname}{RESET}"
            
            # Auto-highlight keywords in the message body
            record.msg = KEYWORD_PATTERN.sub(rf"{KEYWORD_COLOR}\1{RESET}", original_msg)
                
        # Format the record
        result = super().format(record)
        
        # Restore original values
        record.msg = original_msg
        record.levelname = original_levelname
        
        return result

def setup_logging():
    app_env = os.getenv("APP_ENV", "production").lower()
    log_level_str = os.getenv("LOG_LEVEL", "INFO" if app_env != "development" else "DEBUG").upper()
    
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to prevent duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    # Format string: HH:MM:SS [LEVEL] module_name — message
    log_format = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    
    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    use_color = (app_env == "development")
    console_handler.setFormatter(ColoredFormatter(log_format, use_color=use_color))
    root_logger.addHandler(console_handler)
    
    # 2. Daily Rotating File Handler (All logs)
    app_file_handler = TimedRotatingFileHandler(
        filename="logs/app.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    app_file_handler.setLevel(log_level)
    app_file_handler.setFormatter(logging.Formatter(log_format, datefmt="%H:%M:%S"))
    root_logger.addHandler(app_file_handler)
    
    # 3. Error-only Rotating File Handler
    error_file_handler = TimedRotatingFileHandler(
        filename="logs/error.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(logging.Formatter(log_format, datefmt="%H:%M:%S"))
    root_logger.addHandler(error_file_handler)
    
    # Suppress noisy third-party loggers
    noisy_loggers = ["uvicorn.access", "sqlalchemy.engine.Engine", "httpx"]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
