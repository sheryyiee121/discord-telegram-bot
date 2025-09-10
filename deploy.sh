#!/bin/bash

# Discord Bot Deployment Script for AWS EC2
# This script sets up the environment and deploys the Discord to Telegram bot

set -e  # Exit on any error

echo "🚀 Starting Discord Bot deployment on AWS EC2..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and pip
echo "🐍 Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip python3.11-dev

# Install nginx
echo "🌐 Installing Nginx..."
sudo apt install -y nginx

# Install certbot for SSL certificates
echo "🔒 Installing Certbot for SSL..."
sudo apt install -y certbot python3-certbot-nginx

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/discord-bot
sudo chown -R $USER:$USER /opt/discord-bot
cd /opt/discord-bot

# Copy application files
echo "📋 Copying application files..."
# Note: You'll need to upload your files to the server first
# This assumes files are in the home directory
cp ~/app.py .
cp ~/config.py .
cp ~/requirements.txt .
cp -r ~/templates .
cp ~/discord-bot.service /tmp/

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file from template
echo "⚙️  Creating environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "❗ Please edit .env file with your actual tokens and configuration"
fi

# Set up systemd service
echo "🔧 Setting up systemd service..."
sudo cp /tmp/discord-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable discord-bot

# Set up nginx configuration
echo "🌐 Configuring Nginx..."
sudo cp /tmp/discord-bot-nginx.conf /etc/nginx/sites-available/discord-bot
sudo ln -sf /etc/nginx/sites-available/discord-bot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Create log directory
sudo mkdir -p /var/log/discord-bot
sudo chown -R $USER:$USER /var/log/discord-bot

# Set proper permissions
chmod +x app.py
sudo chown -R $USER:$USER /opt/discord-bot

echo "✅ Basic setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit /opt/discord-bot/.env with your actual tokens"
echo "2. Update Discord OAuth redirect URI to your domain"
echo "3. Configure your domain in nginx config"
echo "4. Run: sudo systemctl start discord-bot"
echo "5. Run: sudo systemctl restart nginx"
echo "6. Set up SSL with: sudo certbot --nginx -d yourdomain.com"
echo ""
echo "🔍 Check status with:"
echo "   sudo systemctl status discord-bot"
echo "   sudo journalctl -u discord-bot -f"
