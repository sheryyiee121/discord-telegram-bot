"""
Configuration file for Discord to Telegram Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Discord OAuth2 Configuration
# You need to create a Discord application at https://discord.com/developers/applications
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', '')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET', '')

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Redirect URI for Discord OAuth (should match what you set in Discord app settings)
DISCORD_REDIRECT_URI = f'http://localhost:{FLASK_PORT}/discord/callback'

# Discord API URLs
DISCORD_API_BASE_URL = 'https://discord.com/api'
DISCORD_AUTHORIZATION_BASE_URL = DISCORD_API_BASE_URL + '/oauth2/authorize'
DISCORD_TOKEN_URL = DISCORD_API_BASE_URL + '/oauth2/token'
