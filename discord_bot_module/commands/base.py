"""
Base command class and utilities.
"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from src.config.settings import settings
from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordCommands")

class BaseCommand:
    """Base class for Discord commands."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    async def defer_response(self, interaction: discord.Interaction):
        """Defer the interaction response."""
        await interaction.response.defer()
        
    async def send_error(self, interaction: discord.Interaction, message: str, ephemeral: bool = True):
        """Send an error message."""
        error_message = f"❌ **Error**: {message}"
        
        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(error_message, ephemeral=ephemeral)
            
    async def send_success(self, interaction: discord.Interaction, embeds: List[discord.Embed], files: List[discord.File] = None):
        """Send success response with embeds and files."""
        if interaction.response.is_done():
            await interaction.followup.send(embeds=embeds, files=files)
        else:
            await interaction.response.send_message(embeds=embeds, files=files)
