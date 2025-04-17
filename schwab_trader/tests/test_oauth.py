import os
import sys
from requests_oauthlib import OAuth2Session
import webbrowser
import logging
import json
from urllib.parse import urlparse, parse_qs, unquote
import base64
import requests

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SchwabOAuthTest:
    def __init__(self):
        # Your OAuth2 settings
        self.client_id = "1wzwOrhivb2PkR1UCAUVTKYqC4MTNYlj"
        # Add your client secret here
        self.client_secret = input("Enter your client secret: ").strip()
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
    
    def get_basic_auth_header(self):
        """Create Basic Auth header from client_id and client_secret"""
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
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
            authorization_url, state = self.oauth.authorization_url(self.auth_url)
            
            print("\nSchwab OAuth Test")
            print("================")
            print(f"\n1. Opening authorization URL in your browser...")
            print(f"URL: {authorization_url}")
            
            webbrowser.open(authorization_url)
            
            print("\n2. After authorizing, copy the full callback URL from your browser")
            callback_url = input("Enter the callback URL (without @ symbol): ").strip()
            
            # Parse the callback URL
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            code = params.get('code', [None])[0]
            
            if not code:
                print("Error: No authorization code found in callback URL")
                return
                
            print("\nExchanging code for token...")
            
            # Prepare token request
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri
            }
            
            headers = {
                'Authorization': self.get_basic_auth_header(),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            # Make token request
            print("\nMaking token request...")
            response = requests.post(
                self.token_url,
                data=data,
                headers=headers
            )
            
            print(f"\nToken Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                token = response.json()
                print("\nSuccessfully obtained token!")
                
                # Try to get accounts
                print("\nAttempting to get accounts...")
                accounts_response = requests.get(
                    "https://api.schwabapi.com/v1/accounts",
                    headers={
                        "Authorization": f"Bearer {token['access_token']}",
                        "Accept": "application/json"
                    }
                )
                
                print(f"\nAccounts Response:")
                print(f"Status: {accounts_response.status_code}")
                print(f"Body: {accounts_response.text}")
            else:
                print(f"\nError getting token: {response.text}")
                
        except Exception as e:
            print(f"\nError during OAuth flow:")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {str(e)}")

if __name__ == "__main__":
    tester = SchwabOAuthTest()
    tester.test_oauth_flow() 