# Usage Tracking System

This document explains the usage tracking and cost control system for the Discord Technical Analysis Bot.

## Overview

The bot implements a comprehensive usage tracking system to prevent API costs from exceeding user subscription revenue. All users have uniform limits of **$10 per month** for AI analysis features.

## User Limits

All users have the same limits:

- **Monthly Limit**: $10.00 per month
- **Daily Limit**: $2.00 per day
- **Hourly Limit**: 20 requests per hour

## How It Works

### Cost Tracking

- Every AI analysis request is tracked
- Costs are estimated based on Groq API token usage
- Technical analysis and chart generation are free
- Only AI-powered market analysis counts toward limits

### Limit Enforcement

- Users are blocked from making AI requests when limits are exceeded
- Technical analysis (without AI) continues to work
- Limits reset automatically (monthly/daily/hourly)

### User Experience

- Users see usage warnings at 80% of limits
- Clear error messages when limits are exceeded
- Users can check their usage with `/my_usage` command

## Setup

### 1. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Usage Limits (Uniform for all users)
DEFAULT_MONTHLY_LIMIT=10.0
DEFAULT_DAILY_LIMIT=2.0
DEFAULT_HOURLY_REQUESTS=20

# Admin Configuration (comma-separated Discord user IDs)
ADMIN_USER_IDS=123456789012345678,987654321098765432

# Cost Configuration
GROQ_COST_PER_1K_TOKENS=0.0002
USAGE_ALERT_THRESHOLD=0.8
```

### 2. Initialize Database

Run the setup script to create the database:

```bash
poetry run python scripts/setup_database.py
```

### 3. Migrate Existing Users (if applicable)

If upgrading from a previous version:

```bash
poetry run python scripts/migrate_to_uniform_limits.py
```

## User Commands

### `/my_usage`

Shows the user's current usage statistics including:

- Monthly and daily usage vs limits
- Usage breakdown by service
- Warnings and tips

### `/help`

Provides information about bot commands and features.

## Admin Commands

### `/usage_stats [days]`

**Admin Only** - Shows overall usage statistics:

- Total users, requests, and costs
- Top users by cost
- Usage trends

### `/user_usage <user> [days]`

**Admin Only** - Shows detailed usage for a specific user:

- Usage breakdown by service
- Current limits and status
- Token usage statistics

### `/set_user_limits <user> [monthly_limit] [daily_limit] [requests_per_hour]`

**Admin Only** - Manually set limits for a specific user:

- Override default limits for special cases
- Set custom monthly/daily/hourly limits

## Limit Details

### How Limits Work

- **Monthly**: Resets on the 1st of each month
- **Daily**: Resets at midnight UTC
- **Hourly**: Rolling 60-minute window
- **Cost Tracking**: Based on actual API token usage

### Cost Estimation

The system estimates costs based on:

- **Input tokens**: From the analysis prompt
- **Output tokens**: From the AI response
- **Rate**: Configurable per 1K tokens (default: $0.0002)

## Database Schema

### `usage_records` Table

- `user_id`: Discord user ID
- `timestamp`: When the request was made
- `api_service`: Which service was used (groq, coingecko, etc.)
- `tokens_used`: Number of tokens consumed
- `estimated_cost`: Calculated cost in USD
- `request_type`: Type of request (analysis, chart, etc.)
- `metadata`: Additional context (JSON)

### `user_limits` Table

- `user_id`: Discord user ID (primary key)
- `monthly_limit`: Monthly cost limit in USD
- `daily_limit`: Daily cost limit in USD
- `requests_per_hour`: Hourly request limit
- `created_at`: When limits were first set
- `updated_at`: When limits were last modified

## Monitoring

### Regular Monitoring

1. Check `/usage_stats` weekly to monitor overall usage
2. Review top users to identify heavy usage patterns
3. Adjust individual limits if needed for special cases

### Database Maintenance

- Database is SQLite - minimal maintenance required
- Automatic indexes for performance
- Consider archiving old data if database grows large

## Security Notes

- Database contains user IDs and usage patterns
- Keep the database file secure
- Admin commands are restricted to configured admin user IDs
- Usage data should be considered sensitive user information

## Troubleshooting

### User Can't Use AI Commands

- Check if they've exceeded limits with `/user_usage <user>`
- Verify their limits are set correctly
- Check database connectivity

### High Costs

- Review top users with `/usage_stats`
- Check if cost estimation is accurate
- Consider lowering default limits if needed

### Database Issues

- Check if `data/usage_tracker.db` exists and is writable
- Re-run setup script if needed
- Check logs for database errors
