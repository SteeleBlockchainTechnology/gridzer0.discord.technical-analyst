"""
Help-related Discord embeds.
"""
import discord

from src.config.settings import settings

def create_help_embed() -> discord.Embed:
    """Create a help embed for the bot."""
    embed = discord.Embed(
        title="🤖 Technical Analysis Bot Help",
        description="Learn how to use the technical analysis commands.",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📈 /analyze",
        value="""
        **Usage:** `/analyze tickers:AAPL,GOOGL start_date:2023-01-01 end_date:2023-12-31 indicators:20-Day SMA,20-Day EMA`
        
        **Parameters:**
        • `tickers` - Comma-separated stock symbols (e.g., AAPL,GOOGL,TSLA)
        • `start_date` - Start date in YYYY-MM-DD format (optional, defaults to 1 year ago)
        • `end_date` - End date in YYYY-MM-DD format (optional, defaults to today)
        • `indicators` - Comma-separated technical indicators (optional, defaults to 20-Day SMA)
        """,
        inline=False
    )
    
    embed.add_field(
        name="📊 Available Indicators",
        value="\n".join([f"• {ind}" for ind in settings.TECHNICAL_INDICATORS]),
        inline=False
    )
    
    embed.add_field(
        name="💡 Tips",
        value="""
        • Use uppercase ticker symbols (AAPL, not aapl)
        • Date format must be YYYY-MM-DD
        • You can analyze multiple stocks at once
        • Analysis may take a few seconds for multiple tickers
        • Charts are optimized for Discord viewing
        """,
        inline=False
    )
    
    embed.add_field(
        name="🔍 Examples",
        value="""
        `/analyze tickers:AAPL` - Simple analysis of Apple stock
        `/analyze tickers:AAPL,GOOGL indicators:20-Day SMA,20-Day EMA` - Multiple stocks with multiple indicators
        `/analyze tickers:TSLA start_date:2024-01-01 end_date:2024-06-01` - Custom date range
        """,
        inline=False
    )
    
    embed.set_footer(text="For support, contact the bot administrator.")
    
    return embed
