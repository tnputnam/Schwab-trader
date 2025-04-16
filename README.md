# Schwab Trader Application

A Python-based trading automation system for Charles Schwab that provides automated trading capabilities and a dashboard interface for monitoring and control.

## Table of Contents
1. [Application Structure](#application-structure)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Features](#features)
7. [API Endpoints](#api-endpoints)
8. [Error Handling](#error-handling)
9. [Security](#security)

## Application Structure
```
schwab_trader/
├── dashboard/
│   └── app.py           # Main Flask application and dashboard
├── browser/
│   └── interface.py     # Browser automation interface
└── start.sh            # Application startup script
```

## Prerequisites
- Python 3.x
- Chrome browser
- Charles Schwab account
- Alpha Vantage API key

## Installation
1. Clone the repository
2. Run the startup script:
   ```bash
   ./start.sh
   ```
   This will:
   - Create a virtual environment
   - Install dependencies
   - Set up configuration
   - Initialize the Chrome browser

## Configuration
The application requires the following environment variables:
- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
- `FLASK_SECRET_KEY`: Secret key for Flask session management

These can be set in the `.env` file that is created during installation.

## Usage
1. Start the application using `start.sh`
2. Access the dashboard at `http://localhost:5000`
3. Log in to your Schwab account through the interface
4. Use the dashboard to:
   - Monitor portfolio
   - Place trades
   - View market data
   - Manage positions

## Features
### Trading Operations
- Portfolio management
- Order placement and tracking
- Position monitoring
- Account balance tracking
- Trade history management

### Market Data
- Real-time quotes
- Stock fundamentals
- Market search
- Historical data analysis
- Performance tracking

### System Management
- Chrome browser control
- Session management
- Error handling
- Logging and monitoring
- Configuration management

## API Endpoints
### System Control
- `/api/system/status` - Get system status
- `/api/system/check_login` - Check Schwab login status
- `/api/system/start_chrome` - Start Chrome browser
- `/api/system/stop_chrome` - Stop Chrome browser

### Trading Operations
- `/api/trading/order` - Place trading orders
- `/api/trading/history` - Get trade history
- `/api/trading/account` - Get account information
- `/api/trading/positions` - Get current positions
- `/api/trading/start` - Start trading session

### Market Data
- `/api/market/search` - Search for market instruments
- `/api/market/quote/<symbol>` - Get quote for symbol
- `/api/assets/search` - Search for assets

### Portfolio Management
- `/api/portfolio/import` - Import portfolio data
- `/api/portfolio/export/pdf` - Export portfolio as PDF

### User Management
- `/api/login/status` - Check login status
- `/api/login/start` - Start login session

## Error Handling
The application includes comprehensive error handling for:
- Trading operations
- Browser automation
- API interactions
- System operations

## Security
- API key management
- Session handling
- Secure configuration
- Error logging
- Access control

## License
[Add your license information here]

## Contributing
[Add contribution guidelines here] 