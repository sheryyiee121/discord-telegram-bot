from flask import Flask, redirect, session, request, url_for
from requests_oauthlib import OAuth2Session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('production.env')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'test-secret-key')

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI')
DISCORD_API_BASE_URL = 'https://discord.com/api'
DISCORD_AUTHORIZATION_BASE_URL = DISCORD_API_BASE_URL + '/oauth2/authorize'
DISCORD_TOKEN_URL = DISCORD_API_BASE_URL + '/oauth2/token'

print("=== OAuth Configuration ===")
print(f"Client ID: {DISCORD_CLIENT_ID}")
print(f"Client Secret: {DISCORD_CLIENT_SECRET[:10]}..." if DISCORD_CLIENT_SECRET else "No secret")
print(f"Redirect URI: {DISCORD_REDIRECT_URI}")
print("==========================")

@app.route('/')
def index():
    return '''
    <h1>Discord OAuth Test</h1>
    <a href="/login">Login with Discord</a>
    '''

@app.route('/login')
def login():
    discord = OAuth2Session(DISCORD_CLIENT_ID, redirect_uri=DISCORD_REDIRECT_URI, scope=['identify'])
    authorization_url, state = discord.authorization_url(DISCORD_AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    
    print(f"\n=== LOGIN ===")
    print(f"Authorization URL: {authorization_url}")
    print(f"State: {state}")
    
    return redirect(authorization_url)

@app.route('/discord/callback')
def callback():
    print(f"\n=== CALLBACK ===")
    print(f"Full URL: {request.url}")
    print(f"Args: {request.args}")
    
    try:
        discord = OAuth2Session(DISCORD_CLIENT_ID, redirect_uri=DISCORD_REDIRECT_URI)
        token = discord.fetch_token(
            DISCORD_TOKEN_URL,
            client_secret=DISCORD_CLIENT_SECRET,
            authorization_response=request.url
        )
        print(f"Token received: {token}")
        return f"<h1>Success!</h1><pre>{token}</pre>"
    except Exception as e:
        print(f"Error: {e}")
        return f"<h1>Error</h1><pre>{e}</pre>"

if __name__ == '__main__':
    # Allow OAuth over HTTP for localhost
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, port=5000)
