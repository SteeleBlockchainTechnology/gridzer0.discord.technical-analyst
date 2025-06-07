"""
Error handling for Discord interactions.
"""
import discord
from discord import app_commands
import logging

from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordErrorHandler")

class ErrorHandler:
    """Handle Discord bot errors."""
    
    @staticmethod
    async def handle_app_command_error(
        interaction: discord.Interaction, 
        error: app_commands.AppCommandError
    ):
        """Handle application command errors."""
        logger.error(f"Command error: {error}")
        
        error_message = "❌ **Error**: An error occurred while processing your command. Please try again later."
        
        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)
    
    @staticmethod
    async def handle_interaction_timeout(interaction: discord.Interaction):
        """Handle interaction timeout errors."""
        logger.warning(f"Interaction timeout for user {interaction.user}")
        
        try:
            await interaction.followup.send(
                "⏰ **Timeout**: The operation took too long to complete. Please try again.",
                ephemeral=True
            )
        except discord.HTTPException:
            # Interaction is too old to respond to
            pass
    
    @staticmethod
    async def handle_validation_error(interaction: discord.Interaction, message: str):
        """Handle validation errors."""
        logger.warning(f"Validation error: {message}")
        
        error_message = f"❌ **Validation Error**: {message}"
        
        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)
