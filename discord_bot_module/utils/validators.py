"""
Validation utilities for Discord commands.
"""
from typing import List
import logging

from src.config.settings import settings
from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordValidators")

def validate_indicators(indicators: List[str]) -> List[str]:
    """Validate and return only supported indicators."""
    valid_indicators = []
    for indicator in indicators:
        if indicator in settings.TECHNICAL_INDICATORS:
            valid_indicators.append(indicator)
        else:
            logger.warning(f"Unsupported indicator: {indicator}")
    return valid_indicators

def validate_tickers(tickers: List[str]) -> List[str]:
    """Validate ticker symbols (basic validation)."""
    valid_tickers = []
    for ticker in tickers:
        if ticker and len(ticker) >= 1 and ticker.isalnum():
            valid_tickers.append(ticker.upper())
        else:
            logger.warning(f"Invalid ticker format: {ticker}")
    return valid_tickers
