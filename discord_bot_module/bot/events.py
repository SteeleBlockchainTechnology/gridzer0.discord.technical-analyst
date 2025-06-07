"""
Bot event handlers.
"""
import discord
from discord.ext import commands
from discord import app_commands
import logging

from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordBotEvents")

async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle application command errors."""
    logger.error(f"Command error: {error}")
    
    if interaction.response.is_done():
        await interaction.followup.send(
            "❌ **Error**: An error occurred while processing your command. Please try again later.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ **Error**: An error occurred while processing your command. Please try again later.",
            ephemeral=True
        )

def setup_events(bot: commands.Bot):
    """Setup bot event handlers."""
    bot.tree.on_error = on_app_command_error
