import os
import sys
from requests_oauthlib import OAuth2Session
import webbrowser
import logging
import json
from urllib.parse import urlparse, parse_qs, unquote

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SchwabOAuthTest:
    def __init__(self):
        # Your OAuth2 settings
        self.client_id = "1wzwOrhivb2PkR1UCAUVTKYqC4MTNYlj"
        self.auth_url = "https://api.schwabapi.com/v1/oauth/authorize"
        self.token_url = "https://api.schwabapi.com/v1/oauth/token"
        self.redirect_uri = "https://developer.schwab.com/oauth2-redirect.html"
        self.scope = ["readonly"]
        
        # Initialize OAuth session with debug
        self.oauth = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
    
    def clean_url(self, url):
        """Clean the URL by removing any unwanted characters"""
        # Remove @ symbol if it exists at the start
        if url.startswith('@'):
            url = url[1:]
        # Ensure the URL starts with https://
        if not url.startswith('https://'):
            url = 'https://' + url
            
        print("\nURL Cleaning Steps:")
        print(f"1. Original URL: {url}")
        print(f"2. URL after @ removal: {url}")
        print(f"3. Final URL: {url}")
        return url
    
    def parse_callback_url(self, callback_url):
        """Parse the callback URL to extract code and other parameters"""
        # Clean the URL first
        clean_callback_url = self.clean_url(callback_url)
        
        # Parse URL and parameters
        parsed = urlparse(clean_callback_url)
        params = parse_qs(parsed.query)
        
        # Debug output
        print("\nURL Parsing Results:")
        print(f"Scheme: {parsed.scheme}")
        print(f"Netloc: {parsed.netloc}")
        print(f"Path: {parsed.path}")
        print(f"Query parameters:")
        for key, value in params.items():
            print(f"  {key}: {value[0]}")
        
        return params, clean_callback_url
    
    def test_oauth_flow(self):
        try:
            # Get authorization URL
            authorization_url, state = self.oauth.authorization_url(
                self.auth_url
            )
            
            print("\nSchwab OAuth Test")
            print("================")
            print(f"\n1. Opening authorization URL in your browser...")
            print(f"URL: {authorization_url}")
            
            # Open the URL in browser
            webbrowser.open(authorization_url)
            
            # Wait for user to authorize and get the callback URL
            print("\n2. After authorizing, copy the full callback URL from your browser")
            print("   NOTE: If you see an @ symbol at the start, please remove it before pasting")
            callback_url = input("Enter the callback URL: ").strip()
            
            # Parse and clean the callback URL
            params, clean_callback_url = self.parse_callback_url(callback_url)
            
            print("\nAuthorization Code Details:")
            if 'code' in params:
                code = params['code'][0]
                print(f"Code: {code}")
                print(f"Code length: {len(code)}")
            
            try:
                print("\nAttempting to exchange code for token...")
                token = self.oauth.fetch_token(
                    token_url=self.token_url,
                    authorization_response=clean_callback_url,
                    client_id=self.client_id,
                    include_client_id=True
                )
                
                print("\nToken exchange successful!")
                print(f"Token type: {token.get('token_type', 'N/A')}")
                print(f"Access token length: {len(token.get('access_token', ''))}")
                
                # Try to get accounts
                print("\nAttempting to get accounts...")
                response = self.oauth.get(
                    "https://api.schwabapi.com/v1/accounts",
                    headers={
                        "Authorization": f"Bearer {token['access_token']}",
                        "Accept": "application/json"
                    }
                )
                
                print(f"\nAccount API Response:")
                print(f"Status code: {response.status_code}")
                print(f"Response body: {response.text}")
                
            except Exception as token_error:
                print(f"\nError during token exchange:")
                print(f"Error type: {type(token_error).__name__}")
                print(f"Error message: {str(token_error)}")
                
        except Exception as e:
            print(f"\nGeneral error:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")

if __name__ == "__main__":
    # Run the test
    tester = SchwabOAuthTest()
    tester.test_oauth_flow() 