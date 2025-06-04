"""
Logging utilities for the Technical Analysis application.
"""
import logging
import os
import sys
from ..config.settings import settings

def setup_logger(name="TechnicalAnalysisApp"):
    """Set up and return a configured logger.
    
    Args:
        name (str): The name for the logger
        
    Returns:
        logging.Logger: A configured logger instance
    """
    log_file = settings.LOG_FILE
    logs_dir = os.path.dirname(log_file)
    
    # Ensure the logs directory exists
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    # Configure the logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Get and return the logger
    return logging.getLogger(name)
