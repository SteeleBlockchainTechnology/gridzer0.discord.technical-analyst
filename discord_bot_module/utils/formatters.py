"""
Formatting utilities for Discord messages.
"""
from typing import List
from datetime import datetime

def format_ticker_list(tickers: List[str]) -> str:
    """Format a list of tickers for display."""
    if not tickers:
        return "None"
    return ", ".join(tickers)

def format_date_range(start_date: datetime, end_date: datetime) -> str:
    """Format a date range for display."""
    return f"{start_date.date()} to {end_date.date()}"

def format_indicators_list(indicators: List[str]) -> str:
    """Format a list of indicators for display."""
    if not indicators:
        return "None"
    return ", ".join(indicators)

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
