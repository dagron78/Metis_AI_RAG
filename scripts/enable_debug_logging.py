#!/usr/bin/env python3
"""
Script to enable DEBUG level logging for the relevant modules to see Ollama output comparison.

This script:
1. Sets the logging level to DEBUG for the relevant modules
2. Configures logging to output to both console and a file
"""
import os
import sys
import logging
import logging.config

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_debug_logging():
    """
    Configure logging to show DEBUG messages for the relevant modules
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Log file path
    log_file = os.path.join(logs_dir, "ollama_debug.log")
    
    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "stream": sys.stdout,
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "formatter": "detailed",
                "filename": log_file,
                "mode": "a",
            },
        },
        "loggers": {
            "app.rag.rag_generation": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            },
            "app.rag.rag_engine": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            },
            "app.api.chat": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            },
            "app.utils.text_processor": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            },
            "ollama_debug": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    }
    
    # Apply the configuration
    logging.config.dictConfig(logging_config)
    
    # Create a logger for this script
    logger = logging.getLogger("ollama_debug")
    logger.info("Debug logging enabled for Ollama output comparison")
    logger.info(f"Logs will be written to {log_file}")
    
    return logger

if __name__ == "__main__":
    # Setup debug logging
    logger = setup_debug_logging()
    
    # Print instructions
    logger.info("=" * 80)
    logger.info("DEBUG LOGGING ENABLED FOR OLLAMA OUTPUT COMPARISON")
    logger.info("=" * 80)
    logger.info("To see the raw and processed outputs:")
    logger.info("1. Run your application with this logging configuration")
    logger.info("2. Make requests to the chat API")
    logger.info("3. Check the logs for entries with 'RAW OLLAMA OUTPUT' and 'PROCESSED BACKEND OUTPUT'")
    logger.info("4. Use the Query ID to correlate the different stages of processing")
    logger.info("\nAlternatively, use the check_ollama_debug_logs.py script to make test requests")
    logger.info("=" * 80)