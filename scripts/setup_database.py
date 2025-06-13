"""
Database migration and setup script for usage tracking.
Run this script to initialize the usage tracking database.
"""
import sys
import os
from pathlib import Path

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.usage_tracker import UsageTracker
from src.config.settings import settings
from src.utils.logging_utils import setup_logger

logger = setup_logger("DatabaseMigration")

def setup_database():
    """Initialize the usage tracking database."""
    try:
        logger.info("Setting up usage tracking database...")
        
        # Initialize the usage tracker (this will create the database)
        usage_tracker = UsageTracker()
        
        logger.info("Database setup completed successfully!")
        
        # Create some example premium users if admin IDs are configured
        if settings.ADMIN_USER_IDS:
            logger.info("Setting up admin users with premium limits...")
            for admin_id in settings.ADMIN_USER_IDS:
                if admin_id.strip():  # Skip empty IDs
                    usage_tracker.update_user_limits(
                        admin_id.strip(),
                        monthly_limit=settings.PREMIUM_MONTHLY_LIMIT,
                        daily_limit=settings.PREMIUM_DAILY_LIMIT,
                        requests_per_hour=settings.PREMIUM_HOURLY_REQUESTS,
                        is_premium=True
                    )
                    logger.info(f"Set premium limits for admin user: {admin_id}")
        
        # Show current settings
        logger.info("Current usage limit settings:")
        logger.info(f"  Standard Monthly: ${settings.DEFAULT_MONTHLY_LIMIT}")
        logger.info(f"  Standard Daily: ${settings.DEFAULT_DAILY_LIMIT}")
        logger.info(f"  Standard Hourly Requests: {settings.DEFAULT_HOURLY_REQUESTS}")
        logger.info(f"  Premium Monthly: ${settings.PREMIUM_MONTHLY_LIMIT}")
        logger.info(f"  Premium Daily: ${settings.PREMIUM_DAILY_LIMIT}")
        logger.info(f"  Premium Hourly Requests: {settings.PREMIUM_HOURLY_REQUESTS}")
        logger.info(f"  Admin Users: {len(settings.ADMIN_USER_IDS)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False

def check_database_status():
    """Check the current status of the database."""
    try:
        usage_tracker = UsageTracker()
        cache_info = usage_tracker.get_cache_info() if hasattr(usage_tracker, 'get_cache_info') else {}
        
        logger.info("Database status check:")
        logger.info(f"  Database file: {usage_tracker.db_path}")
        logger.info(f"  Database exists: {os.path.exists(usage_tracker.db_path)}")
        
        # Get some basic stats
        stats = usage_tracker.get_usage_stats(days=30)
        logger.info(f"  Total users (30 days): {stats.get('unique_users', 0)}")
        logger.info(f"  Total requests (30 days): {stats.get('total_requests', 0)}")
        logger.info(f"  Total cost (30 days): ${stats.get('total_cost', 0):.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration and setup for usage tracking")
    parser.add_argument("--setup", action="store_true", help="Initialize the database")
    parser.add_argument("--status", action="store_true", help="Check database status")
    parser.add_argument("--reset", action="store_true", help="Reset the database (WARNING: Deletes all data)")
    
    args = parser.parse_args()
    
    if args.setup:
        success = setup_database()
        sys.exit(0 if success else 1)
    
    elif args.status:
        success = check_database_status()
        sys.exit(0 if success else 1)
    
    elif args.reset:
        confirm = input("Are you sure you want to reset the database? This will delete all usage data. Type 'YES' to confirm: ")
        if confirm == "YES":
            try:
                usage_tracker = UsageTracker()
                if os.path.exists(usage_tracker.db_path):
                    os.remove(usage_tracker.db_path)
                    logger.info("Database file deleted")
                
                # Recreate
                setup_database()
                logger.info("Database reset completed")
            except Exception as e:
                logger.error(f"Error resetting database: {e}")
                sys.exit(1)
        else:
            logger.info("Database reset cancelled")
    
    else:
        parser.print_help()
