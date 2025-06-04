## AI-Powered Technical Analysis Dashboard (Gemini 2.0)
## Source: https://www.youtube.com/@DeepCharts

# Libraries
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import groq
import tempfile
import os
import json
import base64
from datetime import datetime, timedelta

# Configure the API key - IMPORTANT: Use Streamlit secrets or environment variables for security
# For now, using hardcoded API key - REPLACE WITH YOUR ACTUAL API KEY SECURELY
GROQ_API_KEY = "your api key goes here"
client = groq.Groq(api_key=GROQ_API_KEY)

# Select the LLama model
MODEL_NAME = 'meta-llama/llama-4-maverick-17b-128e-instruct'

# Set up Streamlit app
st.set_page_config(layout="wide")
st.title("AI-Powered Technical Stock Analysis Dashboard")
st.sidebar.header("Configuration")

# Input for multiple stock tickers (comma-separated)
tickers_input = st.sidebar.text_input("Enter Stock Tickers (comma-separated):", "AAPL,MSFT,GOOG")
# Parse tickers by stripping extra whitespace and splitting on commas
tickers = [ticker.strip().upper() for ticker in tickers_input.split(",") if ticker.strip()]

# Set the date range: start date = one year before today, end date = today
end_date_default = datetime.today()
start_date_default = end_date_default - timedelta(days=365)
start_date = st.sidebar.date_input("Start Date", value=start_date_default)
end_date = st.sidebar.date_input("End Date", value=end_date_default)

# Technical indicators selection (applied to every ticker)
st.sidebar.subheader("Technical Indicators")
indicators = st.sidebar.multiselect(
    "Select Indicators:",
    ["20-Day SMA", "20-Day EMA", "20-Day Bollinger Bands", "VWAP"],
    default=["20-Day SMA"]
)

# Button to fetch data for all tickers
if st.sidebar.button("Fetch Data"):
    stock_data = {}
    for ticker in tickers:
        # Download data for each ticker using yfinance
        data = yf.download(ticker, start=start_date, end=end_date, multi_level_index=False)
        if not data.empty:
            stock_data[ticker] = data
        else:
            st.warning(f"No data found for {ticker}.")
    st.session_state["stock_data"] = stock_data
    st.success("Stock data loaded successfully for: " + ", ".join(stock_data.keys()))

