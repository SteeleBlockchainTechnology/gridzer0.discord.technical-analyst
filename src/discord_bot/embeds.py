"""
Discord Embeds for Bot Messages
"""
import discord
from datetime import datetime
from typing import List, Optional

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to a maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

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
        title=f"{ticker} Technical Analysis",
        description=truncate_text(technical_summary, 1900),  # Conservative limit
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # Add AI analysis as field if available
    if ai_analysis and len(ai_analysis) > 0:
        embed.add_field(
            name="AI Analysis",
            value=truncate_text(ai_analysis, 800),  # Very conservative for fields
            inline=False
        )
    
    # Add chart image
    embed.set_image(url=f"attachment://{ticker}_chart.png")
    
    # Add metadata footer
    period_text = f"{start_date.date()} to {end_date.date()}"
    indicators_text = ", ".join(indicators)
    footer_text = f"Period: {period_text} | Indicators: {indicators_text}"
    
    embed.set_footer(text=truncate_text(footer_text, 200))
    
    return embed

def create_error_embed(ticker: str, error_message: str) -> discord.Embed:
    """Create an embed for error messages."""
    embed = discord.Embed(
        title=f"Error - {ticker}",
        description=truncate_text(error_message, 1900),
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
        title="Analysis Summary",
        description=f"Completed analysis for {len(tickers)} ticker(s): {', '.join(tickers)}",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="Period", 
        value=f"{start_date.date()} to {end_date.date()}", 
        inline=True
    )
    embed.add_field(
        name="Indicators", 
        value=", ".join(indicators), 
        inline=True
    )
    
    return embed

def create_help_embed() -> discord.Embed:
    """Create a help embed for the bot."""    
    embed = discord.Embed(
        title="📊 Technical Analysis Bot Help",
        description="Interactive Discord bot for technical analysis of stocks and cryptocurrencies.",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="📈 Stock Analysis Commands",
        value="""
        **Usage:** `/analyze`
        
        **Features:**
        • Interactive ticker input for stocks (AAPL, GOOGL, TSLA, etc.)
        • Technical indicator selection via buttons
        • Custom date range setting
        • Yahoo Finance data source
        • AI-powered analysis insights
        """,
        inline=False
    )
    
    embed.add_field(
        name="₿ Cryptocurrency Analysis Commands",
        value="""
        **Usage:** `/crypto`
        
        **Features:**
        • Interactive ticker input for crypto (BTC, ETH, ADA, etc.)
        • Same technical indicators as stocks
        • Custom date range setting
        • CoinGecko API data source
        • AI-powered crypto insights
        """,
        inline=False
    )
    
    embed.add_field(
        name="📋 Available Technical Indicators",
        value="""
        • **20-Day SMA** - Simple Moving Average
        • **20-Day EMA** - Exponential Moving Average
        • **Bollinger Bands** - Volatility indicator
        • **VWAP** - Volume Weighted Average Price
        """,
        inline=False
    )
    
    embed.add_field(
        name="💡 Usage Tips",
        value="""
        • Choose `/analyze` for stocks, `/crypto` for cryptocurrencies
        • Use uppercase symbols (AAPL, BTC not aapl, btc)
        • Dates must be in YYYY-MM-DD format
        • Multiple tickers: separate with commas
        • Interactive setup - no need to memorize commands!
        """,
        inline=False
    )
    
    embed.add_field(
        name="🚀 Quick Examples",
        value="""
        **Stocks:** `/analyze` → Set tickers: AAPL,GOOGL → Select indicators
        **Crypto:** `/crypto` → Set tickers: BTC,ETH → Select indicators
        **Mixed analysis:** Use both commands separately
        """,
        inline=False
    )
    
    embed.set_footer(text="GridZer0 Technical Analysis Bot • For support, contact the administrator")
    
    return embed
