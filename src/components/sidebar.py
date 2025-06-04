import streamlit as st
from datetime import datetime, timedelta
from ..config.settings import settings

class SidebarComponent:
    """Component for rendering the application sidebar."""
    
    def __init__(self):
        """Initialize the sidebar component."""

        self.settings = settings
        
    def render_sidebar(self):
        """Render the sidebar configuration elements."""

        st.sidebar.header("Configuration")
        
        # Input for multiple stock tickers (comma-separated)
        default_tickers = ", ".join(self.settings.DEFAULT_TICKERS)
        tickers_input = st.sidebar.text_input("Enter Tickers (comma-separated):", default_tickers)
        # Parse tickers by stripping extra whitespace and splitting on commas
        tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]
        
        # Set the date range: start date = one year before today, end date = today
        end_date_default = datetime.today()
        start_date_default = end_date_default - timedelta(days=self.settings.DEFAULT_LOOKBACK_DAYS)
        start_date = st.sidebar.date_input("Start Date", value=start_date_default)
        end_date = st.sidebar.date_input("End Date", value=end_date_default)
        
        # Technical indicators selection
        st.sidebar.subheader("Technical Indicators")
        indicators = st.sidebar.multiselect(
            "Select Indicators:",
            self.settings.TECHNICAL_INDICATORS,
            default=["20-Day SMA"]
        )
        
        # Button to fetch data
        fetch_clicked = st.sidebar.button("Fetch Data")
        
        # Return the configuration
        return {
            "tickers": tickers,
            "start_date": start_date,
            "end_date": end_date,
            "indicators": indicators,
            "fetch_clicked": fetch_clicked
        }