# Ensure we have data to analyze
if "stock_data" in st.session_state and st.session_state["stock_data"]:

    # Define a function to build chart, call the Gemini API and return structured result
    def analyze_ticker(ticker, data):
        # Build candlestick chart for the given ticker's data
        fig = go.Figure(data=[
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name="Candlestick"
            )
        ])

        # Add selected technical indicators
        def add_indicator(indicator):
            if indicator == "20-Day SMA":
                sma = data['Close'].rolling(window=20).mean()
                fig.add_trace(go.Scatter(x=data.index, y=sma, mode='lines', name='SMA (20)'))
            elif indicator == "20-Day EMA":
                ema = data['Close'].ewm(span=20).mean()
                fig.add_trace(go.Scatter(x=data.index, y=ema, mode='lines', name='EMA (20)'))
            elif indicator == "20-Day Bollinger Bands":
                sma = data['Close'].rolling(window=20).mean()
                std = data['Close'].rolling(window=20).std()
                bb_upper = sma + 2 * std
                bb_lower = sma - 2 * std
                fig.add_trace(go.Scatter(x=data.index, y=bb_upper, mode='lines', name='BB Upper'))
                fig.add_trace(go.Scatter(x=data.index, y=bb_lower, mode='lines', name='BB Lower'))
            elif indicator == "VWAP":
                data['VWAP'] = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
                fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], mode='lines', name='VWAP'))
                
        for ind in indicators:
            add_indicator(ind)
        fig.update_layout(xaxis_rangeslider_visible=False)

        # Save chart as temporary PNG file and read image bytes
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            fig.write_image(tmpfile.name)
            tmpfile_path = tmpfile.name
        with open(tmpfile_path, "rb") as f:
            image_bytes = f.read()
        os.remove(tmpfile_path)

        # Encode the image as base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create a text description of the chart data for the LLM
        data_description = f"""
        Stock: {ticker}
        Date Range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}
        Current Price: ${data['Close'].iloc[-1]:.2f}
        Price Change: ${data['Close'].iloc[-1] - data['Close'].iloc[0]:.2f} ({((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100:.2f}%)
        52-week High: ${data['High'].max():.2f}
        52-week Low: ${data['Low'].min():.2f}
        Volume: {data['Volume'].iloc[-1]:,}
        """
        
        # Add technical indicator data to description
        for ind in indicators:
            if ind == "20-Day SMA":
                sma_value = data['Close'].rolling(window=20).mean().iloc[-1]
                data_description += f"\n20-Day SMA: ${sma_value:.2f}"
            elif ind == "20-Day EMA":
                ema_value = data['Close'].ewm(span=20).mean().iloc[-1]
                data_description += f"\n20-Day EMA: ${ema_value:.2f}"
            elif ind == "20-Day Bollinger Bands":
                sma = data['Close'].rolling(window=20).mean().iloc[-1]
                std = data['Close'].rolling(window=20).std().iloc[-1]
                bb_upper = sma + 2 * std
                bb_lower = sma - 2 * std
                data_description += f"\nBollinger Bands: Upper=${bb_upper:.2f}, Middle=${sma:.2f}, Lower=${bb_lower:.2f}"
            elif ind == "VWAP":
                vwap_value = (data['Close'] * data['Volume']).sum() / data['Volume'].sum()
                data_description += f"\nVWAP: ${vwap_value:.2f}"

        # Updated prompt asking for a detailed justification of technical analysis and a recommendation.
        analysis_prompt = (
            f"You are a Stock Trader specializing in Technical Analysis at a top financial institution. "
            f"Analyze the stock chart for {ticker} based on the following data:\n\n{data_description}\n\n"
            f"Provide a detailed justification of your analysis, explaining what patterns, signals, and trends you observe. "
            f"Then, based solely on the data, provide a recommendation from the following options: "
            f"'Strong Buy', 'Buy', 'Weak Buy', 'Hold', 'Weak Sell', 'Sell', or 'Strong Sell'. "
            f"Return your output as a JSON object with two keys: 'action' and 'justification'."
        )        # Call the Groq API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a professional financial analyst specializing in technical analysis."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.1,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        
        try:
            # Get response content from Groq
            result_text = response.choices[0].message.content
            # Parse JSON from the response text
            result = json.loads(result_text)
            
            # Validate that we got the expected format
            if 'action' not in result or 'justification' not in result:
                # If the response doesn't have the expected structure, try to fix it
                if len(result) > 0:
                    # Maybe it has different key names but still usable data
                    keys = list(result.keys())
                    if len(keys) >= 2:
                        # Use whatever two keys we have
                        new_result = {
                            "action": result.get(keys[0], "Unknown"),
                            "justification": result.get(keys[1], "No justification provided")
                        }
                        result = new_result
                    else:
                        # Add missing fields
                        if 'action' not in result:
                            result['action'] = "Unknown"
                        if 'justification' not in result:
                            result['justification'] = "No justification provided"
                else:
                    raise ValueError("Empty or invalid JSON object from response")
                
        except json.JSONDecodeError as e:
            result = {"action": "Error", "justification": f"JSON Parsing error: {e}. Raw response: {result_text}"}
        except ValueError as ve:
            result = {"action": "Error", "justification": f"Value Error: {ve}. Raw response: {result_text}"}
        except Exception as e:
            result = {"action": "Error", "justification": f"General Error: {e}. Raw response: {result_text if 'result_text' in locals() else 'Unknown'}"}

        return fig, result

    # Create tabs: first tab for overall summary, subsequent tabs per ticker
    tab_names = ["Overall Summary"] + list(st.session_state["stock_data"].keys())
    tabs = st.tabs(tab_names)

    # List to store overall results
    overall_results = []

    # Process each ticker and populate results
    for i, ticker in enumerate(st.session_state["stock_data"]):
        data = st.session_state["stock_data"][ticker]
        # Analyze ticker: get chart figure and structured output result
        fig, result = analyze_ticker(ticker, data)
        overall_results.append({"Stock": ticker, "Recommendation": result.get("action", "N/A")})
        # In each ticker-specific tab, display the chart and detailed justification
        with tabs[i + 1]:
            st.subheader(f"Analysis for {ticker}")
            st.plotly_chart(fig)
            st.write("**Detailed Justification:**")
            st.write(result.get("justification", "No justification provided."))

    # In the Overall Summary tab, display a table of all results
    with tabs[0]:
        st.subheader("Overall Structured Recommendations")
        df_summary = pd.DataFrame(overall_results)
        st.table(df_summary)
else:
    st.info("Please fetch stock data using the sidebar.")