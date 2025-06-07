"""
Parsing utilities for Discord commands.
"""
from typing import List, Optional
from datetime import datetime
import logging

from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordParsers")

def parse_comma_separated_string(value: str) -> List[str]:
    """Parse comma-separated string into a list of strings."""
    if not value:
        return []
    return [item.strip().upper() for item in value.split(",") if item.strip()]

def parse_indicators_string(value: str) -> List[str]:
    """Parse comma-separated indicators string preserving case."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}")
        return None
