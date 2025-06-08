"""
Interactive UI Components for Discord Bot
"""
import discord
from typing import List, Callable
from datetime import datetime

from src.config.settings import settings
from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordUI")

class IndicatorSelectView(discord.ui.View):
    """Interactive view for selecting technical indicators."""
    
    def __init__(self, tickers: List[str], start_date: datetime, end_date: datetime, callback: Callable):
        super().__init__(timeout=300)  # 5 minute timeout
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.callback = callback
        self.selected_indicators = ["20-Day SMA"]  # Default selection
    @discord.ui.select(
        placeholder="Select technical indicators (multiple allowed)...",
        min_values=1,
        max_values=4,
        row=0,
        options=[
            discord.SelectOption(
                label="20-Day SMA",
                description="Simple Moving Average (20 days)",
                default=True
            ),
            discord.SelectOption(
                label="20-Day EMA", 
                description="Exponential Moving Average (20 days)"
            ),
            discord.SelectOption(
                label="Bollinger Bands",
                description="Volatility indicator bands"
            ),            discord.SelectOption(
                label="VWAP",
                description="Volume Weighted Average Price"
            )
        ]
    )
    async def indicator_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Handle indicator selection."""
        self.selected_indicators = select.values
        logger.info(f"User selected indicators: {self.selected_indicators}")
        
        # Update the dropdown options to reflect current selection
        self._update_dropdown_options()
        
        # Update the embed to show selected indicators
        embed = create_indicator_selection_embed(
            self.tickers, 
            self.start_date, 
            self.end_date,
            self.selected_indicators
        )
        
        # Use edit_message for immediate response - don't defer here
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Start Analysis", style=discord.ButtonStyle.green, row=1)
    async def start_analysis(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start the analysis with selected indicators."""
        try:
            logger.info(f"Starting analysis for tickers: {self.tickers}")
            logger.info(f"Selected indicators for analysis: {self.selected_indicators}")
            
            # Defer the interaction response since analysis will take time
            await interaction.response.defer()
            
            # Disable the view
            for item in self.children:
                item.disabled = True
            
            # Update the message to show analysis is starting
            embed = discord.Embed(
                title="Analysis Starting...",
                description=f"Analyzing {', '.join(self.tickers)} with indicators: {', '.join(self.selected_indicators)}\nThis may take a few moments...",
                color=discord.Color.orange()
            )
            
            await interaction.edit_original_response(embed=embed, view=self)
            
            # Run the analysis callback
            logger.info(f"Calling analysis callback with indicators: {self.selected_indicators}")
            await self.callback(interaction, self.tickers, self.start_date, self.end_date, self.selected_indicators)
            
        except Exception as e:
            logger.error(f"Error in start_analysis: {e}")
            try:
                await interaction.followup.send("An error occurred while starting the analysis.", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, row=1)
    async def cancel_analysis(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the analysis."""
        try:
            logger.info("Analysis cancelled by user")
            
            # Disable the view
            for item in self.children:
                item.disabled = True
            
            embed = discord.Embed(
                title="Analysis Cancelled",
                description="The analysis has been cancelled.",
                color=discord.Color.red()
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error in cancel_analysis: {e}")
            try:
                await interaction.response.send_message("Analysis cancelled.", ephemeral=True)
            except:
                pass
    
    async def on_timeout(self):
        """Handle view timeout."""
        logger.info("Indicator selection view timed out")
        
        # Disable all items
        for item in self.children:
            item.disabled = True

    def _update_dropdown_options(self):
        """Update the dropdown options to reflect current selection."""
        # Get the select component
        select_component = self.children[0]  # First component is the select dropdown
        
        # Create new options with updated default states
        new_options = [
            discord.SelectOption(
                label="20-Day SMA",
                description="Simple Moving Average (20 days)",
                default="20-Day SMA" in self.selected_indicators
            ),
            discord.SelectOption(
                label="20-Day EMA", 
                description="Exponential Moving Average (20 days)",
                default="20-Day EMA" in self.selected_indicators
            ),
            discord.SelectOption(
                label="Bollinger Bands",
                description="Volatility indicator bands",
                default="Bollinger Bands" in self.selected_indicators
            ),
            discord.SelectOption(
                label="VWAP",
                description="Volume Weighted Average Price",
                default="VWAP" in self.selected_indicators
            )
        ]
        
        # Update the select component options
        select_component.options = new_options

def create_indicator_selection_embed(
    tickers: List[str], 
    start_date: datetime, 
    end_date: datetime,
    selected_indicators: List[str] = None
) -> discord.Embed:
    """Create an embed for the indicator selection interface."""
    embed = discord.Embed(
        title="Technical Analysis Setup",
        description=f"**Tickers:** {', '.join(tickers)}\n**Period:** {start_date.date()} to {end_date.date()}",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="Available Indicators",
        value="\n".join([
            "20-Day SMA - Simple Moving Average",
            "20-Day EMA - Exponential Moving Average", 
            "Bollinger Bands - Volatility bands",
            "VWAP - Volume Weighted Average Price"
        ]),
        inline=False
    )
    
    if selected_indicators:
        embed.add_field(
            name="Selected Indicators",
            value="\n".join([f"• {indicator}" for indicator in selected_indicators]),
            inline=False
        )
    
    embed.add_field(
        name="Instructions",
        value="1. Select one or more indicators from the dropdown\n2. Click **Start Analysis** to begin\n3. Click **Cancel** to abort",
        inline=False
    )
    
    embed.set_footer(text="Selection will timeout in 5 minutes")
    
    return embed
