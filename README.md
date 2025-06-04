# Technical Analysis Agent

A modular Streamlit application that provides technical analysis for stocks and cryptocurrencies using yfinance for data fetching and Groq AI for advanced analysis.

## Features

- Real-time stock and cryptocurrency data using Yahoo Finance API
- Technical indicators including:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Bollinger Bands
  - Volume Weighted Average Price (VWAP)
- Interactive candlestick charts with Plotly
- AI-powered market analysis and recommendations using Groq API
- Clean, modular architecture following best practices

## Project Structure

```
.
├── .env                 # Environment variables (API keys, etc.)
├── .gitignore           # Git ignore file
├── app.py               # Main application entry point
├── logs/                # Directory for application logs
├── main.py              # Original single-file application (legacy)
├── pyproject.toml       # Project dependencies and metadata
├── src/                 # Source code directory
│   ├── components/      # UI components
│   │   ├── analysis_display.py  # Analysis display components
│   │   └── sidebar.py   # Sidebar configuration components
│   ├── config/          # Configuration settings
│   │   └── settings.py  # Application settings
│   ├── models/          # Data models (if needed)
│   ├── services/        # Business logic services
│   │   ├── ai_analysis_service.py   # AI analysis using Groq API
│   │   ├── market_data_service.py   # Market data fetching with yfinance
│   │   └── technical_analysis_service.py  # Technical indicator calculations
│   └── utils/           # Utility functions
│       └── logging_utils.py  # Logging configuration
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd technical-analysis-agent
```

2. Set up environment variables by creating an `.env` file:

```
GROQ_API_KEY=your_groq_api_key
MODEL_NAME=meta-llama/llama-4-maverick-17b-128e-instruct
LOGS_DIR=logs
LOG_FILE=technical_analysis_app.log
LOG_LEVEL=DEBUG
```

3. Install dependencies using Poetry:

```bash
poetry install
```

Or using pip:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
poetry run streamlit run app.py
```

Or

```bash
streamlit run app.py
```

2. Enter stock or cryptocurrency tickers in the sidebar (comma-separated)
3. Set the date range for analysis
4. Select technical indicators to display
5. Click "Fetch Data" to load the data and generate analysis

## Dependencies

- streamlit: Web application framework
- yfinance: Yahoo Finance data API
- plotly: Interactive charts
- groq: Groq API client for AI analysis
- python-dotenv: Environment variable management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
