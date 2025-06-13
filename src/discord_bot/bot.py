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
            # Load admin and user command cogs
            await self.load_extension('src.discord_bot.admin_commands')
            await self.load_extension('src.discord_bot.user_commands')
            logger.info("Loaded admin and user commands")
            
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
        
        # Initialize usage tracker
        try:
            from src.database.usage_tracker import UsageTracker
            usage_tracker = UsageTracker()
        except ImportError:
            logger.warning("Usage tracker not available")
            usage_tracker = None
        
        # Check user limits before showing UI
        user_id = str(interaction.user.id)
        if usage_tracker:
            limits_check = usage_tracker.check_user_limits(user_id)
            
            if not limits_check['within_limits']:
                # Send limit exceeded message
                embed = discord.Embed(
                    title="🚫 Usage Limit Exceeded",
                    description=_create_limit_message(limits_check),
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Create callback function for analysis
        async def run_analysis(analysis_interaction, tickers, start_date, end_date, indicators, view=None):
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
                        
                        # For crypto, use disambiguation data if available
                        if asset_type == "crypto" and view and hasattr(view, 'crypto_disambiguation'):
                            # Get the corresponding disambiguation data for this ticker
                            ticker_index = tickers.index(ticker)
                            coin_name = None
                            contract_address = None
                            
                            crypto_disambiguation = view.crypto_disambiguation
                            
                            if crypto_disambiguation.get('coin_names') and ticker_index < len(crypto_disambiguation['coin_names']):
                                coin_name = crypto_disambiguation['coin_names'][ticker_index]
                                if coin_name:  # Only use non-empty names
                                    coin_name = coin_name.strip()
                            
                            if crypto_disambiguation.get('contract_addresses') and ticker_index < len(crypto_disambiguation['contract_addresses']):
                                contract_address = crypto_disambiguation['contract_addresses'][ticker_index]
                                if contract_address:  # Only use non-empty addresses
                                    contract_address = contract_address.strip()
                            
                            logger.info(f"Using disambiguation for {ticker}: name='{coin_name}', contract='{contract_address}'")
                            
                            # Call crypto service with disambiguation
                            data = await asyncio.to_thread(
                                data_service.fetch_data,
                                ticker, start_date.date(), end_date.date(),
                                coin_name, contract_address
                            )
                        else:
                            # Standard call for stocks or crypto without disambiguation
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
                                    data, ticker, indicators, user_id
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
        
        # Add usage warning if approaching limits
        if usage_tracker:
            limits_check = usage_tracker.check_user_limits(user_id)
            usage_warning = _create_usage_warning(limits_check)
            if usage_warning:
                embed.add_field(
                    name="💡 Usage Info",
                    value=usage_warning,
                    inline=False
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
    else:        await interaction.response.send_message(error_message, ephemeral=True)

# HELPER FUNCTIONS FOR USAGE TRACKING
def _create_limit_message(limits_check: dict) -> str:
    """Create limit exceeded message."""
    if limits_check['monthly_usage'] >= limits_check['monthly_limit']:
        return (f"You've reached your monthly AI analysis limit of ${limits_check['monthly_limit']:.2f}.\n"
               f"Used: ${limits_check['monthly_usage']:.2f}\n\n"
               f"Your limit will reset next month.")
    elif limits_check['daily_usage'] >= limits_check['daily_limit']:
        return (f"You've reached your daily AI analysis limit of ${limits_check['daily_limit']:.2f}.\n"
               f"Used: ${limits_check['daily_usage']:.2f}\n\n"
               f"Your limit will reset tomorrow.")
    else:
        return f"You've exceeded your hourly request limit of {limits_check['hourly_limit']} requests."

def _create_usage_warning(limits_check: dict) -> str:
    """Create usage warning message."""
    monthly_pct = limits_check['monthly_usage'] / limits_check['monthly_limit'] if limits_check['monthly_limit'] > 0 else 0
    daily_pct = limits_check['daily_usage'] / limits_check['daily_limit'] if limits_check['daily_limit'] > 0 else 0
    
    if monthly_pct >= 0.8:
        return (f"⚠️ You've used {monthly_pct:.0%} of your monthly limit "
               f"(${limits_check['monthly_usage']:.2f}/${limits_check['monthly_limit']:.2f})")
    elif daily_pct >= 0.8:
        return (f"⚠️ You've used {daily_pct:.0%} of your daily limit "
               f"(${limits_check['daily_usage']:.2f}/${limits_check['daily_limit']:.2f})")
    
    return None

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
