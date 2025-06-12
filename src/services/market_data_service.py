"""
Market data service using yfinance API.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from ..utils.logging_utils import setup_logger
from ..config.settings import settings

# Set up logger for this module
logger = setup_logger("MarketDataService")

class MarketDataService:
    """Service for fetching market data from Yahoo Finance."""
    
    def __init__(self):
        """Initialize the market data service."""
    
    def get_ticker_data(self, ticker, start_date, end_date):
        """Fetch ticker data from Yahoo Finance."""

        try:
            # Check if this is a cryptocurrency ticker and append -USD if needed
            yf_ticker = ticker
            
            logger.info(f"Downloading data for {ticker} using yfinance symbol {yf_ticker}")
            # Download data using yfinance
            data = yf.download(yf_ticker, start=start_date, end=end_date, multi_level_index=False)
            
            if not data.empty:
                logger.info(f"Retrieved {len(data)} records for {ticker}")
                return data
            else:
                logger.warning(f"No data found for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None
    
    def fetch_data(self, ticker, start_date, end_date):
        """Alias for get_ticker_data to maintain consistency with Discord bot."""
        return self.get_ticker_data(ticker, start_date, end_date)
    
    def get_multiple_tickers_data(self, tickers, start_date, end_date):
        """
        Fetch data for multiple tickers.
        
        """
        logger.info(f"Fetching data for tickers: {tickers}")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        stock_data = {}
        
        for ticker in tickers:
            data = self.get_ticker_data(ticker, start_date, end_date)
            if data is not None:
                stock_data[ticker] = data
        
        return stock_data
