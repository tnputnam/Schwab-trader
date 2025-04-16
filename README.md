# Schwab Trader

A modern trading application built with FastAPI, featuring real-time market data, portfolio management, and trading capabilities.

## Features

- Real-time stock quotes and market data
- Portfolio tracking and management
- Live trading interface
- Watchlist functionality
- Price alerts
- Portfolio analytics
- Technical analysis tools

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd schwab-trader
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys:
     - Alpha Vantage API key
     - NewsAPI key

5. Start the application:
```bash
./start.sh
```

## API Keys

- Alpha Vantage: https://www.alphavantage.co/support/#api-key
- NewsAPI: https://newsapi.org/register

## Development

The application uses:
- FastAPI for the backend
- SQLAlchemy for database management
- WebSockets for real-time updates
- Alpha Vantage and NewsAPI for market data

## Project Structure

```
schwab-trader/
├── main.py              # Main application entry point
├── models.py            # Database models
├── requirements.txt     # Python dependencies
├── start.sh            # Startup script
├── templates/          # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── index.html
│   └── trading.html
└── static/             # Static files (CSS, JS, images)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 