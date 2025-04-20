from flask import current_app
from oauthlib.oauth2 import WebApplicationClient
import requests

def get_schwab_oauth():
    """Get the Schwab OAuth client."""
    client_id = current_app.config.get('SCHWAB_CLIENT_ID')
    client_secret = current_app.config.get('SCHWAB_CLIENT_SECRET')
    redirect_uri = current_app.config.get('SCHWAB_REDIRECT_URI')
    
    if not all([client_id, client_secret, redirect_uri]):
        raise ValueError("Missing required Schwab OAuth configuration")
    
    client = WebApplicationClient(client_id)
    return client 