"""
Configuration settings for the Technical Analysis application.
This module loads and provides access to environment variables and other settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    # Discord Bot Settings
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
    DISCORD_STATUS = os.getenv("DISCORD_STATUS", "for /analyze commands")
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

    # Model Settings
    MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/llama-4-maverick-17b-128e-instruct")
    
    # Log Settings
    LOGS_DIR = os.getenv("LOGS_DIR", "logs")
    LOG_FILE = os.path.join(LOGS_DIR, os.getenv("LOG_FILE", "technical_analysis_app.log"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
      # Application defaults
    DEFAULT_TICKERS = ["AAPL", "GOOGL", "BTC", "ETH", "ADA"]
    DEFAULT_LOOKBACK_DAYS = 365
    
    # Data source preferences
    PREFERRED_CRYPTO_SOURCE = "coingecko"
    PREFERRED_STOCK_SOURCE = "yfinance"
    
    # Technical indicator options
    TECHNICAL_INDICATORS = [
        "20-Day SMA", 
        "20-Day EMA", 
        "20-Day Bollinger Bands", 
        "VWAP"
    ]
      # Recommendation options
    RECOMMENDATION_OPTIONS = [
        "Strong Buy", 
        "Buy", 
        "Weak Buy", 
        "Hold", 
        "Weak Sell", 
        "Sell", 
        "Strong Sell"
    ]    # Usage limits for cost control - Uniform limits for all users
    DEFAULT_MONTHLY_LIMIT = float(os.getenv("DEFAULT_MONTHLY_LIMIT", "10.0"))  # $10 per month for all users
    DEFAULT_DAILY_LIMIT = float(os.getenv("DEFAULT_DAILY_LIMIT", "2.0"))       # $2 per day
    DEFAULT_HOURLY_REQUESTS = int(os.getenv("DEFAULT_HOURLY_REQUESTS", "20"))  # 20 requests per hour
    
    # Admin settings
    ADMIN_USER_IDS = [id.strip() for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]
    USAGE_ALERT_THRESHOLD = float(os.getenv("USAGE_ALERT_THRESHOLD", "0.8"))  # Alert when 80% of limit is reached
    
    # Cost estimation (adjust based on actual Groq pricing)
    GROQ_COST_PER_1K_TOKENS = float(os.getenv("GROQ_COST_PER_1K_TOKENS", "0.0002"))

# Create a settings instance for importing elsewhere
settings = Settings()
