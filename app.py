from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import discord
import asyncio
import threading
from telegram import Bot
from telegram.ext import Application
import os
from dotenv import load_dotenv
import time
import requests
from requests_oauthlib import OAuth2Session
from flask_session import Session
import secrets
import openai

# OAuth2 transport setting - use environment variable
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '0')

load_dotenv('production.env')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/discord/callback')
DISCORD_API_BASE_URL = 'https://discord.com/api'
DISCORD_AUTHORIZATION_BASE_URL = DISCORD_API_BASE_URL + '/oauth2/authorize'
DISCORD_TOKEN_URL = DISCORD_API_BASE_URL + '/oauth2/token'

# Telegram Configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8021291312:AAGvseQBHdoKMzgTFtdLgqYNeJ69nOM6Efk')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1001002840428854')

# Auto-detected Discord Bot Configuration
DISCORD_BOT_TOKEN = 'MTQxMjAyODk1MjQwMjQ2NDc4MQ.GibYXo.Xnziw6rzyIpQVMxNismf_c1qoFsnOOV7R8kyls'

# ChatGPT Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Global variables to store bot instances and settings
discord_client = None
telegram_bot = None
bot_settings = {
    'discord_token': '',  # OAuth access token for user identification
    'discord_bot_token': DISCORD_BOT_TOKEN,  # Bot token for message reading (auto-configured)
    'discord_channel_urls': [],  # Multiple channel URLs
    'telegram_bot_token': TELEGRAM_BOT_TOKEN,
    'telegram_chat_id': TELEGRAM_CHAT_ID,
    'is_running': False,
    'discord_user': None,
    'enable_customization': False,
    'custom_prompt': ''
}

