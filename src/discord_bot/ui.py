"""
Interactive UI Components for Discord Bot

This module provides Discord UI components for technical analysis setup:
- DateRangeModal: Input modal for date range selection
- IndicatorSelectionView: Dynamic toggle buttons for technical indicators
- IndicatorSelectView: Main view orchestrating the analysis setup
"""
import discord
from typing import List, Callable, Optional
from datetime import datetime, timedelta, timezone

from src.config.settings import settings
from src.utils.logging_utils import setup_logger

logger = setup_logger("DiscordUI")

# Constants for better maintainability
DEFAULT_TIMEOUT = 300  # 5 minutes
SELECTION_TIMEOUT = 60  # 1 minute for sub-views
MAX_DATE_RANGE_DAYS = 365 * 5  # 5 years maximum
MIN_DATE_RANGE_DAYS = 1  # 1 day minimum

# Available technical indicators with descriptions
AVAILABLE_INDICATORS = {
    "20-Day SMA": "Simple Moving Average",
    "20-Day EMA": "Exponential Moving Average", 
    "Bollinger Bands": "Volatility bands",
    "VWAP": "Volume Weighted Average Price"
}


class DateRangeModal(discord.ui.Modal, title="Set Date Range"):
    """Modal for inputting start and end dates with enhanced validation."""
    
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        
        # Calculate dynamic default dates (timezone-aware)
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        one_year_ago = today - timedelta(days=364)
        
        # Create text inputs with dynamic defaults
        self.start_date_input = discord.ui.TextInput(
            label="Start Date",
            placeholder=f"Format: YYYY-MM-DD (e.g., {one_year_ago.strftime('%Y-%m-%d')})",
            default=one_year_ago.strftime('%Y-%m-%d'),
            max_length=10,
            required=True
        )
        
        self.end_date_input = discord.ui.TextInput(
            label="End Date", 
            placeholder=f"Format: YYYY-MM-DD (e.g., {today.strftime('%Y-%m-%d')})",
            default=today.strftime('%Y-%m-%d'),
            max_length=10,
            required=True
        )
        
        # Add the text inputs to the modal
        self.add_item(self.start_date_input)
        self.add_item(self.end_date_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle date range submission with comprehensive validation."""
        try:
            # Parse the dates
            start_date_str = self.start_date_input.value.strip()
            end_date_str = self.end_date_input.value.strip()
            
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                await interaction.response.send_message(
                    f"Invalid start date format: '{start_date_str}'. Please use YYYY-MM-DD format (e.g., 2024-01-01)", 
                    ephemeral=True
                )
                return
            
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                await interaction.response.send_message(
                    f"Invalid end date format: '{end_date_str}'. Please use YYYY-MM-DD format (e.g., 2024-12-31)", 
                    ephemeral=True
                )
                return
            
            # Validate date range logic
            if start_date >= end_date:
                await interaction.response.send_message(
                    f"Start date ({start_date_str}) must be before end date ({end_date_str})!", 
                    ephemeral=True
                )
                return
            
            # Validate date range constraints
            date_range_days = (end_date - start_date).days
            if date_range_days < MIN_DATE_RANGE_DAYS:
                await interaction.response.send_message(
                    f"Date range is too short ({date_range_days} days). Minimum is {MIN_DATE_RANGE_DAYS} day(s).", 
                    ephemeral=True
                )
                return
            
            if date_range_days > MAX_DATE_RANGE_DAYS:
                await interaction.response.send_message(
                    f"Date range is too long ({date_range_days} days). Maximum is {MAX_DATE_RANGE_DAYS} days ({MAX_DATE_RANGE_DAYS // 365} years).", 
                    ephemeral=True
                )
                return
            
            # Validate dates are not in the future
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            if end_date > today:
                await interaction.response.send_message(
                    f"End date ({end_date_str}) cannot be in the future. Latest allowed date is {today.strftime('%Y-%m-%d')}.", 
                    ephemeral=True
                )
                return
            
            # Update the parent view's dates
            self.parent_view.start_date = start_date
            self.parent_view.end_date = end_date
            
            logger.info(f"Date range updated: {start_date_str} to {end_date_str} ({date_range_days} days)")
            
            # Update the embed to show the new date range
            embed = create_indicator_selection_embed(
                self.parent_view.tickers,
                self.parent_view.start_date,
                self.parent_view.end_date, 
                self.parent_view.selected_indicators
            )
            
            await interaction.response.edit_message(embed=embed, view=self.parent_view)
            
        except Exception as e:
            error_msg = f"Unexpected error setting date range: {str(e)}"
            logger.error(error_msg)
            await interaction.response.send_message(
                "An unexpected error occurred while setting the date range. Please try again.", 
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        """Handle modal errors gracefully."""
        logger.error(f"DateRangeModal error: {error}")
        try:
            await interaction.response.send_message(
                "An error occurred while processing your date input. Please try again.", 
                ephemeral=True
            )
        except:
            # In case interaction was already responded to
            pass


class IndicatorSelectionView(discord.ui.View):
    """
    Dynamic view for selecting technical indicators with toggle buttons.
    Generates buttons dynamically from available indicators for easy extension.
    """
    
    def __init__(self, parent_view):
        super().__init__(timeout=SELECTION_TIMEOUT)
        self.parent_view = parent_view
        self._setup_dynamic_buttons()
    
    def _setup_dynamic_buttons(self):
        """Dynamically create toggle buttons for all available indicators."""
        indicators = list(AVAILABLE_INDICATORS.keys())
        
        # Create toggle buttons dynamically (4 per row max)
        for i, indicator in enumerate(indicators):
            row = i // 4  # 4 buttons per row
            style = self._get_button_style(indicator)
            
            # Create button with dynamic callback
            button = discord.ui.Button(
                label=indicator,
                style=style,
                row=row,
                custom_id=f"toggle_{indicator.replace(' ', '_').replace('-', '_').lower()}"
            )
            
            # Bind the callback dynamically
            button.callback = self._create_toggle_callback(indicator, button)
            self.add_item(button)
          # Add control buttons on the last row
        button_row = len(indicators) // 4 + 1
        
        # Select All button
        select_all_button = discord.ui.Button(
            label="Select All",
            style=discord.ButtonStyle.secondary,
            row=button_row,
            custom_id="select_all",
            emoji="✅"
        )
        select_all_button.callback = self._select_all_callback
        self.add_item(select_all_button)
        
        # Clear All button
        clear_all_button = discord.ui.Button(
            label="Clear All",
            style=discord.ButtonStyle.secondary,
            row=button_row,
            custom_id="clear_all",
            emoji="❌"
        )
        clear_all_button.callback = self._clear_all_callback
        self.add_item(clear_all_button)
        
        # Done button
        done_button = discord.ui.Button(
            label="✓ Done",
            style=discord.ButtonStyle.primary,
            row=button_row,
            custom_id="done_selecting"
        )
        done_button.callback = self._done_selecting_callback
        self.add_item(done_button)
    
    def _get_button_style(self, indicator: str) -> discord.ButtonStyle:
        """Get button style based on selection state."""
        return discord.ButtonStyle.green if indicator in self.parent_view.selected_indicators else discord.ButtonStyle.secondary
    def _create_toggle_callback(self, indicator: str, button: discord.ui.Button):
        """Create a toggle callback for a specific indicator."""
        async def toggle_callback(interaction: discord.Interaction):
            await self._toggle_indicator(interaction, indicator, button)
        return toggle_callback
    
    async def _toggle_indicator(self, interaction: discord.Interaction, indicator: str, button: discord.ui.Button):
        """Toggle an indicator on/off with instant response."""
        try:
            is_selected = indicator in self.parent_view.selected_indicators
            
            if is_selected:
                # Remove indicator
                self.parent_view.selected_indicators.remove(indicator)
                button.style = discord.ButtonStyle.secondary
                action = "deselected"
            else:
                # Add indicator
                self.parent_view.selected_indicators.append(indicator)
                button.style = discord.ButtonStyle.green
                action = "selected"
            
            logger.info(f"Indicator {indicator} {action}. Current selection: {self.parent_view.selected_indicators}")
            
            # Update the Done button label to show selection count
            done_button = None
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == "done_selecting":
                    done_button = item
                    break
            
            if done_button:
                selected_count = len(self.parent_view.selected_indicators)
                if selected_count > 0:
                    done_button.label = f"✓ Done ({selected_count})"
                    done_button.style = discord.ButtonStyle.success
                else:
                    done_button.label = "✓ Done"
                    done_button.style = discord.ButtonStyle.primary
              # Quick response - just update the view without changing the embed
            await interaction.response.edit_message(view=self)
            
        except Exception as e:
            error_msg = f"Error toggling indicator {indicator}: {str(e)}"
            logger.error(error_msg)
            await interaction.response.send_message(
                f"An error occurred while toggling {indicator}. Please try again.", 
                ephemeral=True
            )
    
    async def _select_all_callback(self, interaction: discord.Interaction):
        """Select all available indicators."""
        try:
            # Add all indicators to selection if not already selected
            all_indicators = list(AVAILABLE_INDICATORS.keys())
            self.parent_view.selected_indicators = all_indicators.copy()
            
            logger.info(f"Selected all indicators: {self.parent_view.selected_indicators}")
            
            # Update all indicator button styles to green
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id.startswith('toggle_'):
                    item.style = discord.ButtonStyle.green
            
            # Update the Done button to show selection count
            done_button = None
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == "done_selecting":
                    done_button = item
                    break
            
            if done_button:
                selected_count = len(self.parent_view.selected_indicators)
                done_button.label = f"✓ Done ({selected_count})"
                done_button.style = discord.ButtonStyle.success
            
            # Quick response - just update the view
            await interaction.response.edit_message(view=self)
            
        except Exception as e:
            error_msg = f"Error selecting all indicators: {str(e)}"
            logger.error(error_msg)
            await interaction.response.send_message(
                "An error occurred while selecting all indicators. Please try again.", 
                ephemeral=True
            )
    
    async def _clear_all_callback(self, interaction: discord.Interaction):
        """Clear all selected indicators."""
        try:
            # Clear all selections
            self.parent_view.selected_indicators = []
            
            logger.info("Cleared all indicator selections")
            
            # Update all indicator button styles to secondary
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id.startswith('toggle_'):
                    item.style = discord.ButtonStyle.secondary
            
            # Update the Done button to default state
            done_button = None
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == "done_selecting":
                    done_button = item
                    break
            
            if done_button:
                done_button.label = "✓ Done"
                done_button.style = discord.ButtonStyle.primary
            
            # Quick response - just update the view
            await interaction.response.edit_message(view=self)
            
        except Exception as e:
            error_msg = f"Error clearing all indicators: {str(e)}"
            logger.error(error_msg)
            await interaction.response.send_message(
                "An error occurred while clearing indicators. Please try again.", 
                ephemeral=True
            )
    
    async def _done_selecting_callback(self, interaction: discord.Interaction):
        """Handle completion of indicator selection."""
        try:
            # Ensure at least one indicator is selected
            if not self.parent_view.selected_indicators:
                await interaction.response.send_message(
                    "Please select at least one technical indicator before proceeding!", 
                    ephemeral=True
                )
                return
            
            logger.info(f"User completed indicator selection: {self.parent_view.selected_indicators}")
            
            # Update the main embed to show selected indicators
            embed = create_indicator_selection_embed(
                self.parent_view.tickers,
                self.parent_view.start_date,
                self.parent_view.end_date, 
                self.parent_view.selected_indicators
            )
            
            await interaction.response.edit_message(embed=embed, view=self.parent_view)
        except Exception as e:
            error_msg = f"Error completing indicator selection: {str(e)}"
            logger.error(error_msg)
            await interaction.response.send_message(
                "An error occurred while saving your indicator selection. Please try again.", 
                ephemeral=True
            )
    
    def _create_selection_embed(self) -> discord.Embed:
        """Create embed showing current indicator selection state."""
        selected_count = len(self.parent_view.selected_indicators)
        total_count = len(AVAILABLE_INDICATORS)
        
        # Dynamic title based on selection status
        if selected_count == 0:
            title = "📊 Select Technical Indicators"
            description = "Click indicators below to start your selection"
        else:
            title = f"📊 Indicators Selected: {selected_count}/{total_count}"
            description = "Continue selecting or click **✓ Done** when finished"
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue() if selected_count > 0 else discord.Color.orange()
        )
        
        # Show currently selected indicators
        if self.parent_view.selected_indicators:
            selected_list = "\n".join([f"✅ {ind}" for ind in self.parent_view.selected_indicators])
            embed.add_field(
                name="Your Selection",
                value=selected_list,
                inline=True
            )
        
        # Show available indicators with descriptions
        available_list = "\n".join([
            f"• **{ind}** - {desc}" 
            for ind, desc in AVAILABLE_INDICATORS.items()
        ])        
        embed.add_field(
            name="Available Indicators",
            value=available_list,
            inline=False
        )
        
        embed.add_field(
            name="Quick Selection Tips",
            value="🔵 = Available • 🟢 = Selected • Click to toggle\n✅ **Select All** • ❌ **Clear All** • ✓ **Done** when finished",
            inline=False
        )
        
        return embed
    
    async def on_timeout(self):
        """Handle timeout by disabling all buttons."""
        logger.info("Indicator selection view timed out")
        for item in self.children:
            item.disabled = True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        """Handle view errors gracefully."""
        logger.error(f"IndicatorSelectionView error: {error}")
        try:
            await interaction.response.send_message(
                "An error occurred with the indicator selection. Please try again.", 
                ephemeral=True
            )
        except:
            pass


class IndicatorSelectView(discord.ui.View):
    """
    Main interactive view for technical analysis setup.
    Orchestrates indicator selection, date range setting, and analysis initiation.
    """
    def __init__(self, tickers: List[str], callback: Callable):
        super().__init__(timeout=DEFAULT_TIMEOUT)
        self.tickers = tickers
        self.callback = callback
        self.selected_indicators = ["20-Day SMA"]  # Default selection for better UX
        
        # Set default date range to last year (timezone-aware)
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        one_year_ago = today - timedelta(days=364)
        self.start_date: Optional[datetime] = one_year_ago
        self.end_date: Optional[datetime] = today
        self._analysis_started = False  # Prevent multiple analysis starts
        
        logger.info(f"Initialized with default date range: {one_year_ago.date()} to {today.date()}")
    
    @discord.ui.button(
        label="Select Indicators", 
        style=discord.ButtonStyle.secondary, 
        row=0,
        emoji="📊"
    )
    async def select_indicators(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open dynamic indicator selection interface."""
        try:
            logger.info(f"Opening indicator selection for user {interaction.user.display_name}")
            
            # Create the indicator selection view
            indicator_view = IndicatorSelectionView(self)
            
            # Create embed for indicator selection
            embed = indicator_view._create_selection_embed()
            await interaction.response.edit_message(embed=embed, view=indicator_view)
            
        except Exception as e:
            error_msg = f"Error opening indicator selection: {str(e)}"
            logger.error(error_msg)
            await interaction.response.send_message(
                "An error occurred while opening indicator selection. Please try again.", 
                ephemeral=True
            )
    
    @discord.ui.button(
        label="Change Date Range", 
        style=discord.ButtonStyle.secondary, 
        row=0,
        emoji="📅"
    )
    async def set_date_range(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open modal to set date range."""
        try:
            logger.info(f"Opening date range modal for user {interaction.user.display_name}")
            modal = DateRangeModal(self)
            await interaction.response.send_modal(modal)
        except Exception as e:
            error_msg = f"Error opening date range modal: {str(e)}"
            logger.error(error_msg)
            await interaction.response.send_message(
                "An error occurred while opening the date selector. Please try again.", 
                ephemeral=True
            )
    
    @discord.ui.button(
        label="Reset All", 
        style=discord.ButtonStyle.secondary, 
        row=1,
        emoji="🔄"
    )
    async def reset_selections(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reset all selections to defaults."""
        try:
            logger.info(f"Resetting selections for user {interaction.user.display_name}")
              # Reset to defaults
            self.selected_indicators = ["20-Day SMA"]
            
            # Reset date range to default (last year)
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            one_year_ago = today - timedelta(days=364)
            self.start_date = one_year_ago
            self.end_date = today
            self._analysis_started = False
            
            # Re-enable all buttons in case they were disabled
            for item in self.children:
                item.disabled = False
            
            # Update embed to show reset state
            embed = create_indicator_selection_embed(
                self.tickers,
                self.start_date,
                self.end_date, 
                self.selected_indicators
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            error_msg = f"Error resetting selections: {str(e)}"
            logger.error(error_msg)
            await interaction.response.send_message(
                "An error occurred while resetting selections. Please try again.", 
                ephemeral=True
            )
        
    @discord.ui.button(
        label="Start Analysis", 
        style=discord.ButtonStyle.green, 
        row=1,
        emoji="▶️"
    )
    async def start_analysis(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start the analysis with comprehensive validation."""
        if self._analysis_started:
            await interaction.response.send_message(
                "Analysis is already in progress. Please wait for it to complete.", 
                ephemeral=True
            )
            return
        
        try:
            # Validate prerequisites
            validation_error = self._validate_analysis_prerequisites()
            if validation_error:
                await interaction.response.send_message(validation_error, ephemeral=True)
                return
            
            logger.info(f"Starting analysis for user {interaction.user.display_name}")
            logger.info(f"Tickers: {self.tickers}")
            logger.info(f"Indicators: {self.selected_indicators}")
            logger.info(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
            
            # Mark analysis as started and defer response
            self._analysis_started = True
            await interaction.response.defer()
            
            # Disable the view during analysis
            self._disable_view()
            
            # Update message to show analysis is starting
            embed = self._create_analysis_starting_embed()
            await interaction.edit_original_response(embed=embed, view=self)
            
            # Execute the analysis callback
            await self.callback(interaction, self.tickers, self.start_date, self.end_date, self.selected_indicators)
            
        except Exception as e:
            self._analysis_started = False  # Reset flag on error
            error_msg = f"Error starting analysis: {str(e)}"
            logger.error(error_msg)
            try:
                await interaction.followup.send(
                    "An error occurred while starting the analysis. Please try again.", 
                    ephemeral=True
                )
            except:
                # In case followup fails, try alternative approach
                pass
    
    @discord.ui.button(
        label="Cancel", 
        style=discord.ButtonStyle.red, 
        row=1,
    )
    async def cancel_analysis(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the analysis setup."""
        try:
            logger.info(f"Analysis cancelled by user {interaction.user.display_name}")
            
            # Disable the view
            self._disable_view()
            
            embed = discord.Embed(
                title="❌ Analysis Cancelled",
                description="The technical analysis setup has been cancelled.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="Status",
                value="You can start a new analysis anytime using `/analyze`",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            error_msg = f"Error cancelling analysis: {str(e)}"
            logger.error(error_msg)
            try:
                await interaction.response.send_message("Analysis cancelled.", ephemeral=True)
            except:
                pass
    
    def _validate_analysis_prerequisites(self) -> Optional[str]:
        """Validate all prerequisites for starting analysis."""
        if not self.selected_indicators:
            return "Please select at least one technical indicator using the '📊 Select Indicators' button!"
        
        # Dates should always be set due to default values, but double-check
        if not self.start_date or not self.end_date:
            return "Date range error. Please try resetting and setting a new date range."
        
        # Additional validation: ensure we have a reasonable date range
        date_range_days = (self.end_date - self.start_date).days
        if date_range_days < 20:  # Need minimum data for technical analysis
            return f"Date range is too short ({date_range_days} days). Please select at least 20 days for meaningful technical analysis."
        
        return None  # No errors
    
    def _disable_view(self):
        """Disable all buttons in the view."""
        for item in self.children:
            item.disabled = True
    
    def _create_analysis_starting_embed(self) -> discord.Embed:
        """Create embed showing analysis is starting."""
        date_range_days = (self.end_date - self.start_date).days
        
        embed = discord.Embed(
            title="⏳ Analysis Starting...",
            description="Processing your technical analysis request",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="Tickers",
            value=", ".join(self.tickers),
            inline=True
        )
        
        embed.add_field(
            name="Indicators",
            value="\n".join([f"• {ind}" for ind in self.selected_indicators]),
            inline=True
        )
        
        embed.add_field(
            name="Date Range",
            value=f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}\n({date_range_days} days)",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Status",
            value="Fetching market data and generating analysis...\nThis may take a few moments.",
            inline=False
        )
        
        embed.set_footer(text="Please wait while we process your request")
        
        return embed
    
    async def on_timeout(self):
        """Handle view timeout by disabling all components."""
        logger.info(f"Analysis setup view timed out for tickers: {self.tickers}")
        self._disable_view()
    
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        """Handle view errors gracefully."""
        self._analysis_started = False  # Reset flag on error
        logger.error(f"IndicatorSelectView error: {error}")
        try:
            await interaction.response.send_message(
                "An error occurred with the analysis setup. Please try again.", 
                ephemeral=True
            )
        except:
            pass


def create_indicator_selection_embed(
    tickers: List[str], 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    selected_indicators: Optional[List[str]] = None
) -> discord.Embed:
    """
    Create a comprehensive embed for the technical analysis setup interface.
    
    Args:
        tickers: List of ticker symbols to analyze
        start_date: Analysis start date (timezone-aware)
        end_date: Analysis end date (timezone-aware)
        selected_indicators: Currently selected technical indicators
    
    Returns:
        Discord embed with setup information and instructions
    """    # Calculate date range information
    if start_date and end_date:
        date_range_days = (end_date - start_date).days
        date_range_text = f"**📅 Period:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({date_range_days} days)"
    else:
        # This should rarely happen since we have default dates, but provide fallback
        date_range_text = "**📅 Period:** ⚠️ Error loading default range - please reset or change date range"
    
    # Create main embed
    embed = discord.Embed(
        title="📊 Technical Analysis Setup",
        description=f"**Tickers:** {', '.join(tickers)}\n{date_range_text}",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )
    
    # Add available indicators section
    available_indicators_text = "\n".join([
        f"• **{name}** - {desc}" 
        for name, desc in AVAILABLE_INDICATORS.items()
    ])
    embed.add_field(
        name="📋 Available Technical Indicators",
        value=available_indicators_text,
        inline=False
    )
    
    # Add selected indicators section
    if selected_indicators:
        selected_text = "\n".join([f"{indicator}" for indicator in selected_indicators])
        embed.add_field(
            name=f"Selected Indicators ({len(selected_indicators)})",
            value=selected_text,
            inline=True
        )
    else:
        embed.add_field(
            name="Selected Indicators",
            value="None selected",
            inline=True
        )
    
    # Add setup status
    indicators_ready = bool(selected_indicators)
    dates_ready = bool(start_date and end_date)
    
    status_text = f"📊 Indicators: {'✅' if indicators_ready else '❌'}\n📅 Date Range: {'✅' if dates_ready else '❌'}"
    if indicators_ready and dates_ready:
        status_text += "\n🚀 Ready to analyze!"
    else:
        status_text += "\n⏳ Setup incomplete"
    
    embed.add_field(
        name="📋 Setup Status",
        value=status_text,
        inline=True
    )
    
    # Add instructions
    embed.add_field(
        name="📝 Instructions",
        value=(
            "1️⃣ **Select Indicators** - Choose technical indicators\n"
            "2️⃣ **Set Date Range** - Choose analysis period\n"
            "3️⃣ **▶Start Analysis** - Begin technical analysis\n"
            "🔄 **Reset All** - Clear selections and start over\n"
        ),
        inline=False
    )
    
    # Add footer with timeout information
    embed.set_footer(
        text=f"⏰ Setup expires in {DEFAULT_TIMEOUT // 60} minutes • GridZer0 Technical Analysis Bot"
    )
    
    return embed
