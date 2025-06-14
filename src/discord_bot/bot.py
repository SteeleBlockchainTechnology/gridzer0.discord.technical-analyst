"""
Main Discord Bot - All bot functionality in one clean file
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import io

# Import services
from src.config.settings import settings
from src.services.market_data_service import MarketDataService
from src.services.crypto_market_data_service import CryptoMarketDataService
from src.services.technical_analysis_service import TechnicalAnalysisService
from src.services.chart_image_service import ChartImageService
from src.services.ai_analysis_service import AIAnalysisService
from src.utils.logging_utils import setup_logger

# Import UI components and embeds from the same folder
from .ui import IndicatorSelectView, create_indicator_selection_embed
from .embeds import create_analysis_embed, create_error_embed, create_summary_embed, create_help_embed

logger = setup_logger("DiscordBot")

class TechnicalAnalysisBot(commands.Bot):
    """Main Discord bot class."""
    
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
        self.crypto_market_data_service = CryptoMarketDataService()
        self.technical_analysis_service = TechnicalAnalysisService()
        self.chart_image_service = ChartImageService()
        self.ai_analysis_service = AIAnalysisService()
        
    async def setup_hook(self):
        """Called when the bot is starting up."""
        logger.info("Bot is starting up...")
        try:
            # Sync command tree
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
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

# Utility functions
def parse_comma_separated_string(value: str) -> List[str]:
    """Parse comma-separated string into a list of strings."""
    if not value:
        return []
    return [item.strip().upper() for item in value.split(",") if item.strip()]

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def validate_indicators(indicators: List[str]) -> List[str]:
    """Validate and return only supported indicators."""
    valid_indicators = []
    # Create a case-insensitive lookup
    indicator_lookup = {ind.upper(): ind for ind in settings.TECHNICAL_INDICATORS}
    
    for indicator in indicators:
        # Try exact match first
        if indicator in settings.TECHNICAL_INDICATORS:
            valid_indicators.append(indicator)
        # Then try case-insensitive match
        elif indicator.upper() in indicator_lookup:
            valid_indicators.append(indicator_lookup[indicator.upper()])
        else:
            logger.warning(f"Unsupported indicator: {indicator}")
    return valid_indicators

# Create bot instance
bot = TechnicalAnalysisBot()

# STOCK ANALYSIS COMMAND
@bot.tree.command(name="analyze", description="Open the stock technical analysis interface")
async def analyze_stock_command(interaction: discord.Interaction):
    """Open the stock technical analysis setup interface."""
    await _analyze_command_handler(interaction, "stock")

# CRYPTO ANALYSIS COMMAND  
@bot.tree.command(name="crypto", description="Open the cryptocurrency technical analysis interface")
async def analyze_crypto_command(interaction: discord.Interaction):
    """Open the cryptocurrency technical analysis setup interface."""
    await _analyze_command_handler(interaction, "crypto")

# SHARED ANALYSIS HANDLER
async def _analyze_command_handler(interaction: discord.Interaction, asset_type: str):
    """Shared handler for both stock and crypto analysis commands."""
    
    try:
        logger.info(f"{asset_type.capitalize()} analysis command received from {interaction.user}")
        
        # Create callback function for analysis
        async def run_analysis(analysis_interaction, tickers, start_date, end_date, indicators):
            """Run the actual analysis with selected indicators."""
            # The interaction has been deferred by the UI component
            # We can use followup messages to send results
            
            logger.info(f"Analysis callback received indicators: {indicators}")
            logger.info(f"Analysis callback received tickers: {tickers}")
            logger.info(f"Analysis type: {asset_type}")
            
            try:
                embeds = []
                files = []
                
                # Select the appropriate data service based on asset type
                data_service = bot.crypto_market_data_service if asset_type == "crypto" else bot.market_data_service
                
                for ticker in tickers:
                    try:
                        # Fetch market data
                        logger.info(f"Fetching {asset_type} data for {ticker}")
                        data = await asyncio.to_thread(
                            data_service.fetch_data,
                            ticker, start_date.date(), end_date.date()
                        )
                        
                        if data is None or data.empty:
                            embeds.append(create_error_embed(ticker, "No data available for this ticker."))
                            continue
                          # Generate technical analysis
                        logger.info(f"Generating analysis for {ticker}")
                        
                        # Create chart
                        fig = bot.technical_analysis_service.create_candlestick_chart(
                            data, ticker, indicators
                        )
                        
                        # Export chart as image
                        img_buffer = bot.chart_image_service.export_chart_as_image(fig)
                        
                        if img_buffer:
                            # Create Discord file
                            img_buffer.seek(0)
                            discord_file = discord.File(img_buffer, filename=f"{ticker}_chart.png")
                            files.append(discord_file)
                            
                            # Generate technical summary
                            technical_summary = bot.technical_analysis_service.generate_technical_data_summary(
                                data, ticker, indicators
                            )
                            
                            # Get AI analysis
                            ai_analysis_text = "AI analysis unavailable."
                            try:
                                ai_analysis = await asyncio.to_thread(
                                    bot.ai_analysis_service.analyze_stock_data,
                                    data, ticker, indicators
                                )
                                
                                if isinstance(ai_analysis, dict) and 'action' in ai_analysis:
                                    ai_analysis_text = f"**Recommendation:** {ai_analysis.get('action', 'Unknown')}\n"
                                    if 'justification' in ai_analysis:
                                        justification = ai_analysis['justification']
                                        if isinstance(justification, dict):
                                            ai_analysis_text += f"**Analysis:** {justification.get('overall_analysis', 'No detailed analysis available.')}"
                                        else:
                                            ai_analysis_text += f"**Analysis:** {str(justification)}"
                                else:
                                    ai_analysis_text = str(ai_analysis)
                                    
                            except Exception as e:
                                logger.error(f"AI analysis failed for {ticker}: {e}")
                                ai_analysis_text = "AI analysis unavailable due to an error."
                            
                            # Create embed for this ticker
                            embed = create_analysis_embed(
                                ticker, technical_summary, ai_analysis_text, 
                                start_date, end_date, indicators
                            )
                            embeds.append(embed)
                            
                        else:
                            # Fallback if image generation fails
                            technical_summary = bot.technical_analysis_service.generate_technical_data_summary(
                                data, ticker, indicators
                            )
                            
                            embed = create_analysis_embed(
                                ticker, technical_summary, "Chart generation failed.", 
                                start_date, end_date, indicators
                            )
                            embed.set_footer(text="Chart generation failed.")
                            embeds.append(embed)
                            
                    except Exception as e:
                        logger.error(f"Error processing {ticker}: {e}")
                        embeds.append(create_error_embed(ticker, f"Error processing ticker: {str(e)[:500]}"))
                
                # Send results using followup messages
                if embeds:
                    # Send embeds in batches of up to 10 (Discord limit)
                    for i in range(0, len(embeds), 10):
                        batch_embeds = embeds[i:i+10]
                        batch_files = files[i:i+10] if files else None
                        
                        await analysis_interaction.followup.send(embeds=batch_embeds, files=batch_files)
                          # Send summary if multiple tickers
                    if len(tickers) > 1:
                        summary_embed = create_summary_embed(tickers, start_date, end_date, indicators)
                        await analysis_interaction.followup.send(embed=summary_embed)
                else:
                    await analysis_interaction.followup.send(
                        "No data could be processed for the provided tickers.", ephemeral=True
                    )                    
            except Exception as e:
                logger.error(f"Error in analysis: {e}")
                await analysis_interaction.followup.send(
                    f"An error occurred during analysis: {str(e)[:500]}", ephemeral=True
                )
        
        # Show the setup interface (no tickers initially)
        view = IndicatorSelectView(
            tickers=[],  # Start with empty ticker list
            callback=run_analysis,
            asset_type=asset_type
        )
        
        # Create embed showing the setup interface
        embed = create_indicator_selection_embed(
            [],  # Empty ticker list initially
            view.start_date,
            view.end_date,
            view.selected_indicators,
            asset_type
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in {asset_type} analyze command: {e}")
        await interaction.response.send_message(
            f"❌ An error occurred: {str(e)[:500]}", ephemeral=True
        )

# HELP COMMAND
@bot.tree.command(name="help", description="Get help with using the technical analysis bot")
async def help_command(interaction: discord.Interaction):
    """Provide help information for the bot."""
    embed = create_help_embed()
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ERROR HANDLER
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Handle application command errors."""
    logger.error(f"Command error: {error}")
    
    error_message = "❌ **Error**: An error occurred while processing your command. Please try again later."
    
    if interaction.response.is_done():
        await interaction.followup.send(error_message, ephemeral=True)
    else:
        await interaction.response.send_message(error_message, ephemeral=True)

# CREATION FUNCTION
def create_bot():
    """Create and return the bot instance."""
    return bot

def run_bot():
    """Run the Discord bot."""
    try:
        logger.info("Starting Discord bot...")
        bot.run(settings.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
