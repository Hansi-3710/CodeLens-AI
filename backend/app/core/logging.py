"""
Structured logging configuration.

Belongs to: backend/app/core/
Phase: 2 (Backend Foundation)
"""
import logging
import logging.config

from app.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    log_format = (
        '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
        if settings.ENVIRONMENT == "production"
        else "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": {"format": log_format}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {"handlers": ["console"], "level": "DEBUG" if settings.DEBUG else "INFO"},
        }
    )
