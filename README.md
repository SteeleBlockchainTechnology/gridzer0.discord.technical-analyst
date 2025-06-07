# Technical Analysis Agent

A comprehensive technical analysis application that provides multiple interfaces for analyzing stocks and cryptocurrencies. Features include a Discord bot for real-time analysis, CLI interface for terminal users, and modular architecture for easy extension.

## Features

- **Multiple Interfaces**: Discord bot, CLI, and extensible architecture
- **Real-time Data**: Stock and cryptocurrency data using Yahoo Finance API
- **Technical Indicators**:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Bollinger Bands
  - Volume Weighted Average Price (VWAP)
- **Interactive Charts**: Candlestick charts with Plotly
- **AI Analysis**: Powered by Groq API for intelligent market insights
- **Modular Design**: Clean, maintainable, and extensible architecture

## Project Structure

```
.
├── .env                 # Environment variables (API keys, etc.)
├── .gitignore           # Git ignore file
├── main.py              # Main application entry point
├── logs/                # Directory for application logs
├── pyproject.toml       # Project dependencies and metadata
├── discord_bot_module/  # Discord bot implementation
│   ├── bot/             # Core bot functionality
│   ├── commands/        # Slash commands
│   ├── embeds/          # Discord embed creation
│   ├── handlers/        # Interaction handlers
│   └── utils/           # Discord-specific utilities
├── src/                 # Core source code directory
│   ├── config/          # Configuration settings
│   │   └── settings.py  # Application settings
│   ├── models/          # Data models
│   ├── services/        # Business logic services
│   │   ├── ai_analysis_service.py     # AI analysis using Groq API
│   │   ├── market_data_service.py     # Market data fetching
│   │   └── technical_analysis_service.py  # Technical indicators
│   └── utils/           # Utility functions
│       └── logging_utils.py  # Logging configuration
```

## Installation

1. Clone the repository:

````bash
git clone <repository-url>
## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd technical-analysis-agent
````

2. Set up environment variables by creating an `.env` file:

```
GROQ_API_KEY=your_groq_api_key
DISCORD_TOKEN=your_discord_bot_token
MODEL_NAME=meta-llama/llama-4-maverick-17b-128e-instruct
DISCORD_STATUS=Technical Analysis
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

The application supports multiple modes of operation through the main.py entry point:

### Discord Bot Mode

Run the Discord bot for real-time technical analysis in Discord servers:

```bash
poetry run python main.py discord
```

With environment validation:

```bash
poetry run python main.py discord --validate
```

### CLI Mode

Interactive command-line interface for terminal users:

```bash
poetry run python main.py cli
```

Features:

- Analyze individual tickers
- List available technical indicators
- Save charts to HTML files
- AI-powered analysis

### Test Mode

Run the application test suite:

```bash
poetry run python main.py test
```

### Help

View all available options:

```bash
poetry run python main.py --help
```

````

Or

```bash
streamlit run app.py
````

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
