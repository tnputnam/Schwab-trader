"""News service for fetching and processing market news."""
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
from schwab_trader.utils.logging_utils import get_logger
from schwab_trader.utils.config_utils import get_config
from schwab_trader.utils.error_utils import APIError, ConfigurationError

logger = get_logger(__name__)

class NewsService:
    """Service for fetching and processing market news."""
    
    def __init__(self):
        """Initialize the news service with configuration."""
        self.config = get_config()
        self._validate_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SchwabTrader/1.0',
            'Accept': 'application/json'
        })
        
    def _validate_config(self) -> None:
        """Validate required configuration settings."""
        required_settings = [
            'NEWS_API_KEY',
            'NEWS_API_BASE_URL',
            'NEWS_CACHE_TTL',
            'NEWS_MAX_ARTICLES'
        ]
        
        for setting in required_settings:
            if not hasattr(self.config, setting):
                raise ConfigurationError(f"Missing required setting: {setting}")
    
    def _validate_response(self, response: requests.Response) -> None:
        """Validate API response and raise appropriate errors."""
        if response.status_code == 401:
            raise APIError("Invalid API credentials", status_code=401)
        elif response.status_code == 429:
            raise APIError("API rate limit exceeded", status_code=429)
        elif response.status_code >= 500:
            raise APIError("News API service unavailable", status_code=response.status_code)
        elif not response.ok:
            raise APIError(f"News API error: {response.text}", status_code=response.status_code)
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make an API request with consistent error handling."""
        try:
            url = f"{self.config.NEWS_API_BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            self._validate_response(response)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise APIError(f"Failed to fetch news: {str(e)}")
    
    def get_market_news(self, limit: int = 10) -> List[Dict]:
        """Fetch market news articles."""
        try:
            params = {
                'category': 'market',
                'limit': min(limit, self.config.NEWS_MAX_ARTICLES),
                'sortBy': 'publishedAt'
            }
            data = self._make_request('market-news', params)
            return self._process_articles(data.get('articles', []))
        except Exception as e:
            logger.error(f"Error fetching market news: {str(e)}")
            raise
    
    def get_business_headlines(self, limit: int = 10) -> List[Dict]:
        """Fetch business headlines."""
        try:
            params = {
                'category': 'business',
                'limit': min(limit, self.config.NEWS_MAX_ARTICLES),
                'sortBy': 'publishedAt'
            }
            data = self._make_request('business-headlines', params)
            return self._process_articles(data.get('articles', []))
        except Exception as e:
            logger.error(f"Error fetching business headlines: {str(e)}")
            raise
    
    def search_news(self, query: str, page: int = 1, per_page: int = 10) -> Dict:
        """Search for news articles."""
        try:
            params = {
                'q': query,
                'page': page,
                'pageSize': min(per_page, self.config.NEWS_MAX_ARTICLES),
                'sortBy': 'publishedAt'
            }
            data = self._make_request('search', params)
            return {
                'articles': self._process_articles(data.get('articles', [])),
                'total': data.get('totalResults', 0),
                'page': page
            }
        except Exception as e:
            logger.error(f"Error searching news: {str(e)}")
            raise
    
    def _process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process and standardize article data."""
        processed = []
        for article in articles:
            try:
                processed.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'category': article.get('category', 'general')
                })
            except Exception as e:
                logger.warning(f"Error processing article: {str(e)}")
                continue
        return processed 