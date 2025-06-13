#!/usr/bin/env python3
"""
Technical Analysis Agent - Main Entry Point

This is the main entry point for the Technical Analysis Agent application.
It provides multiple modes of operation:
- Discord Bot: Run the Discord bot for technical analysis
- CLI: Command-line interface for technical analysis
- Web: Web interface (if implemented)
- Test: Run tests for the application

Usage:
    python main.py discord              # Run Discord bot
    python main.py cli                  # Run CLI interface
    python main.py test                 # Run tests
    python main.py --help               # Show help
"""

import datetime
import sys
import argparse
import logging
import asyncio
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import core modules
from src.config.settings import settings
from src.utils.logging_utils import setup_logger

# Set up main logger
logger = setup_logger("TechnicalAnalysisAgent")

class TechnicalAnalysisAgent:
    """Main application class for the Technical Analysis Agent."""
    
    def __init__(self):
        """Initialize the application."""
        self.logger = logger
        self.logger.info("Initializing Technical Analysis Agent")
        
    def run_discord_bot(self):
        """Run the Discord bot."""
        try:
            self.logger.info("Starting Discord bot mode...")
              # Import Discord bot module
            from src.discord_bot.bot import create_bot
            
            # Validate Discord token
            if not settings.DISCORD_TOKEN:
                self.logger.error("DISCORD_TOKEN not found in environment variables")
                self.logger.error("Please set DISCORD_TOKEN in your .env file")
                return False
              # Create and configure bot
            bot = create_bot()
            
            # Run the bot
            self.logger.info("Discord bot starting...")
            bot.run(settings.DISCORD_TOKEN)
            
        except ImportError as e:
            self.logger.error(f"Failed to import Discord modules: {e}")
            self.logger.error("Make sure discord.py is installed: pip install discord.py")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start Discord bot: {e}")
            return False
        
        return True
    def run_cli(self):
        """Run the CLI interface."""
        try:
            self.logger.info("Starting CLI mode...")
            
            from src.services.market_data_service import MarketDataService
            from src.services.crypto_market_data_service import CryptoMarketDataService
            from src.services.technical_analysis_service import TechnicalAnalysisService
            from src.services.ai_analysis_service import AIAnalysisService
            from datetime import datetime, timedelta
            
            # Initialize services
            market_service = MarketDataService()
            crypto_service = CryptoMarketDataService()
            tech_service = TechnicalAnalysisService()
            ai_service = AIAnalysisService()
            
            print("=" * 60)
            print("Technical Analysis Agent - CLI Mode")
            print("=" * 60)
            while True:
                print("\nAvailable commands:")
                print("1. Analyze stock ticker")
                print("2. Analyze cryptocurrency")
                print("3. List available indicators")
                print("4. Exit")
                choice = input("\nEnter your choice (1-4): ").strip()
                
                if choice == "1":
                    self._cli_analyze_ticker(market_service, tech_service, ai_service, "stock")
                elif choice == "2":
                    self._cli_analyze_ticker(crypto_service, tech_service, ai_service, "crypto")
                elif choice == "3":
                    self._cli_list_indicators()
                elif choice == "4":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid choice. Please enter 1, 2, 3, or 4.")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
        except Exception as e:
            self.logger.error(f"CLI error: {e}")
            return False
        return True
    
    def _cli_analyze_ticker(self, data_service, tech_service, ai_service, asset_type):
        """Handle ticker analysis in CLI mode."""
        try:
            # Get user inputs
            asset_name = "stock" if asset_type == "stock" else "cryptocurrency"
            example = "AAPL" if asset_type == "stock" else "BTC"
            ticker = input(f"Enter {asset_name} symbol (e.g., {example}): ").strip().upper()
            if not ticker:
                print(f"{asset_name.capitalize()} symbol is required.")
                return
            
            print(f"Analyzing {ticker} as {asset_name}...")
            
            # Get date range
            days_back = input("Enter number of days back (default: 365): ").strip()
            try:
                days_back = int(days_back) if days_back else 365
            except ValueError:
                days_back = 365
            
            end_date = datetime.now()
            start_date = end_date - datetime.timedelta(days=days_back)
            
            # Get indicators
            print(f"\nAvailable indicators: {', '.join(settings.TECHNICAL_INDICATORS)}")
            indicators_input = input("Enter indicators (comma-separated, default: 20-Day SMA): ").strip()
            indicators = [ind.strip() for ind in indicators_input.split(",")] if indicators_input else ["20-Day SMA"]
            print(f"\nAnalyzing {ticker} ({asset_name}) from {start_date.date()} to {end_date.date()}...")
            print(f"Indicators: {', '.join(indicators)}")
            
            # Fetch data
            data = data_service.fetch_data(ticker, start_date.date(), end_date.date())
            
            if data.empty:
                print(f"No data available for {ticker}")
                return
              # Generate analysis
            summary = tech_service.generate_technical_data_summary(data, ticker, indicators, asset_type)
            print(f"\nTechnical Analysis for {ticker}:")
            print("-" * 40)
            print(summary)
            
            # AI Analysis
            try:
                ai_analysis = ai_service.analyze_stock_data(data, ticker, indicators)
                print(f"\nAI Analysis:")
                print("-" * 40)
                print(ai_analysis)
            except Exception as e:
                print(f"\nAI Analysis unavailable: {e}")
            
            # Ask if user wants to save chart
            save_chart = input("\nSave chart to file? (y/n): ").strip().lower()
            if save_chart == 'y':
                try:
                    fig = tech_service.create_candlestick_chart(data, ticker, indicators)
                    filename = f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    fig.write_html(filename)
                    print(f"Chart saved as {filename}")
                except Exception as e:
                    print(f"Failed to save chart: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in CLI analysis: {e}")
            print(f"Error: {e}")
    
    def _cli_list_indicators(self):
        """List available technical indicators."""
        print("\nAvailable Technical Indicators:")
        print("-" * 40)
        for i, indicator in enumerate(settings.TECHNICAL_INDICATORS, 1):
            print(f"{i:2d}. {indicator}")
    
    def run_tests(self):
        """Run application tests."""
        try:
            self.logger.info("Running tests...")
            
            # Import test modules
            import pytest
            
            # Run tests
            test_args = [
                "-v",  # Verbose output
                "--tb=short",  # Short traceback format
                "tests/" if Path("tests").exists() else "src/",
            ]
            
            return pytest.main(test_args) == 0
            
        except ImportError:
            self.logger.error("pytest not installed. Install it with: pip install pytest")
            return False
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            return False
    
    def validate_environment(self):
        """Validate the environment and dependencies."""
        self.logger.info("Validating environment...")
        
        issues = []
          # Check for required environment variables
        required_env_vars = ['DISCORD_TOKEN', 'GROQ_API_KEY']
        for var in required_env_vars:
            if not getattr(settings, var, None):
                issues.append(f"Missing environment variable: {var}")
        
        # Check for optional environment variables
        optional_env_vars = ['COINGECKO_API_KEY']
        for var in optional_env_vars:
            if not getattr(settings, var, None):
                self.logger.info(f"Optional environment variable not set: {var}")
        
        # Check for required directories
        required_dirs = ['src', 'logs']
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                issues.append(f"Missing directory: {dir_name}")
        
        # Check for required files
        required_files = ['.env.example', 'pyproject.toml']
        for file_name in required_files:
            if not Path(file_name).exists():
                issues.append(f"Missing file: {file_name}")
        
        if issues:
            self.logger.warning("Environment validation issues found:")
            for issue in issues:
                self.logger.warning(f"  - {issue}")
            return False
        
        self.logger.info("Environment validation passed")
        return True

def create_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Technical Analysis Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py discord          # Run Discord bot
  python main.py cli              # Run CLI interface
  python main.py test             # Run tests
  python main.py discord --validate  # Validate environment before running Discord bot
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["discord", "cli", "test"],
        help="Mode of operation"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate environment before running"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Technical Analysis Agent v1.0.0"
    )
    
    return parser

def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create application instance
    app = TechnicalAnalysisAgent()
    
    # Validate environment if requested
    if args.validate:
        if not app.validate_environment():
            logger.error("Environment validation failed")
            sys.exit(1)
    
    # Run the specified mode
    success = False
    
    if args.mode == "discord":
        success = app.run_discord_bot()
    elif args.mode == "cli":
        success = app.run_cli()
    elif args.mode == "test":
        success = app.run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