class DiscordBot(discord.Client):
    def __init__(self, channel_urls, telegram_bot, telegram_chat_id, enable_customization=False, custom_prompt=""):
        # Use minimal intents that don't require privileged access
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        # Enable message content intent for ChatGPT processing
        intents.message_content = True
        intents.members = False
        intents.presences = False
        super().__init__(intents=intents)
        self.channel_urls = channel_urls if isinstance(channel_urls, list) else [channel_urls]
        self.telegram_bot = telegram_bot
        self.telegram_chat_id = telegram_chat_id
        self.target_channels = []
        self.enable_customization = enable_customization
        self.custom_prompt = custom_prompt
        # Set up OpenAI
        openai.api_key = OPENAI_API_KEY
    
    async def process_message_with_gpt(self, message_content, author_name):
        """Process message with ChatGPT if customization is enabled"""
        if not self.enable_customization:
            return f"**{author_name}**: {message_content}"
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.custom_prompt},
                    {"role": "user", "content": f"Discord message from {author_name}: {message_content}"}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            processed_message = response.choices[0].message.content
            return f"**{author_name}** (processed): {processed_message}"
        except Exception as e:
            print(f"Error processing message with GPT: {e}")
            # Fallback to original message if GPT fails
            return f"**{author_name}**: {message_content}"
        
    async def on_ready(self):
        print(f'Discord bot logged in as {self.user}')
        # Extract channel IDs from URLs and join channels
        for channel_url in self.channel_urls:
            try:
                if '/channels/' in channel_url:
                    parts = channel_url.split('/channels/')[-1].split('/')
                    guild_id = int(parts[0])
                    channel_id = int(parts[1])
                    
                    guild = self.get_guild(guild_id)
                    if guild:
                        channel = guild.get_channel(channel_id)
                        if channel:
                            self.target_channels.append(channel)
                            print(f'Successfully found channel: {channel.name} in {guild.name}')
                        else:
                            print(f'Channel not found for URL: {channel_url}')
                    else:
                        print(f'Guild not found for URL: {channel_url}')
            except Exception as e:
                print(f'Error parsing channel URL {channel_url}: {e}')
        
        print(f'Monitoring {len(self.target_channels)} channels')
    
    async def on_message(self, message):
        print(f"Message received: {message.author.display_name} in {message.channel.name}")
        
        # Skip messages from the bot itself
        if message.author == self.user:
            print("Skipping bot's own message")
            return
            
        # Check if message is from any of the target channels
        is_target_channel = any(channel.id == message.channel.id for channel in self.target_channels)
        
        if is_target_channel:
            print(f"Processing message in target channel: {message.channel.name}")
            try:
                # Get message content
                message_text = message.content if message.content else "[Message content not available - enable Message Content Intent in Discord Portal]"
                
                print(f"Message content: '{message_text}'")
                
                # Process message with ChatGPT if customization is enabled
                if self.enable_customization and message_text:
                    content = await self.process_message_with_gpt(message_text, message.author.display_name)
                else:
                    # Format message content normally
                    content = f"**{message.author.display_name}**: {message_text}"
                
                # Send to Telegram with retry logic
                print(f"Sending to Telegram: {content}")
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await self.telegram_bot.send_message(
                            chat_id=self.telegram_chat_id,
                            text=content
                        )
                        print(f'Successfully forwarded message to Telegram!')
                        break
                    except Exception as telegram_error:
                        print(f"Telegram send attempt {attempt + 1} failed: {telegram_error}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2)  # Wait 2 seconds before retry
                        else:
                            raise telegram_error
                
            except Exception as e:
                print(f'Error forwarding message to Telegram: {e}')
                import traceback
                traceback.print_exc()
        else:
            print(f"Message not in target channels. Channel: {message.channel.name}")

def run_discord_bot():
    """Run Discord bot in a separate thread"""
    global discord_client
    
    async def start_bot():
        try:
            # Initialize Telegram bot with better timeout settings
            from telegram.request import HTTPXRequest
            request = HTTPXRequest(
                connection_pool_size=1,
                connect_timeout=30.0,
                read_timeout=30.0,
                write_timeout=30.0,
                pool_timeout=30.0
            )
            telegram_bot = Bot(token=bot_settings['telegram_bot_token'], request=request)
            
            # Initialize Discord bot
            discord_client = DiscordBot(
                bot_settings['discord_channel_urls'],
                telegram_bot,
                bot_settings['telegram_chat_id'],
                bot_settings.get('enable_customization', False),
                bot_settings.get('custom_prompt', '')
            )
            
            # Start Discord bot with the bot token (not OAuth token)
            await discord_client.start(bot_settings['discord_bot_token'])
            
        except Exception as e:
            print(f'Error running Discord bot: {e}')
            bot_settings['is_running'] = False
    
    # Run the async function
    asyncio.run(start_bot())

@app.route('/')
def index():
    discord_user = session.get('discord_user')
    return render_template('index.html', discord_user=discord_user)

@app.route('/discord/login')
def discord_login():
    """Initiate Discord OAuth2 login"""
    print("\n" + "="*50)
    print("DISCORD LOGIN INITIATED")
    print("="*50)
    print(f"Client ID: {DISCORD_CLIENT_ID}")
    print(f"Redirect URI: {DISCORD_REDIRECT_URI}")
    print(f"Authorization Base URL: {DISCORD_AUTHORIZATION_BASE_URL}")
    
    discord = OAuth2Session(
        DISCORD_CLIENT_ID,
        redirect_uri=DISCORD_REDIRECT_URI,
        scope=['identify', 'guilds']
    )
    authorization_url, state = discord.authorization_url(DISCORD_AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    
    # Debug: Check if URL has encoding issues
    print(f"OAuth authorization URL: {authorization_url}")
    print(f"OAuth state: {state}")
    
    # Fix any URL encoding issues
    if "+++" in authorization_url:
        print("WARNING: Found +++ in authorization URL, fixing...")
        authorization_url = authorization_url.replace("+++", "")
    print("="*50 + "\n")
    return redirect(authorization_url)

@app.route('/discord/callback')
def discord_callback():
    """Handle Discord OAuth2 callback"""
    try:
        print("\n" + "="*50)
        print("DISCORD OAUTH CALLBACK DEBUG")
        print("="*50)
        print(f"OAuth callback received. Request URL: {request.url}")
        print(f"Session oauth_state: {session.get('oauth_state')}")
        print(f"Request args: {request.args}")
        print(f"DISCORD_CLIENT_ID: {DISCORD_CLIENT_ID}")
        print(f"DISCORD_CLIENT_SECRET: {DISCORD_CLIENT_SECRET[:10]}..." if DISCORD_CLIENT_SECRET else "DISCORD_CLIENT_SECRET: None")
        print(f"DISCORD_REDIRECT_URI: {DISCORD_REDIRECT_URI}")
        print("="*50)
        
        # Check for error in callback
        if 'error' in request.args:
            error = request.args.get('error')
            error_description = request.args.get('error_description', 'Unknown error')
            print(f"OAuth error: {error} - {error_description}")
            return redirect(url_for('index', error=f'discord_oauth_error_{error}'))
        
        # Check for authorization code
        if 'code' not in request.args:
            print("No authorization code received")
            return redirect(url_for('index', error='no_auth_code'))
        
        # Disable state check for now to avoid session issues
        discord = OAuth2Session(
            DISCORD_CLIENT_ID,
            redirect_uri=DISCORD_REDIRECT_URI
        )
        
        print("\n--- TOKEN EXCHANGE DEBUG ---")
        print(f"Token URL: {DISCORD_TOKEN_URL}")
        print(f"Client ID: {DISCORD_CLIENT_ID}")
        print(f"Client Secret exists: {bool(DISCORD_CLIENT_SECRET)}")
        print(f"Authorization Response URL: {request.url}")
        print(f"Redirect URI being sent: {DISCORD_REDIRECT_URI}")
        print("Attempting to fetch token...")
        
        try:
            token = discord.fetch_token(
                DISCORD_TOKEN_URL,
                client_secret=DISCORD_CLIENT_SECRET,
                authorization_response=request.url,
                include_client_id=True
            )
            print(f"Token received successfully!")
            print(f"Access token: {token.get('access_token', 'No access token')[:20]}...")
        except Exception as token_error:
            print(f"TOKEN EXCHANGE ERROR: {token_error}")
            print(f"Error type: {type(token_error).__name__}")
            raise token_error
        
        # Store the access token
        session['discord_token'] = token['access_token']
        bot_settings['discord_token'] = token['access_token']
        
        # Get user information
        print("Fetching user information...")
        user_response = discord.get(DISCORD_API_BASE_URL + '/users/@me')
        print(f"User response status: {user_response.status_code}")
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"User data: {user_data}")
            session['discord_user'] = {
                'id': user_data['id'],
                'username': user_data['username'],
                'discriminator': user_data.get('discriminator', '0'),
                'avatar': user_data.get('avatar')
            }
            bot_settings['discord_user'] = session['discord_user']
            print("OAuth login successful!")
        else:
            print(f"Failed to get user info: {user_response.text}")
            return redirect(url_for('index', error='failed_user_info'))
        
        return redirect(url_for('index', success='discord_login'))
        
    except Exception as e:
        print(f'OAuth callback error: {e}')
        print(f'Error type: {type(e).__name__}')
        import traceback
        print(f'Traceback: {traceback.format_exc()}')
        return redirect(url_for('index', error='discord_login_failed'))

@app.route('/discord/logout')
def discord_logout():
    """Logout from Discord"""
    session.pop('discord_token', None)
    session.pop('discord_user', None)
    session.pop('oauth_state', None)
    bot_settings['discord_token'] = ''
    bot_settings['discord_user'] = None
    
    # Stop bot if running
    if discord_client and not discord_client.is_closed():
        try:
            asyncio.create_task(discord_client.close())
            bot_settings['is_running'] = False
        except:
            pass
    
    return redirect(url_for('index'))

@app.route('/start_bot', methods=['POST'])
def start_bot():
    global discord_client
    
    try:
        data = request.get_json()
        
        # Check if user is logged in to Discord
        if not session.get('discord_token'):
            return jsonify({'success': False, 'message': 'Please login to Discord first'})
        
        # Store bot settings (Discord OAuth token already stored in session)
        bot_settings['discord_channel_urls'] = data.get('discord_channel_urls', [])
        bot_settings['enable_customization'] = data.get('enable_customization', False)
        bot_settings['custom_prompt'] = data.get('custom_prompt', '')
        # Discord bot token and Telegram settings are now auto-configured
        
        # Validate required fields
        if not bot_settings['discord_channel_urls'] or len(bot_settings['discord_channel_urls']) == 0:
            return jsonify({'success': False, 'message': 'At least one Discord channel URL is required'})
        
        # Stop existing bot if running
        if discord_client and not discord_client.is_closed():
            asyncio.create_task(discord_client.close())
        
        # Start bot in a separate thread
        bot_settings['is_running'] = True
        bot_thread = threading.Thread(target=run_discord_bot, daemon=True)
        bot_thread.start()
        
        return jsonify({'success': True, 'message': 'Bot started successfully!'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting bot: {str(e)}'})

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    global discord_client
    
    try:
        if discord_client and not discord_client.is_closed():
            # Stop the Discord bot
            asyncio.create_task(discord_client.close())
            bot_settings['is_running'] = False
            return jsonify({'success': True, 'message': 'Bot stopped successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Bot is not running'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping bot: {str(e)}'})

@app.route('/status')
def status():
    return jsonify({
        'is_running': bot_settings['is_running'],
        'has_discord_token': bool(session.get('discord_token')),
        'has_telegram_token': bool(bot_settings['telegram_bot_token']),
        'discord_user': session.get('discord_user')
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
