# Discord Bot Module

This module contains all Discord-related functionality for the Technical Analysis Bot, organized in a modular structure for better maintainability and scalability.

## Structure

```
discord_bot_module/
├── __init__.py                 # Module initialization
├── bot/                        # Core bot functionality
│   ├── __init__.py
│   ├── bot.py                  # Main bot class and initialization
│   └── events.py               # Event handlers
├── commands/                   # Slash commands
│   ├── __init__.py
│   ├── base.py                 # Base command class
│   ├── analyze.py              # Analysis command
│   └── help.py                 # Help command
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── parsers.py              # Input parsing utilities
│   ├── validators.py           # Input validation utilities
│   └── formatters.py           # Text formatting utilities
├── handlers/                   # Interaction handlers
│   ├── __init__.py
│   ├── error_handler.py        # Error handling
│   └── interaction_handler.py  # Interaction utilities
└── embeds/                     # Discord embed creation
    ├── __init__.py
    ├── analysis_embeds.py      # Analysis result embeds
    └── help_embeds.py          # Help information embeds
```

## Key Components

### Bot Core (`bot/`)

- **bot.py**: Main bot class with service initialization
- **events.py**: Event handlers for bot lifecycle events

### Commands (`commands/`)

- **base.py**: Base command class with common functionality
- **analyze.py**: Technical analysis command implementation
- **help.py**: Help command implementation

### Utilities (`utils/`)

- **parsers.py**: Functions to parse user input (dates, tickers, etc.)
- **validators.py**: Functions to validate user input
- **formatters.py**: Functions to format text for Discord display

### Handlers (`handlers/`)

- **error_handler.py**: Centralized error handling
- **interaction_handler.py**: Utilities for managing Discord interactions

### Embeds (`embeds/`)

- **analysis_embeds.py**: Creates embeds for analysis results
- **help_embeds.py**: Creates embeds for help information

## Usage

To use the modular Discord bot:

```python
from discord_bot_module.bot.bot import create_bot
from discord_bot_module.bot.events import setup_events

# Create bot instance
bot = create_bot()

# Setup event handlers
setup_events(bot)

# Run the bot
bot.run(DISCORD_TOKEN)
```

## Adding New Commands

1. Create a new file in `commands/` (e.g., `new_command.py`)
2. Implement the command using the base class
3. Add a `setup(bot)` function
4. Import and call the setup function in `bot/bot.py`

## Benefits of This Structure

- **Modularity**: Each component has a specific responsibility
- **Maintainability**: Easy to find and modify specific functionality
- **Scalability**: Simple to add new commands or features
- **Testability**: Individual components can be tested in isolation
- **Reusability**: Utilities can be shared across commands
