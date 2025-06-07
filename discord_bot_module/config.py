"""
Discord bot configuration settings.
"""
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class DiscordConfig:
    """Configuration for Discord bot."""
    
    # Bot settings
    command_prefix: str = '!'
    max_embeds_per_message: int = 10
    interaction_timeout: int = 300  # 5 minutes
    
    # Message limits (Discord limits)
    embed_description_limit: int = 2000
    embed_field_limit: int = 1000
    embed_title_limit: int = 256
    
    # Chart settings
    chart_width: int = 800
    chart_height: int = 600
    chart_dpi: int = 100
    
    # Analysis settings
    default_indicators: List[str] = None
    max_tickers_per_request: int = 10
    max_analysis_period_days: int = 1095  # 3 years
    
    # Error messages
    error_messages: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.default_indicators is None:
            self.default_indicators = ["20-Day SMA"]
            
        if self.error_messages is None:
            self.error_messages = {
                "invalid_ticker": "Please provide valid ticker symbols (e.g., AAPL, GOOGL).",
                "invalid_date": "Please use YYYY-MM-DD date format.",
                "no_data": "No data available for the specified ticker(s).",
                "analysis_failed": "Analysis failed. Please try again later.",
                "timeout": "Request timed out. Please try with fewer tickers or a shorter time period.",
                "rate_limit": "Too many requests. Please wait a moment before trying again."
            }

# Global configuration instance
discord_config = DiscordConfig()
