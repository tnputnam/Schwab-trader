from requests_oauthlib import OAuth2Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchwabOAuth:
    def __init__(self):
        # Your specific OAuth2 settings
        self.client_id = "1wzwOrhivb2PkR1UCAUVTKYqC4MTNYlj"  # Your client ID
        self.auth_url = "https://api.schwabapi.com/v1/oauth/authorize"
        self.token_url = "https://api.schwabapi.com/v1/oauth/token"
        self.redirect_uri = "https://developer.schwab.com/oauth2-redirect.html"
        self.scope = ["readonly"]
        
        # Initialize OAuth session
        self.oauth = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
    
    def get_authorization_url(self):
        """Get the URL where the user needs to authorize the app"""
        authorization_url, state = self.oauth.authorization_url(
            self.auth_url,
            response_type='code'
        )
        logger.info(f"Generated authorization URL: {authorization_url}")
        return authorization_url, state

    def fetch_token(self, authorization_response):
        """Exchange authorization code for access token"""
        try:
            token = self.oauth.fetch_token(
                self.token_url,
                authorization_response=authorization_response,
                client_id=self.client_id,
                include_client_id=True
            )
            logger.info("Successfully fetched token")
            return token
        except Exception as e:
            logger.error(f"Error fetching token: {str(e)}")
            return None

    def get_accounts(self, token):
        """Get account information using the access token"""
        try:
            response = self.oauth.get(
                "https://api.schwabapi.com/v1/accounts",
                headers={
                    "Authorization": f"Bearer {token['access_token']}",
                    "Accept": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            return None 