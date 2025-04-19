# Configuration Migration Guide

This guide helps you migrate your configuration from previous versions of Schwab Trader to the latest version.

## Version 2.0 Migration

### New Configuration Options

The following new configuration options have been added:

1. **Analysis Configuration**
   - `ANALYSIS_VOLUME_WINDOW`: Window size for volume analysis (default: 20)
   - `ANALYSIS_RSI_PERIOD`: Period for RSI calculation (default: 14)
   - `ANALYSIS_MACD_FAST`: Fast period for MACD (default: 12)
   - `ANALYSIS_MACD_SLOW`: Slow period for MACD (default: 26)
   - `ANALYSIS_MACD_SIGNAL`: Signal period for MACD (default: 9)

2. **Real-time Data Configuration**
   - `REALTIME_UPDATE_INTERVAL`: Update interval in seconds (default: 5)
   - `REALTIME_MAX_RETRIES`: Maximum number of retries (default: 3)
   - `REALTIME_RETRY_DELAY`: Delay between retries in seconds (default: 5)

3. **Strategy Testing Configuration**
   - `STRATEGY_TEST_START_DATE`: Start date for testing (default: '2020-01-01')
   - `STRATEGY_TEST_END_DATE`: End date for testing (default: '2023-12-31')
   - `STRATEGY_TEST_INITIAL_CAPITAL`: Initial capital (default: 100000)
   - `STRATEGY_TEST_COMMISSION`: Commission per trade (default: 0.01)

### Changed Configuration Options

The following configuration options have been modified:

1. **News Service**
   - `NEWS_UPDATE_INTERVAL`: Now has validation (60-3600 seconds)
   - `NEWS_SOURCES`: Now requires JSON array format

2. **API Configuration**
   - `SCHWAB_API_BASE_URL`: Now requires valid URL format

### Removed Configuration Options

The following configuration options have been removed:

1. `OLD_NEWS_FORMAT`: Replaced by standardized JSON format
2. `LEGACY_UPDATE_MODE`: Replaced by new real-time configuration

## Migration Steps

### 1. Backup Your Configuration

```bash
cp .env .env.backup
```

### 2. Update Your .env File

Add the new configuration options with their default values:

```env
# Analysis Configuration
ANALYSIS_VOLUME_WINDOW=20
ANALYSIS_RSI_PERIOD=14
ANALYSIS_MACD_FAST=12
ANALYSIS_MACD_SLOW=26
ANALYSIS_MACD_SIGNAL=9

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

### 3. Update Format Requirements

Ensure your existing configuration values meet the new format requirements:

```env
# Update NEWS_SOURCES to JSON array format
NEWS_SOURCES=["reuters", "bloomberg", "cnbc"]

# Ensure SCHWAB_API_BASE_URL is a valid URL
SCHWAB_API_BASE_URL=https://api.schwab.com
```

### 4. Validate Your Configuration

Run the configuration validation:

```bash
python -c "from schwab_trader.config import Config; print(Config.validate_config())"
```

### 5. Test Your Application

Start your application and check the logs for any configuration warnings:

```bash
python run.py
```

## Troubleshooting

### Common Issues

1. **Invalid Date Format**
   - Ensure dates are in YYYY-MM-DD format
   - Example: `STRATEGY_TEST_START_DATE=2020-01-01`

2. **Invalid JSON Format**
   - Ensure arrays are properly formatted
   - Example: `NEWS_SOURCES=["source1", "source2"]`

3. **Value Out of Range**
   - Check the validation rules in the configuration guide
   - Adjust values to be within the specified ranges

### Getting Help

If you encounter issues during migration:

1. Check the application logs for specific error messages
2. Refer to the [Configuration Guide](configuration.md)
3. Open an issue on the project's GitHub repository

## Rollback Procedure

If you need to rollback your configuration:

1. Restore your backup:
   ```bash
   cp .env.backup .env
   ```

2. Restart your application:
   ```bash
   python run.py
   ``` 