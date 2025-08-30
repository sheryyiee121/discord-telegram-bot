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

# Allow HTTP for local development (OAuth2 normally requires HTTPS)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', '1411364572274888836')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET', 'jQEow0R8RgA1aHSFqDYODw6XZsRZN5Bb')
DISCORD_REDIRECT_URI = 'http://localhost:5000/discord/callback'
DISCORD_API_BASE_URL = 'https://discord.com/api'
DISCORD_AUTHORIZATION_BASE_URL = DISCORD_API_BASE_URL + '/oauth2/authorize'
DISCORD_TOKEN_URL = DISCORD_API_BASE_URL + '/oauth2/token'

# Global variables to store bot instances and settings
discord_client = None
telegram_bot = None
bot_settings = {
    'discord_token': '',
    'discord_channel_url': '',
    'telegram_bot_token': '',
    'telegram_chat_id': '',
    'is_running': False,
    'discord_user': None
}

class DiscordBot(discord.Client):
    def __init__(self, channel_url, telegram_bot, telegram_chat_id):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.channel_url = channel_url
        self.telegram_bot = telegram_bot
        self.telegram_chat_id = telegram_chat_id
        self.target_channel = None
        
    async def on_ready(self):
        print(f'Discord bot logged in as {self.user}')
        # Extract channel ID from URL and join channel
        try:
            if '/channels/' in self.channel_url:
                parts = self.channel_url.split('/channels/')[-1].split('/')
                guild_id = int(parts[0])
                channel_id = int(parts[1])
                
                guild = self.get_guild(guild_id)
                if guild:
                    self.target_channel = guild.get_channel(channel_id)
                    if self.target_channel:
                        print(f'Successfully found channel: {self.target_channel.name}')
                    else:
                        print('Channel not found')
                else:
                    print('Guild not found')
        except Exception as e:
            print(f'Error parsing channel URL: {e}')
    
    async def on_message(self, message):
        # Skip messages from the bot itself
        if message.author == self.user:
            return
            
        # Only process messages from the target channel
        if self.target_channel and message.channel.id == self.target_channel.id:
            try:
                # Format message content
                content = f"**{message.author.display_name}**: {message.content}"
                
                # Send to Telegram
                await self.telegram_bot.send_message(
                    chat_id=self.telegram_chat_id,
                    text=content
                )
                print(f'Forwarded message to Telegram: {content[:50]}...')
                
            except Exception as e:
                print(f'Error forwarding message to Telegram: {e}')

def run_discord_bot():
    """Run Discord bot in a separate thread"""
    global discord_client
    
    async def start_bot():
        try:
            # Initialize Telegram bot
            telegram_bot = Bot(token=bot_settings['telegram_bot_token'])
            
            # Initialize Discord bot
            discord_client = DiscordBot(
                bot_settings['discord_channel_url'],
                telegram_bot,
                bot_settings['telegram_chat_id']
            )
            
            # Start Discord bot
            await discord_client.start(bot_settings['discord_token'])
            
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
    discord = OAuth2Session(
        DISCORD_CLIENT_ID,
        redirect_uri=DISCORD_REDIRECT_URI,
        scope=['identify', 'guilds']
    )
    authorization_url, state = discord.authorization_url(DISCORD_AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/discord/callback')
def discord_callback():
    """Handle Discord OAuth2 callback"""
    try:
        print(f"OAuth callback received. Request URL: {request.url}")
        print(f"Session oauth_state: {session.get('oauth_state')}")
        print(f"Request args: {request.args}")
        
        discord = OAuth2Session(
            DISCORD_CLIENT_ID,
            state=session.get('oauth_state'),
            redirect_uri=DISCORD_REDIRECT_URI
        )
        
        print("Attempting to fetch token...")
        token = discord.fetch_token(
            DISCORD_TOKEN_URL,
            client_secret=DISCORD_CLIENT_SECRET,
            authorization_response=request.url
        )
        print(f"Token received: {token.get('access_token', 'No access token')}")
        
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
        
        return redirect(url_for('index'))
        
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
        
        # Store bot settings (Discord token already stored in session)
        bot_settings['discord_channel_url'] = data.get('discord_channel_url')
        bot_settings['telegram_bot_token'] = data.get('telegram_bot_token')
        bot_settings['telegram_chat_id'] = data.get('telegram_chat_id')
        
        # Validate required fields
        if not all([
            bot_settings['discord_channel_url'],
            bot_settings['telegram_bot_token'],
            bot_settings['telegram_chat_id']
        ]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
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
