import logging
import logging.config
from pathlib import Path

from rich.logging import RichHandler

from ion_cannon.config.settings import settings

def setup_logging() -> None:
    """Initialize logging configuration."""
    # Ensure logs directory exists
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "rich": {
                "format": "%(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "level": "INFO",
                "formatter": "rich",
                "rich_tracebacks": True,
                "show_time": False,
                "show_level": True,
                "show_path": False
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": str(settings.LOGS_DIR / "ion_cannon.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "ion_cannon": {  # Root logger for our package
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)