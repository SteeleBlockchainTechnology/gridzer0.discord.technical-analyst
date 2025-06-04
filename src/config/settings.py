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
      # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    # Model Settings
    MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/llama-4-maverick-17b-128e-instruct")
    
    # Log Settings
    LOGS_DIR = os.getenv("LOGS_DIR", "logs")
    LOG_FILE = os.path.join(LOGS_DIR, os.getenv("LOG_FILE", "technical_analysis_app.log"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    
    # Application defaults
    DEFAULT_TICKERS = ["BTC", "ETH", "ADA"]
    DEFAULT_LOOKBACK_DAYS = 365
    
    # Common cryptocurrency symbols that need the -USD suffix
    CRYPTO_SYMBOLS = [
        "BTC", "ETH", "LTC", "XRP", "BCH", "ADA", 
        "DOT", "LINK", "BNB", "XLM", "DOGE", "UNI", "SOL"
    ]
    
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
    ]

# Create a settings instance for importing elsewhere
settings = Settings()
