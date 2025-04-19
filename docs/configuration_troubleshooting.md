# Configuration Troubleshooting Guide

This guide helps you diagnose and resolve common configuration issues in the Schwab Trader application.

## Common Issues and Solutions

### 1. Environment Variables Not Loading

**Symptoms:**
- Configuration values are not being set
- Default values are being used instead of custom values
- Environment variables are not being recognized

**Solutions:**
1. Check if the `.env` file exists in the correct location
2. Verify the format of your `.env` file:
   ```env
   # Correct format
   KEY=value
   
   # Incorrect formats
   KEY = value  # Spaces around =
   KEY:value    # Using : instead of =
   ```
3. Ensure the `.env` file is being loaded:
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); print(os.environ.get('YOUR_KEY'))"
   ```

### 2. Validation Errors

**Symptoms:**
- Application logs show configuration validation warnings
- Certain features are not working as expected
- Values are being reset to defaults

**Solutions:**
1. Check the validation rules for your configuration:
   ```python
   from schwab_trader.config import Config
   print(Config.validate_config())
   ```
2. Ensure values are within the specified ranges:
   - `NEWS_UPDATE_INTERVAL`: 60-3600 seconds
   - `ANALYSIS_HISTORICAL_DAYS`: 30-3650 days
   - `REALTIME_UPDATE_INTERVAL`: 1-60 seconds

### 3. Format Validation Issues

**Symptoms:**
- JSON parsing errors
- Date format errors
- URL validation failures

**Solutions:**
1. For JSON arrays:
   ```env
   # Correct format
   NEWS_SOURCES=["reuters", "bloomberg"]
   
   # Incorrect formats
   NEWS_SOURCES=reuters,bloomberg
   NEWS_SOURCES='["reuters", "bloomberg"]'
   ```
2. For dates:
   ```env
   # Correct format
   STRATEGY_TEST_START_DATE=2020-01-01
   
   # Incorrect formats
   STRATEGY_TEST_START_DATE=01/01/2020
   STRATEGY_TEST_START_DATE=2020.01.01
   ```
3. For URLs:
   ```env
   # Correct format
   SCHWAB_API_BASE_URL=https://api.schwab.com
   
   # Incorrect formats
   SCHWAB_API_BASE_URL=api.schwab.com
   SCHWAB_API_BASE_URL=http://api.schwab.com
   ```

### 4. Directory Creation Issues

**Symptoms:**
- Log files are not being created
- Session files are not being stored
- Permission errors when creating directories

**Solutions:**
1. Check directory permissions:
   ```bash
   ls -la /path/to/your/app
   ```
2. Ensure the application has write permissions:
   ```bash
   chmod 755 /path/to/your/app
   ```
3. Verify directory paths in configuration:
   ```env
   LOG_DIR=logs
   SESSION_FILE_DIR=sessions
   ```

### 5. Environment-Specific Issues

**Development Environment:**
- If debug mode is not working:
  ```env
  FLASK_ENV=development
  DEBUG=True
  ```
- If SQL logging is not showing:
  ```env
  SQLALCHEMY_ECHO=True
  ```

**Production Environment:**
- If secure cookies are causing issues:
  ```env
  SESSION_COOKIE_SECURE=False  # Only for testing
  ```
- If logging is not working:
  ```env
  LOG_LEVEL=DEBUG  # Temporarily for troubleshooting
  ```

### 6. API Configuration Issues

**Symptoms:**
- API calls failing
- Authentication errors
- Rate limiting issues

**Solutions:**
1. Verify API credentials:
   ```env
   SCHWAB_API_KEY=your_key
   SCHWAB_API_SECRET=your_secret
   ```
2. Check API base URL:
   ```env
   SCHWAB_API_BASE_URL=https://api.schwab.com
   ```
3. Adjust rate limiting if needed:
   ```env
   RATELIMIT_DEFAULT=500 per day
   ```

## Debugging Tools

### 1. Configuration Dump

To see all current configuration values:
```python
from schwab_trader.config import Config
config = Config()
for key, value in vars(config).items():
    if not key.startswith('_'):
        print(f"{key}: {value}")
```

### 2. Environment Check

To verify environment variables:
```bash
# Linux/Mac
env | grep SCHWAB

# Windows
set | findstr SCHWAB
```

### 3. Log Analysis

Check application logs for configuration-related messages:
```bash
tail -f logs/schwab_trader.log
```

## Getting Help

If you're still experiencing issues:

1. Check the [Configuration Guide](configuration.md) for detailed documentation
2. Review the [Migration Guide](configuration_migration.md) for version-specific changes
3. Open an issue on the project's GitHub repository with:
   - Your configuration file (with sensitive data removed)
   - Error messages from the logs
   - Steps to reproduce the issue
   - Your environment details (OS, Python version, etc.) 