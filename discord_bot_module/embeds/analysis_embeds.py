"""
Analysis-related Discord embeds.
"""
import discord
from datetime import datetime
from typing import List, Optional

from ..utils.formatters import format_date_range, format_indicators_list, truncate_text

def create_analysis_embed(
    ticker: str, 
    technical_summary: str, 
    ai_analysis: Optional[str],
    start_date: datetime,
    end_date: datetime,
    indicators: List[str]
) -> discord.Embed:
    """Create an embed for technical analysis results."""
    embed = discord.Embed(
        title=f"📈 {ticker} Technical Analysis",
        description=truncate_text(technical_summary, 2000),  # Discord limit
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # Add AI analysis as field if available
    if ai_analysis and len(ai_analysis) > 0:
        embed.add_field(
            name="🤖 AI Analysis",
            value=truncate_text(ai_analysis, 1000),  # Discord field limit
            inline=False
        )
    
    # Add chart image
    embed.set_image(url=f"attachment://{ticker}_chart.png")
    
    # Add metadata
    embed.set_footer(
        text=f"Analysis Period: {format_date_range(start_date, end_date)} | Indicators: {format_indicators_list(indicators)}"
    )
    
    return embed

def create_error_embed(ticker: str, error_message: str) -> discord.Embed:
    """Create an embed for error messages."""
    embed = discord.Embed(
        title=f"❌ {ticker}",
        description=truncate_text(error_message, 2000),
        color=discord.Color.red()
    )
    return embed

def create_summary_embed(
    tickers: List[str],
    start_date: datetime,
    end_date: datetime,
    indicators: List[str]
) -> discord.Embed:
    """Create a summary embed for multiple ticker analysis."""
    embed = discord.Embed(
        title="📊 Analysis Summary",
        description=f"Completed analysis for {len(tickers)} ticker(s): {', '.join(tickers)}",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="Period", 
        value=format_date_range(start_date, end_date), 
        inline=True
    )
    embed.add_field(
        name="Indicators", 
        value=format_indicators_list(indicators), 
        inline=True
    )
    
    return embed
