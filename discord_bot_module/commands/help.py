"""
Help command for the Discord bot.
"""
import discord
from discord.ext import commands
from discord import app_commands

from ..embeds.help_embeds import create_help_embed

async def help_command(interaction: discord.Interaction):
    """Provide help information for the bot."""
    embed = create_help_embed()
    await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot: commands.Bot):
    """Setup the help command."""
    bot.tree.add_command(app_commands.Command(
        name="help",
        description="Get help with using the technical analysis bot",
        callback=help_command
    ))
