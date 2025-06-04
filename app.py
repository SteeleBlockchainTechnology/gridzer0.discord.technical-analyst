import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Import application modules
from src.components import SidebarComponent, AnalysisDisplayComponent
from src.services import MarketDataService, TechnicalAnalysisService, AIAnalysisService
from src.utils import setup_logger
from src.config.settings import settings

# Set up logger for the main application
logger = setup_logger("MainApplication")
logger.info("Application starting")

# Initialize Services
market_data_service = MarketDataService()
technical_analysis_service = TechnicalAnalysisService()
ai_analysis_service = AIAnalysisService()

# Initialize UI Components
sidebar_component = SidebarComponent()
analysis_display_component = AnalysisDisplayComponent()

# Configure Streamlit page
st.set_page_config(layout="wide", page_title="Technical Analysis Agent")
st.title("Technical Analysis Agent")

def main():
    """Main application function."""
    
    # Render sidebar and get configuration
    config = sidebar_component.render_sidebar()
    tickers = config["tickers"]
    start_date = config["start_date"]
    end_date = config["end_date"]
    indicators = config["indicators"]
    fetch_clicked = config["fetch_clicked"]
    
    # Fetch data when button is clicked
    if fetch_clicked:
        logger.info(f"Fetching data for tickers: {tickers}")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # Show loading message
        with st.spinner("Fetching market data..."):
            stock_data = market_data_service.get_multiple_tickers_data(tickers, start_date, end_date)
            
            if stock_data:
                st.session_state["stock_data"] = stock_data
                logger.info(f"Stock data loaded successfully for: {', '.join(stock_data.keys())}")
                st.success("Stock data loaded successfully for: " + ", ".join(stock_data.keys()))
            else:
                st.error("No data was fetched. Please check your input and try again.")
    
    # Process and display analysis if we have data
    if "stock_data" in st.session_state and st.session_state["stock_data"]:
        process_and_display_analysis(
            st.session_state["stock_data"], 
            indicators
        )
    else:
        st.info("Please fetch stock data using the sidebar.")

def process_and_display_analysis(stock_data, indicators):
    """Process and display analysis for all tickers."""

    # Create tabs
    tabs, tab_names = analysis_display_component.create_tabs(stock_data.keys())
    
    # List to store overall results
    overall_results = []
    
    # Process each ticker
    for i, ticker in enumerate(stock_data):
        data = stock_data[ticker]
        
        # Analyze the ticker
        with st.spinner(f"Analyzing {ticker}..."):
            # Create chart
            fig = technical_analysis_service.create_candlestick_chart(data, ticker, indicators)
            
            # Generate technical data summary
            data_description = technical_analysis_service.generate_technical_data_summary(
                data, ticker, indicators
            )
            
            # Get AI analysis
            analysis_result = ai_analysis_service.analyze_market_data(ticker, data_description)
            
            # Add to overall results
            overall_results.append({
                "Stock": ticker, 
                "Recommendation": analysis_result.get("action", "N/A")
            })
            
            # Display in tab
            analysis_display_component.display_ticker_analysis(
                tabs[i + 1], ticker, data, fig, analysis_result, settings.CRYPTO_SYMBOLS
            )
    
    # Display overall summary
    analysis_display_component.display_overall_summary(tabs[0], overall_results)

if __name__ == "__main__":
    main()
