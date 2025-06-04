import streamlit as st
import pandas as pd
from ..config.settings import settings

class AnalysisDisplayComponent:
    """Component for rendering the analysis display."""
    
    def __init__(self):
        """Initialize the analysis display component."""

        self.settings = settings
        
    def create_tabs(self, tickers):
        """Create tabs for each ticker and an overall summary."""

        tab_names = ["Overall Summary"] + list(tickers)
        tabs = st.tabs(tab_names)
        return tabs, tab_names
        
    def display_ticker_analysis(self, tab, ticker, data, fig, analysis_result, crypto_symbols=None):
        """Display analysis for a single ticker in its tab."""

        with tab:
            # Check if this is likely a cryptocurrency 
            if crypto_symbols is None:
                crypto_symbols = self.settings.CRYPTO_SYMBOLS
                
            if ticker in crypto_symbols:
                st.subheader(f"Analysis for {ticker} (using {ticker}-USD data)")
            else:
                st.subheader(f"Analysis for {ticker}")
            
            # Display key price information
            self.display_price_metrics(data)
            
            # Display the chart
            st.plotly_chart(fig)
            
            # Display analysis
            st.write("**Recommendation:**", analysis_result.get("action", "N/A"))
            st.write("**Detailed Justification:**")
            st.write(analysis_result.get("justification", "No justification provided."))
    
    def display_price_metrics(self, data):
        """Display key price metrics in a clean format."""

        current_price = data['Close'].iloc[-1]
        price_change = data['Close'].iloc[-1] - data['Close'].iloc[0]
        price_change_pct = (price_change / data['Close'].iloc[0]) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        with col2:
            st.metric("Price Change", f"${price_change:.2f}")
        with col3:
            st.metric("% Change", f"{price_change_pct:.2f}%")
    
    def display_overall_summary(self, tab, results):
        """Display overall summary of all ticker analyses."""
        
        with tab:
            st.subheader("Overall Structured Recommendations")
            if results:
                df_summary = pd.DataFrame(results)
                st.table(df_summary)
            else:
                st.info("No analysis results available.")
