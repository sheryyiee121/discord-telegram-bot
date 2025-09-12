import os
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv('production.env')

# Get the values
client_id = os.getenv('DISCORD_CLIENT_ID')
redirect_uri = os.getenv('DISCORD_REDIRECT_URI')

print("=== DISCORD OAUTH DEBUG ===")
print(f"Client ID: {client_id}")
print(f"Redirect URI from env: {redirect_uri}")
print(f"URL encoded redirect URI: {urllib.parse.quote(redirect_uri, safe='')}")
print()
print("=== INSTRUCTIONS ===")
print("1. Go to Discord Developer Portal")
print("2. Make sure you have EXACTLY this redirect URI:")
print(f"   {redirect_uri}")
print()
print("3. The authorization URL would be:")
auth_url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={urllib.parse.quote(redirect_uri, safe='')}&response_type=code&scope=identify"
print(auth_url)
print()
print("4. Make sure there are NO SPACES before or after the redirect URI in Discord Portal")
print("5. Make sure you're using the exact same URL to access your app:")
print(f"   {redirect_uri.replace('/discord/callback', '')}")
