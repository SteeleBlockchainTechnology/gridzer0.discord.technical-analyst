"""
Discord Bot for Technical Analysis
Main bot class and initialization
"""
import discord
from discord.ext import commands
import logging
from typing import Optional

from src.config.settings import settings
from src.services.market_data_service import MarketDataService
from src.services.technical_analysis_service import TechnicalAnalysisService
from src.services.ai_analysis_service import AIAnalysisService
from src.utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger("DiscordBot")

class TechnicalAnalysisBot(commands.Bot):
    """Discord bot for technical analysis."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Initialize services
        self.market_data_service = MarketDataService()
        self.technical_analysis_service = TechnicalAnalysisService()
        self.ai_analysis_service = AIAnalysisService()
        
    async def setup_hook(self):
        """Called when the bot is starting up."""
        logger.info("Bot is starting up...")
        try:
            # Load commands
            await self.load_commands()
            
            # Sync command tree
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    async def load_commands(self):
        """Load all command modules."""
        from ..commands.analyze import setup as setup_analyze
        from ..commands.help import setup as setup_help
        
        # Setup commands
        setup_analyze(self)
        setup_help(self)
        
        logger.info("Commands loaded successfully")
    
    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name=settings.DISCORD_STATUS
            )
        )

def create_bot() -> TechnicalAnalysisBot:
    """Create and return a bot instance."""
    return TechnicalAnalysisBot()
