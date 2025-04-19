# Configuration Guide

This document provides detailed information about the configuration options available in the Schwab Trader application.

## Environment Variables

The application uses environment variables for configuration. You can set these variables in your environment or in a `.env` file.

### Base Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Secret key for session management | 'dev' | No |
| `DATABASE_URL` | Database connection URL | 'sqlite:///data/schwab_trader.db' | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | 'INFO' | No |
| `LOG_DIR` | Directory for log files | 'logs' | No |

### API Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SCHWAB_API_KEY` | Schwab API key | None | Yes |
| `SCHWAB_API_SECRET` | Schwab API secret | None | Yes |
| `SCHWAB_API_BASE_URL` | Schwab API base URL | 'https://api.schwab.com' | No |

### News Service Configuration

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `NEWS_UPDATE_INTERVAL` | News update interval in seconds | 300 | 60-3600 |
| `NEWS_MAX_ARTICLES` | Maximum number of articles to store | 100 | - |
| `NEWS_SOURCES` | List of news sources as JSON array | ["reuters", "bloomberg", "cnbc"] | - |

### Analysis Configuration

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `ANALYSIS_HISTORICAL_DAYS` | Number of days for historical analysis | 365 | 30-3650 |
| `ANALYSIS_VOLUME_WINDOW` | Window size for volume analysis | 20 | - |
| `ANALYSIS_RSI_PERIOD` | Period for RSI calculation | 14 | - |
| `ANALYSIS_MACD_FAST` | Fast period for MACD | 12 | - |
| `ANALYSIS_MACD_SLOW` | Slow period for MACD | 26 | - |
| `ANALYSIS_MACD_SIGNAL` | Signal period for MACD | 9 | - |

### Real-time Data Configuration

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `REALTIME_UPDATE_INTERVAL` | Update interval in seconds | 5 | 1-60 |
| `REALTIME_MAX_RETRIES` | Maximum number of retries | 3 | - |
| `REALTIME_RETRY_DELAY` | Delay between retries in seconds | 5 | - |

### Strategy Testing Configuration

| Variable | Description | Default | Range |
|----------|-------------|---------|-------|
| `STRATEGY_TEST_START_DATE` | Start date for strategy testing | '2020-01-01' | - |
| `STRATEGY_TEST_END_DATE` | End date for strategy testing | '2023-12-31' | - |
| `STRATEGY_TEST_INITIAL_CAPITAL` | Initial capital for testing | 100000 | 1000-1000000 |
| `STRATEGY_TEST_COMMISSION` | Commission per trade | 0.01 | 0-0.1 |

## Environment-Specific Settings

### Development Environment

- Debug mode enabled
- SQLAlchemy echo enabled
- Faster update intervals for testing
- Less secure cookie settings

### Testing Environment

- In-memory database
- CSRF protection disabled
- Very fast update intervals
- Minimal logging

### Production Environment

- Debug mode disabled
- Secure cookie settings
- File-based logging with rotation
- Standard update intervals

## Configuration Validation

The application validates configuration values against defined rules during initialization. If any values are outside their specified ranges, warnings will be logged.

## Best Practices

1. **Security**
   - Always use strong `SECRET_KEY` in production
   - Keep API keys and secrets secure
   - Use HTTPS in production

2. **Performance**
   - Adjust update intervals based on your needs
   - Monitor memory usage with large data sets
   - Use appropriate cache settings

3. **Development**
   - Use development environment for local development
   - Test with different configurations
   - Monitor logs for configuration warnings

## Example .env File

```env
# Base Configuration
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///data/schwab_trader.db
LOG_LEVEL=INFO

# API Configuration
SCHWAB_API_KEY=your-api-key
SCHWAB_API_SECRET=your-api-secret

# News Configuration
NEWS_UPDATE_INTERVAL=300
NEWS_MAX_ARTICLES=100
NEWS_SOURCES=["reuters", "bloomberg", "cnbc"]

# Analysis Configuration
ANALYSIS_HISTORICAL_DAYS=365
ANALYSIS_VOLUME_WINDOW=20
ANALYSIS_RSI_PERIOD=14

# Real-time Configuration
REALTIME_UPDATE_INTERVAL=5
REALTIME_MAX_RETRIES=3
REALTIME_RETRY_DELAY=5

# Strategy Testing
STRATEGY_TEST_START_DATE=2020-01-01
STRATEGY_TEST_END_DATE=2023-12-31
STRATEGY_TEST_INITIAL_CAPITAL=100000
STRATEGY_TEST_COMMISSION=0.01
``` 