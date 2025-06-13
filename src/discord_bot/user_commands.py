"""
User commands for checking their own usage.
"""
import discord
from discord.ext import commands
from discord import app_commands
from ..database.usage_tracker import UsageTracker
from ..config.settings import settings
from ..utils.logging_utils import setup_logger

logger = setup_logger("UserCommands")

class UserCommands(commands.Cog):
    """User commands for checking usage and limits."""
    
    def __init__(self, bot):
        self.bot = bot
        self.usage_tracker = UsageTracker()
    
    @app_commands.command(name="my_usage", description="Check your AI analysis usage")
    async def my_usage(self, interaction: discord.Interaction):
        """Check user's own usage statistics."""
        try:
            user_id = str(interaction.user.id)
            usage_stats = self.usage_tracker.get_user_usage(user_id, days=30)
            limits_check = self.usage_tracker.check_user_limits(user_id)
            
            embed = discord.Embed(
                title="📊 Your Usage Statistics",
                color=discord.Color.blue()
            )
            
            # Current usage vs limits
            monthly_pct = (limits_check['monthly_usage'] / limits_check['monthly_limit']) * 100 if limits_check['monthly_limit'] > 0 else 0
            daily_pct = (limits_check['daily_usage'] / limits_check['daily_limit']) * 100 if limits_check['daily_limit'] > 0 else 0
            
            # Status indicator
            if monthly_pct >= 100:
                status_emoji = "🔴"
                status_text = "Over Limit"
            elif monthly_pct >= 80:
                status_emoji = "🟡"
                status_text = "Approaching Limit"
            else:
                status_emoji = "🟢"
                status_text = "Within Limits"
            
            embed.add_field(
                name="Current Usage",
                value=(f"**This Month:** ${limits_check['monthly_usage']:.2f} / ${limits_check['monthly_limit']:.2f} ({monthly_pct:.1f}%)\n"
                      f"**Today:** ${limits_check['daily_usage']:.2f} / ${limits_check['daily_limit']:.2f} ({daily_pct:.1f}%)\n"
                      f"**This Hour:** {limits_check['hourly_requests']} / {limits_check['hourly_limit']} requests"),
                inline=False
            )            # Account info - uniform limits for all users
            status_color = "🟢" if limits_check['within_limits'] else "🔴"
            status_text = "Within Limits" if limits_check['within_limits'] else "Over Limit"
            
            embed.add_field(
                name="Account Info",
                value=(f"**Status:** {status_color} {status_text}\n"
                      f"**Monthly Limit:** ${limits_check['monthly_limit']:.2f}"),
                inline=False
            )
            
            # Detailed usage by service
            if usage_stats:
                total_cost = sum(service['cost'] for service in usage_stats.values())
                total_requests = sum(service['requests'] for service in usage_stats.values())
                
                embed.add_field(
                    name="30-Day Summary",
                    value=(f"**Total Cost:** ${total_cost:.2f}\n"
                          f"**Total Requests:** {total_requests}"),
                    inline=False
                )
                
                # Show service breakdown if there's usage
                service_count = 0
                for service, stats in usage_stats.items():
                    if service_count >= 2:  # Limit to 2 services to avoid embed limits
                        break
                    embed.add_field(
                        name=f"{service.upper()}",
                        value=(f"${stats['cost']:.2f}\n"
                              f"{stats['requests']} requests"),
                        inline=True
                    )
                    service_count += 1
            else:
                embed.add_field(
                    name="30-Day Summary",
                    value="No usage recorded yet. Try running some analyses!",
                    inline=False
                )            # Usage tips and warnings
            if monthly_pct >= 90:
                embed.add_field(
                    name="⚠️ Warning",
                    value="You're very close to your monthly limit! Your usage will be restricted when you reach $10.",
                    inline=False
                )
            elif monthly_pct >= 80:
                embed.add_field(
                    name="💡 Tip",
                    value="You're approaching your monthly limit. Consider optimizing your analysis requests.",
                    inline=False
                )
            elif total_cost == 0:
                embed.add_field(
                    name="🎉 Welcome!",
                    value="You have $10 in AI analysis credits this month. Start analyzing some stocks or crypto!",
                    inline=False
                )
            
            # Set embed color based on usage
            if monthly_pct >= 100:
                embed.color = discord.Color.red()
            elif monthly_pct >= 80:
                embed.color = discord.Color.orange()
            else:
                embed.color = discord.Color.green()
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error getting user usage: {e}")
            await interaction.response.send_message("❌ Error retrieving your usage data.", ephemeral=True)

    @app_commands.command(name="usage_help", description="Get help about usage limits and pricing")
    async def usage_help(self, interaction: discord.Interaction):
        """Provide information about usage limits and how they work."""
        try:
            embed = discord.Embed(
                title="💡 Usage Limits & Pricing Info",
                description="Learn about how our AI analysis usage system works",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📊 Usage Limits (All Users)",
                value=(f"• **Monthly:** ${settings.DEFAULT_MONTHLY_LIMIT:.2f}\n"
                      f"• **Daily:** ${settings.DEFAULT_DAILY_LIMIT:.2f}\n"
                      f"• **Hourly:** {settings.DEFAULT_HOURLY_REQUESTS} requests"),
                inline=False
            )
            
            embed.add_field(
                name="🔄 Reset Schedule",
                value="• **Monthly:** 1st of each month\n• **Daily:** Midnight UTC\n• **Hourly:** Every hour",
                inline=False
            )
            
            embed.add_field(
                name="💰 What Counts as Usage",
                value=(
                    "• Each AI analysis request\n"
                    "• Cost based on AI model usage\n"
                    "• Chart generation is free\n"
                    "• Basic market data is free"
                ),
                inline=False
            )
            
            embed.add_field(
                name="📈 Tips to Optimize Usage",
                value=(
                    "• Analyze multiple tickers in one request\n"
                    "• Use longer time periods for more insights\n"
                    "• Review your usage with `/my_usage`\n"
                    "• Consider premium for heavy usage"
                ),
                inline=False
            )
            
            embed.set_footer(text="Contact an admin for premium upgrade or questions")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing usage help: {e}")
            await interaction.response.send_message("❌ Error retrieving help information.", ephemeral=True)

async def setup(bot):
    """Setup function for the user commands cog."""
    await bot.add_cog(UserCommands(bot))
