# Discord to Telegram Bot

A Python Flask web application that forwards messages from Discord channels to Telegram groups.

## Features

- Web-based interface for easy configuration
- Real-time message forwarding from Discord to Telegram
- User-friendly dashboard to start/stop the bot
- Secure token handling

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Discord OAuth Application

#### Create Discord Application
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Give it a name (e.g., "Discord to Telegram Bot")
4. Go to "OAuth2" section
5. Copy the "Client ID" and "Client Secret"
6. Add redirect URL: `http://localhost:5000/discord/callback`
7. In "OAuth2 URL Generator", select scopes: `identify` and `guilds`

#### Telegram Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow the instructions to create a new bot
4. Copy the bot token provided

#### Telegram Chat ID
1. Add your bot to the target group/channel
2. Send a message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for the chat ID in the response

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Discord OAuth2 Application Settings
DISCORD_CLIENT_ID=your_discord_client_id_here
DISCORD_CLIENT_SECRET=your_discord_client_secret_here

# Flask Settings (optional)
SECRET_KEY=your-super-secret-key-here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
```

### 4. Run the Application

```bash
python app.py
```

The web interface will be available at `http://localhost:5000`

## How to Use

1. Open the web interface at `http://localhost:5000`
2. Click "Login with Discord" to authenticate with your Discord account
3. After login, enter the Discord channel URL you want to monitor
4. Enter your Telegram bot token
5. Enter the Telegram chat ID where messages should be forwarded
6. Click "Start Bot"

The bot will automatically:
- Use your authenticated Discord session
- Join the specified channel
- Monitor for new messages
- Forward all messages to your Telegram group

## Important Notes

✅ **Safe & Legitimate**: Uses Discord OAuth2 for authentication - no need to extract tokens manually!
📱 **User-Friendly**: Simple web interface with Discord login button
🔒 **Secure**: Sessions are managed securely, tokens are not exposed

- Keep your tokens secure and never share them
- The bot will forward ALL messages from the monitored channel
- Make sure your Telegram bot has permission to send messages in the target chat

## Troubleshooting

- **Bot not starting**: Check that all tokens are correct
- **Messages not forwarding**: Ensure the bot has access to both Discord channel and Telegram chat
- **Connection issues**: Check your internet connection and token validity

## Security

- Tokens are only stored in memory while the bot is running
- Use the web interface on a secure, private network
- Consider using environment variables for production deployment
