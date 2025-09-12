from dotenv import load_dotenv
import os

# Load production.env
load_dotenv('production.env')

print("=== Environment Variables Debug ===")
print(f"DISCORD_CLIENT_ID: {os.getenv('DISCORD_CLIENT_ID')}")
print(f"DISCORD_CLIENT_SECRET: {os.getenv('DISCORD_CLIENT_SECRET')}")
print(f"DISCORD_REDIRECT_URI: {os.getenv('DISCORD_REDIRECT_URI')}")
print(f"SECRET_KEY exists: {bool(os.getenv('SECRET_KEY'))}")
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
print(f"OAUTHLIB_INSECURE_TRANSPORT: {os.getenv('OAUTHLIB_INSECURE_TRANSPORT')}")

# Check if production.env exists
import os.path
print(f"\nproduction.env exists: {os.path.exists('production.env')}")

# Print current working directory
print(f"Current directory: {os.getcwd()}")
