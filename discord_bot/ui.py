"""
Interactive UI Components for Discord Bot
"""
import discord
from typing import List, Callable
from datetime import datetime

from src.config.settings import settings
from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordUI")


class DateRangeModal(discord.ui.Modal, title="Set Date Range"):
    """Modal for inputting start and end dates."""
    
    def __init__(self, view):
        super().__init__()
        self.parent_view = view
    
    start_date = discord.ui.TextInput(
        label="Start Date",
        placeholder="Enter start date (YYYY-MM-DD), e.g., 2024-01-01",
        default="2024-01-01",
        max_length=10,
        required=True
    )
    
    end_date = discord.ui.TextInput(
        label="End Date", 
        placeholder="Enter end date (YYYY-MM-DD), e.g., 2024-12-31",
        default="2024-12-31",
        max_length=10,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle date range submission."""
        try:
            # Parse the dates
            start_date_obj = datetime.strptime(self.start_date.value, "%Y-%m-%d")
            end_date_obj = datetime.strptime(self.end_date.value, "%Y-%m-%d")
            
            # Validate date range
            if start_date_obj >= end_date_obj:
                await interaction.response.send_message(
                    "Start date must be before end date!", ephemeral=True
                )
                return
            
            # Update the view's dates
            self.parent_view.start_date = start_date_obj
            self.parent_view.end_date = end_date_obj
            
            # Update the embed to show the new date range
            embed = create_indicator_selection_embed(
                self.parent_view.tickers,
                self.parent_view.start_date,
                self.parent_view.end_date, 
                self.parent_view.selected_indicators
            )
            
            await interaction.response.edit_message(embed=embed, view=self.parent_view)
            
        except ValueError:
            await interaction.response.send_message(
                "Invalid date format! Please use YYYY-MM-DD format (e.g., 2024-01-01)", 
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in date range modal: {e}")
            await interaction.response.send_message(
                "An error occurred while setting the date range.", ephemeral=True
            )


class IndicatorSelectionView(discord.ui.View):
    """View for selecting technical indicators with toggle buttons."""
    
    def __init__(self, parent_view):
        super().__init__(timeout=60)  # 1 minute timeout for this sub-view
        self.parent_view = parent_view
        self.available_indicators = ["20-Day SMA", "20-Day EMA", "Bollinger Bands", "VWAP"]
    
    def get_button_style(self, indicator: str) -> discord.ButtonStyle:
        """Get button style based on selection state."""
        return discord.ButtonStyle.green if indicator in self.parent_view.selected_indicators else discord.ButtonStyle.secondary
    
    @discord.ui.button(label="20-Day SMA", style=discord.ButtonStyle.green, row=0)
    async def toggle_sma(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle 20-Day SMA indicator."""
        await self._toggle_indicator(interaction, "20-Day SMA", button)
    
    @discord.ui.button(label="20-Day EMA", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_ema(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle 20-Day EMA indicator."""
        await self._toggle_indicator(interaction, "20-Day EMA", button)
    
    @discord.ui.button(label="Bollinger Bands", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_bollinger(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle Bollinger Bands indicator."""
        await self._toggle_indicator(interaction, "Bollinger Bands", button)
    
    @discord.ui.button(label="VWAP", style=discord.ButtonStyle.secondary, row=1)
    async def toggle_vwap(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Toggle VWAP indicator."""
        await self._toggle_indicator(interaction, "VWAP", button)
    
    @discord.ui.button(label="Done", style=discord.ButtonStyle.primary, row=2)
    async def done_selecting(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Finish indicator selection."""
        try:
            # Ensure at least one indicator is selected
            if not self.parent_view.selected_indicators:
                await interaction.response.send_message(
                    "Please select at least one indicator!", ephemeral=True
                )
                return
            
            logger.info(f"User finished selecting indicators: {self.parent_view.selected_indicators}")
            
            # Update the main embed to show selected indicators
            embed = create_indicator_selection_embed(
                self.parent_view.tickers,
                self.parent_view.start_date,
                self.parent_view.end_date, 
                self.parent_view.selected_indicators
            )
            
            await interaction.response.edit_message(embed=embed, view=self.parent_view)
            
        except Exception as e:
            logger.error(f"Error finishing indicator selection: {e}")
            await interaction.response.send_message(
                "An error occurred while saving indicator selection.", ephemeral=True
            )
    
    async def _toggle_indicator(self, interaction: discord.Interaction, indicator: str, button: discord.ui.Button):
        """Toggle an indicator on/off."""
        try:
            if indicator in self.parent_view.selected_indicators:
                # Remove indicator
                self.parent_view.selected_indicators.remove(indicator)
                button.style = discord.ButtonStyle.secondary
            else:
                # Add indicator
                self.parent_view.selected_indicators.append(indicator)
                button.style = discord.ButtonStyle.green
            
            logger.info(f"Toggled {indicator}. Current selection: {self.parent_view.selected_indicators}")
            
            # Create updated embed showing current selection
            embed = discord.Embed(
                title="Select Technical Indicators",
                description=f"**Current Selection:** {', '.join(self.parent_view.selected_indicators) if self.parent_view.selected_indicators else 'None'}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Available Indicators",
                value="\n".join([
                    "• 20-Day SMA - Simple Moving Average",
                    "• 20-Day EMA - Exponential Moving Average", 
                    "• Bollinger Bands - Volatility bands",
                    "• VWAP - Volume Weighted Average Price"
                ]),
                inline=False
            )
            
            embed.add_field(
                name="Instructions",
                value="Click indicators to toggle them on/off (green = selected)\nClick **Done** when finished selecting",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error toggling indicator {indicator}: {e}")
            await interaction.response.send_message(
                "An error occurred while toggling the indicator.", ephemeral=True
            )


class IndicatorSelectView(discord.ui.View):
    """Interactive view for selecting technical indicators and date range."""
    
    def __init__(self, tickers: List[str], callback: Callable):
        super().__init__(timeout=300)  # 5 minute timeout
        self.tickers = tickers
        self.callback = callback
        self.selected_indicators = ["20-Day SMA"]  # Default selection
        self.start_date = None
        self.end_date = None
    
    @discord.ui.button(label="Select Indicators", style=discord.ButtonStyle.secondary, row=0)
    async def select_indicators(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open indicator selection interface."""
        try:
            # Create the indicator selection view
            indicator_view = IndicatorSelectionView(self)
            
            # Create embed for indicator selection
            embed = discord.Embed(
                title="Select Technical Indicators",
                description=f"**Current Selection:** {', '.join(self.selected_indicators) if self.selected_indicators else 'None'}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Available Indicators",
                value="\n".join([
                    "• 20-Day SMA - Simple Moving Average",
                    "• 20-Day EMA - Exponential Moving Average", 
                    "• Bollinger Bands - Volatility bands",
                    "• VWAP - Volume Weighted Average Price"
                ]),
                inline=False
            )
            
            embed.add_field(
                name="Instructions",
                value="Click indicators to toggle them on/off (green = selected)\nClick **Done** when finished selecting",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=indicator_view)
            
        except Exception as e:
            logger.error(f"Error opening indicator selection: {e}")
            await interaction.response.send_message(
                "An error occurred while opening indicator selection.", ephemeral=True
            )
    
    @discord.ui.button(label="Set Date Range", style=discord.ButtonStyle.secondary, row=1)
    async def set_date_range(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open modal to set date range."""
        modal = DateRangeModal(self)
        await interaction.response.send_modal(modal)
        
    @discord.ui.button(label="Start Analysis", style=discord.ButtonStyle.green, row=1)
    async def start_analysis(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start the analysis with selected indicators."""
        try:
            # Check if dates are set
            if not self.start_date or not self.end_date:
                await interaction.response.send_message(
                    "Please set a date range first using the 'Set Date Range' button!", 
                    ephemeral=True
                )
                return
            
            logger.info(f"Starting analysis for tickers: {self.tickers}")
            logger.info(f"Selected indicators for analysis: {self.selected_indicators}")
            logger.info(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
            
            # Defer the interaction response since analysis will take time
            await interaction.response.defer()
            
            # Disable the view
            for item in self.children:
                item.disabled = True
            
            # Update the message to show analysis is starting
            embed = discord.Embed(
                title="Analysis Starting...",
                description=f"Analyzing {', '.join(self.tickers)} with indicators: {', '.join(self.selected_indicators)}\nDate Range: {self.start_date.date()} to {self.end_date.date()}\nThis may take a few moments...",
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


def create_indicator_selection_embed(
    tickers: List[str], 
    start_date: datetime = None, 
    end_date: datetime = None,
    selected_indicators: List[str] = None
) -> discord.Embed:
    """Create an embed for the indicator selection interface."""
    
    # Format date range display
    if start_date and end_date:
        date_range = f"**Period:** {start_date.date()} to {end_date.date()}"
    else:
        date_range = "**Period:** Not set (use 'Set Date Range' button)"
    
    embed = discord.Embed(
        title="Technical Analysis Setup",
        description=f"**Tickers:** {', '.join(tickers)}\n{date_range}",
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
        value="1. Click **Select Indicators** to choose technical indicators\n2. Click **Set Date Range** to choose analysis period\n3. Click **Start Analysis** to begin\n4. Click **Cancel** to abort",
        inline=False
    )
    
    embed.set_footer(text="Selection will timeout in 5 minutes")
    
    return embed
