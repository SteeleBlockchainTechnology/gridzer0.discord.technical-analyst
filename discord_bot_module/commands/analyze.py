"""
Analyze command for technical analysis.
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from .base import BaseCommand
from ..utils.parsers import parse_comma_separated_string, parse_date_string
from ..utils.validators import validate_indicators
from ..embeds.analysis_embeds import create_analysis_embed, create_error_embed, create_summary_embed
from src.config.settings import settings
from src.utils.logging_utils import setup_logger

logger = setup_logger("AnalyzeCommand")

class AnalyzeCommand(BaseCommand):
    """Handle the analyze command for technical analysis."""
    
    async def process_ticker(self, ticker: str, start_date: datetime, end_date: datetime, indicators: List[str]):
        """Process a single ticker analysis."""
        try:
            # Fetch market data
            logger.info(f"Fetching data for {ticker}")
            data = await asyncio.to_thread(
                self.bot.market_data_service.fetch_data,
                ticker, start_date.date(), end_date.date()
            )
            
            if data.empty:
                return create_error_embed(ticker, "No data available for this ticker.")
            
            # Generate technical analysis
            logger.info(f"Generating analysis for {ticker}")
            
            # Create chart
            fig = self.bot.technical_analysis_service.create_candlestick_chart(
                data, ticker, indicators
            )
            
            # Export chart as image
            img_buffer = self.bot.technical_analysis_service.export_chart_as_image(fig)
            
            if img_buffer:
                # Create Discord file
                img_buffer.seek(0)
                discord_file = discord.File(img_buffer, filename=f"{ticker}_chart.png")
                
                # Generate technical summary
                technical_summary = self.bot.technical_analysis_service.generate_technical_data_summary(
                    data, ticker, indicators
                )
                
                # Get AI analysis
                try:
                    ai_analysis = await asyncio.to_thread(
                        self.bot.ai_analysis_service.analyze_stock_data,
                        data, ticker, indicators
                    )
                except Exception as e:
                    logger.error(f"AI analysis failed for {ticker}: {e}")
                    ai_analysis = "AI analysis unavailable."
                
                # Create embed for this ticker
                embed = create_analysis_embed(
                    ticker, technical_summary, ai_analysis, 
                    start_date, end_date, indicators
                )
                
                return embed, discord_file
                
            else:
                # Fallback if image generation fails
                technical_summary = self.bot.technical_analysis_service.generate_technical_data_summary(
                    data, ticker, indicators
                )
                
                embed = create_analysis_embed(
                    ticker, technical_summary, None, 
                    start_date, end_date, indicators
                )
                embed.set_footer(text="Chart generation failed.")
                
                return embed, None
                
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            return create_error_embed(ticker, f"Error processing ticker: {str(e)[:1000]}"), None

@app_commands.describe(
    tickers="Comma-separated ticker symbols (e.g., 'AAPL,GOOGL' or 'BTC,ETH')",
    start_date="Start date in YYYY-MM-DD format (e.g., '2023-01-01')",
    end_date="End date in YYYY-MM-DD format (e.g., '2023-12-31')",
    indicators="Comma-separated indicators (e.g., '20-Day SMA,20-Day EMA')"
)
async def analyze_command(
    interaction: discord.Interaction,
    tickers: str,
    start_date: str = None,
    end_date: str = None,
    indicators: str = "20-Day SMA"
):
    """Analyze stocks or cryptocurrencies with technical indicators."""
    
    command_handler = AnalyzeCommand(interaction.client)
    
    # Defer the response since analysis might take time
    await command_handler.defer_response(interaction)
    
    try:
        logger.info(f"Analysis command received from {interaction.user}: tickers={tickers}")
        
        # Parse and validate inputs
        ticker_list = parse_comma_separated_string(tickers)
        if not ticker_list:
            await command_handler.send_error(
                interaction, 
                "Please provide at least one valid ticker symbol."
            )
            return
        
        # Parse dates
        if start_date:
            parsed_start_date = parse_date_string(start_date)
            if not parsed_start_date:
                await command_handler.send_error(
                    interaction,
                    "Invalid start date format. Please use YYYY-MM-DD format."
                )
                return
        else:
            # Default to 1 year ago
            parsed_start_date = datetime.now() - timedelta(days=settings.DEFAULT_LOOKBACK_DAYS)
        
        if end_date:
            parsed_end_date = parse_date_string(end_date)
            if not parsed_end_date:
                await command_handler.send_error(
                    interaction,
                    "Invalid end date format. Please use YYYY-MM-DD format."
                )
                return
        else:
            # Default to today
            parsed_end_date = datetime.now()
        
        # Parse and validate indicators
        indicator_list = parse_comma_separated_string(indicators)
        valid_indicators = validate_indicators(indicator_list)
        
        if not valid_indicators:
            await command_handler.send_error(
                interaction,
                f"No valid indicators provided. Supported indicators: {', '.join(settings.TECHNICAL_INDICATORS)}"
            )
            return
        
        # Process each ticker
        embeds = []
        files = []
        
        for ticker in ticker_list:
            result = await command_handler.process_ticker(
                ticker, parsed_start_date, parsed_end_date, valid_indicators
            )
            
            if isinstance(result, tuple):
                embed, file = result
                embeds.append(embed)
                if file:
                    files.append(file)
            else:
                embeds.append(result)
        
        # Send results
        if embeds:
            # Send embeds in batches (Discord limit: 10 embeds per message)
            for i in range(0, len(embeds), 10):
                batch_embeds = embeds[i:i+10]
                batch_files = files[i:i+10] if files else None
                
                await interaction.followup.send(embeds=batch_embeds, files=batch_files)
                    
            # Send summary if multiple tickers
            if len(ticker_list) > 1:
                summary_embed = create_summary_embed(
                    ticker_list, parsed_start_date, parsed_end_date, valid_indicators
                )
                await interaction.followup.send(embed=summary_embed)
        else:
            await command_handler.send_error(
                interaction,
                "No data could be processed for the provided tickers."
            )
            
    except Exception as e:
        logger.error(f"Error in analyze command: {e}")
        await command_handler.send_error(
            interaction,
            f"An error occurred: {str(e)[:1000]}"
        )

def setup(bot: commands.Bot):
    """Setup the analyze command."""
    bot.tree.add_command(app_commands.Command(
        name="analyze",
        description="Analyze stocks or cryptocurrencies with technical indicators",
        callback=analyze_command
    ))
