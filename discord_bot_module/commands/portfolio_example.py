"""
Example: Portfolio command for the Discord bot.
This demonstrates how to add new commands to the modular structure.
"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import List

from .base import BaseCommand
from ..utils.parsers import parse_comma_separated_string
from ..utils.validators import validate_tickers
from ..utils.formatters import format_ticker_list

class PortfolioCommand(BaseCommand):
    """Handle portfolio-related commands."""
    
    async def create_portfolio_summary(self, tickers: List[str]) -> discord.Embed:
        """Create a portfolio summary embed."""
        embed = discord.Embed(
            title="📊 Portfolio Summary",
            description=f"Summary for: {format_ticker_list(tickers)}",
            color=discord.Color.green()
        )
        
        # This would normally fetch real portfolio data
        embed.add_field(
            name="Holdings",
            value=f"{len(tickers)} stocks",
            inline=True
        )
        
        embed.add_field(
            name="Status",
            value="✅ Active",
            inline=True
        )
        
        return embed

@app_commands.describe(
    tickers="Comma-separated ticker symbols for your portfolio (e.g., 'AAPL,GOOGL,TSLA')"
)
async def portfolio_command(
    interaction: discord.Interaction,
    tickers: str
):
    """View your portfolio summary."""
    
    command_handler = PortfolioCommand(interaction.client)
    
    await command_handler.defer_response(interaction)
    
    try:
        # Parse and validate inputs
        ticker_list = parse_comma_separated_string(tickers)
        valid_tickers = validate_tickers(ticker_list)
        
        if not valid_tickers:
            await command_handler.send_error(
                interaction,
                "Please provide at least one valid ticker symbol."
            )
            return
        
        # Create portfolio summary
        embed = await command_handler.create_portfolio_summary(valid_tickers)
        
        await command_handler.send_success(interaction, [embed])
        
    except Exception as e:
        await command_handler.send_error(
            interaction,
            f"An error occurred: {str(e)[:1000]}"
        )

def setup(bot: commands.Bot):
    """Setup the portfolio command."""
    bot.tree.add_command(app_commands.Command(
        name="portfolio",
        description="View your portfolio summary",
        callback=portfolio_command
    ))
