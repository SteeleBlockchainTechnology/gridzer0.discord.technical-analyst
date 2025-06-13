"""
Admin commands for usage management.
"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from ..database.usage_tracker import UsageTracker
from ..config.settings import settings
from ..utils.logging_utils import setup_logger

logger = setup_logger("AdminCommands")

class AdminCommands(commands.Cog):
    """Admin commands for managing user usage and limits."""
    
    def __init__(self, bot):
        self.bot = bot
        self.usage_tracker = UsageTracker()
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        return str(user_id) in settings.ADMIN_USER_IDS
    
    @app_commands.command(name="usage_stats", description="Get usage statistics (Admin only)")
    @app_commands.describe(days="Number of days to analyze (default: 30)")
    async def usage_stats(self, interaction: discord.Interaction, days: int = 30):
        """Get overall usage statistics."""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Admin access required.", ephemeral=True)
            return
        
        try:
            stats = self.usage_tracker.get_usage_stats(days)
            top_users = self.usage_tracker.get_top_users_by_usage(days, 5)
            
            embed = discord.Embed(
                title=f"📊 Usage Statistics ({days} days)",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Overall Stats",
                value=(f"**Unique Users:** {stats.get('unique_users', 0)}\n"
                      f"**Total Requests:** {stats.get('total_requests', 0)}\n"
                      f"**Total Cost:** ${stats.get('total_cost', 0):.2f}\n"
                      f"**Avg Cost/Request:** ${stats.get('avg_cost_per_request', 0):.4f}"),
                inline=False
            )
            
            if top_users:
                top_users_text = "\n".join([
                    f"<@{user_id}>: ${cost:.2f}" for user_id, cost in top_users
                ])
                embed.add_field(
                    name="Top Users by Cost",
                    value=top_users_text,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            await interaction.response.send_message("❌ Error retrieving stats.", ephemeral=True)
    
    @app_commands.command(name="user_usage", description="Get usage for a specific user (Admin only)")
    @app_commands.describe(
        user="The user to check usage for",
        days="Number of days to analyze (default: 30)"
    )
    async def user_usage(self, interaction: discord.Interaction, user: discord.Member, days: int = 30):
        """Get usage statistics for a specific user."""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Admin access required.", ephemeral=True)
            return
        
        try:
            user_id = str(user.id)
            usage_stats = self.usage_tracker.get_user_usage(user_id, days)
            limits_check = self.usage_tracker.check_user_limits(user_id)
            
            embed = discord.Embed(
                title=f"📊 Usage for {user.display_name} ({days} days)",
                color=discord.Color.blue()
            )
            
            total_cost = sum(service['cost'] for service in usage_stats.values())
            total_requests = sum(service['requests'] for service in usage_stats.values())
            embed.add_field(
                name="Summary",                value=(f"**Total Cost:** ${total_cost:.2f}\n"
                      f"**Total Requests:** {total_requests}\n"
                      f"**Monthly Limit:** ${limits_check['monthly_limit']:.2f}\n"
                      f"**Daily Limit:** ${limits_check['daily_limit']:.2f}"),
                inline=False
            )
            
            if usage_stats:
                for service, stats in usage_stats.items():
                    embed.add_field(
                        name=f"{service.upper()} Usage",
                        value=(f"**Cost:** ${stats['cost']:.2f}\n"
                              f"**Requests:** {stats['requests']}\n"
                              f"**Tokens:** {stats['tokens']:,}"),
                        inline=True
                    )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error getting user usage: {e}")
            await interaction.response.send_message("❌ Error retrieving user usage.", ephemeral=True)
    @app_commands.command(name="set_user_limits", description="Set usage limits for a user (Admin only)")
    @app_commands.describe(
        user="The user to update",
        monthly_limit="Monthly cost limit in USD (default: $10)",
        daily_limit="Daily cost limit in USD (default: $2)", 
        requests_per_hour="Requests per hour limit (default: 20)"
    )
    async def set_user_limits(self, interaction: discord.Interaction, 
                             user: discord.Member,
                             monthly_limit: Optional[float] = None, 
                             daily_limit: Optional[float] = None,
                             requests_per_hour: Optional[int] = None):
        """Set usage limits for a specific user."""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Admin access required.", ephemeral=True)
            return
        
        try:
            user_id = str(user.id)
            success = self.usage_tracker.update_user_limits(
                user_id, monthly_limit, daily_limit, requests_per_hour
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ User Limits Updated",
                    description=f"Successfully updated limits for {user.display_name}",
                    color=discord.Color.green()
                )
                
                # Show current limits
                limits = self.usage_tracker.get_user_limits(user_id)
                embed.add_field(
                    name="Current Limits",
                    value=(f"**Monthly:** ${limits['monthly_limit']:.2f}\n"
                          f"**Daily:** ${limits['daily_limit']:.2f}\n"
                          f"**Hourly Requests:** {limits['requests_per_hour']}"),
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Failed to update user limits",
                    color=discord.Color.red()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting user limits: {e}")
            await interaction.response.send_message("❌ Error updating limits.", ephemeral=True)
    
    @app_commands.command(name="set_premium", description="Set premium status for a user (Admin only)")
    @app_commands.describe(
        user="The user to update",
        premium="Whether to grant premium status"
    )
    async def set_premium(self, interaction: discord.Interaction, user: discord.Member, premium: bool):
        """Set premium status for a user with appropriate limits."""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Admin access required.", ephemeral=True)
            return
        
        try:
            user_id = str(user.id)
            
            if premium:
                # Set premium limits
                success = self.usage_tracker.update_user_limits(
                    user_id,
                    monthly_limit=settings.PREMIUM_MONTHLY_LIMIT,
                    daily_limit=settings.PREMIUM_DAILY_LIMIT,
                    requests_per_hour=settings.PREMIUM_HOURLY_REQUESTS,
                    is_premium=True
                )
            else:
                # Set standard limits
                success = self.usage_tracker.update_user_limits(
                    user_id,
                    monthly_limit=settings.DEFAULT_MONTHLY_LIMIT,
                    daily_limit=settings.DEFAULT_DAILY_LIMIT,
                    requests_per_hour=settings.DEFAULT_HOURLY_REQUESTS,
                    is_premium=False
                )
            
            if success:
                status = "Premium" if premium else "Standard"
                embed = discord.Embed(
                    title="✅ Premium Status Updated",
                    description=f"Successfully set {user.display_name} to {status}",
                    color=discord.Color.green()
                )
                
                # Show new limits
                limits = self.usage_tracker.get_user_limits(user_id)
                embed.add_field(
                    name="New Limits",
                    value=(f"**Monthly:** ${limits['monthly_limit']:.2f}\n"
                          f"**Daily:** ${limits['daily_limit']:.2f}\n"
                          f"**Hourly Requests:** {limits['requests_per_hour']}\n"
                          f"**Premium:** {'Yes' if limits['is_premium'] else 'No'}"),
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Failed to update premium status",
                    color=discord.Color.red()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting premium status: {e}")
            await interaction.response.send_message("❌ Error updating premium status.", ephemeral=True)

async def setup(bot):
    """Setup function for the admin commands cog."""
    await bot.add_cog(AdminCommands(bot))
