"""
Interaction handling utilities.
"""
import discord
from discord.ext import commands
import asyncio
import logging
from typing import List, Optional

from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordInteractionHandler")

class InteractionHandler:
    """Handle Discord interactions."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def send_paginated_embeds(
        self, 
        interaction: discord.Interaction, 
        embeds: List[discord.Embed], 
        files: Optional[List[discord.File]] = None,
        max_embeds_per_message: int = 10
    ):
        """Send embeds in paginated batches."""
        if not embeds:
            await interaction.followup.send(
                "❌ No data to display.", 
                ephemeral=True
            )
            return
        
        # Send embeds in batches
        for i in range(0, len(embeds), max_embeds_per_message):
            batch_embeds = embeds[i:i+max_embeds_per_message]
            batch_files = files[i:i+max_embeds_per_message] if files else None
            
            try:
                if i == 0 and not interaction.response.is_done():
                    await interaction.response.send_message(
                        embeds=batch_embeds, 
                        files=batch_files
                    )
                else:
                    await interaction.followup.send(
                        embeds=batch_embeds, 
                        files=batch_files
                    )
                    
                # Small delay between batches to avoid rate limits
                if i + max_embeds_per_message < len(embeds):
                    await asyncio.sleep(0.5)
                    
            except discord.HTTPException as e:
                logger.error(f"Failed to send embed batch {i//max_embeds_per_message + 1}: {e}")
                await interaction.followup.send(
                    f"❌ Failed to send results batch {i//max_embeds_per_message + 1}",
                    ephemeral=True
                )
    
    async def defer_if_needed(self, interaction: discord.Interaction, ephemeral: bool = False):
        """Defer interaction response if not already done."""
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=ephemeral)
    
    async def send_thinking_message(self, interaction: discord.Interaction):
        """Send a 'thinking' message for long operations."""
        await self.defer_if_needed(interaction)
        await interaction.followup.send("🤔 Processing your request...", ephemeral=True)
