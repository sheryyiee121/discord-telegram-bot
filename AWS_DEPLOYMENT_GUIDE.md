# Discord to Telegram Bot - AWS EC2 Deployment Guide

This guide will help you deploy your Discord to Telegram bot on AWS EC2 with a production-ready setup including SSL, reverse proxy, and process management.

## 🚀 Quick Start

If you're in a hurry, follow these condensed steps:

1. Launch an EC2 instance (Ubuntu 22.04 LTS)
2. Upload your files to the server
3. Run the deployment script: `bash deploy.sh`
4. Configure your environment variables
5. Start the services

## 📋 Prerequisites

- AWS account with EC2 access
- Domain name (recommended for SSL)
- Discord application with bot token
- Telegram bot token

## 🖥️ Step 1: Launch EC2 Instance

### Instance Configuration
- **AMI**: Ubuntu Server 22.04 LTS
- **Instance Type**: t3.micro (free tier) or t3.small for better performance
- **Storage**: 20 GB gp3 (minimum)
- **Security Group**: Configure ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

### Security Group Rules
```
Type        Protocol    Port Range    Source
SSH         TCP         22           Your IP/0.0.0.0/0
HTTP        TCP         80           0.0.0.0/0
HTTPS       TCP         443          0.0.0.0/0
```

### Key Pair
- Create or use existing key pair
- Download the .pem file and keep it secure

## 🔐 Step 2: Connect to Your Instance

```bash
# Make key file secure
chmod 400 your-key.pem

# Connect to instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## 📁 Step 3: Upload Your Application Files

### Option A: Using SCP
```bash
# From your local machine
scp -i your-key.pem -r . ubuntu@your-ec2-public-ip:~/
```

### Option B: Using Git
```bash
# On EC2 instance
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### Option C: Manual Upload
Upload these files to your home directory on EC2:
- `app.py`
- `config.py`
- `requirements.txt`
- `templates/` directory
- `deploy.sh`
- `discord-bot.service`
- `discord-bot-nginx.conf`
- `env.example`

## 🛠️ Step 4: Run Deployment Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
bash deploy.sh
```

The script will:
- Update system packages
- Install Python 3.11, nginx, certbot
- Set up application directory
- Create virtual environment
- Install dependencies
- Configure systemd service
- Set up nginx reverse proxy

## ⚙️ Step 5: Configure Environment Variables

```bash
# Navigate to application directory
cd /opt/discord-bot

# Copy environment template
cp env.example .env

# Edit environment file
nano .env
```

### Required Environment Variables

```env
# Discord OAuth2 (from Discord Developer Portal)
DISCORD_CLIENT_ID=1234567890123456789
DISCORD_CLIENT_SECRET=your_discord_client_secret

# Discord Bot Token (from Discord Developer Portal)
DISCORD_BOT_TOKEN=your_discord_bot_token

# Telegram Bot (from @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Flask Security
SECRET_KEY=sdjsadhksadksakdsad
FLASK_ENV=production
FLASK_DEBUG=False

# Domain Configuration
DISCORD_REDIRECT_URI=https://your-domain.com/discord/callback
```

### How to Get Tokens

#### Discord Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token for `DISCORD_BOT_TOKEN`
5. Go to "OAuth2" section
6. Copy Client ID and Client Secret
7. Add redirect URI: `https://your-domain.com/discord/callback`

#### Telegram Setup
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token
4. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

## 🌐 Step 6: Configure Domain and SSL

### Update Nginx Configuration
```bash
# Edit nginx config
sudo nano /etc/nginx/sites-available/discord-bot

# Replace 'your-domain.com' with your actual domain
# Save and exit
```

### Test Nginx Configuration
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Set Up SSL Certificate
```bash
# Install SSL certificate
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 🚀 Step 7: Start Your Application

```bash
# Start the Discord bot service
sudo systemctl start discord-bot

# Enable auto-start on boot
sudo systemctl enable discord-bot

# Restart nginx
sudo systemctl restart nginx
```

## 📊 Step 8: Verify Deployment

### Check Service Status
```bash
# Check bot status
sudo systemctl status discord-bot

# Check nginx status
sudo systemctl status nginx

# View bot logs
sudo journalctl -u discord-bot -f
```

### Test Your Application
1. Visit `https://your-domain.com`
2. Try Discord OAuth login
3. Configure a Discord channel URL
4. Start the bot and test message forwarding

## 🔧 Maintenance Commands

### Service Management
```bash
# Restart bot
sudo systemctl restart discord-bot

# Stop bot
sudo systemctl stop discord-bot

# View logs
sudo journalctl -u discord-bot -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Updates
```bash
# Update application code
cd /opt/discord-bot
git pull origin main  # if using git

# Restart service
sudo systemctl restart discord-bot
```

## 🛡️ Security Best Practices

### 1. Firewall Configuration
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH, HTTP, HTTPS
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
```

### 2. Regular Updates
```bash
# Update system packages regularly
sudo apt update && sudo apt upgrade -y
```

### 3. Monitor Logs
```bash
# Set up log rotation
sudo nano /etc/logrotate.d/discord-bot
```

### 4. Backup Configuration
```bash
# Backup your .env file and any custom configs
cp /opt/discord-bot/.env ~/backup-env
```

## 🐛 Troubleshooting

### Common Issues

#### Bot Won't Start
```bash
# Check logs
sudo journalctl -u discord-bot -n 50

# Check Python environment
cd /opt/discord-bot
source venv/bin/activate
python app.py  # Test manually
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew
```

#### Nginx Issues
```bash
# Test nginx config
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R ubuntu:ubuntu /opt/discord-bot
chmod +x /opt/discord-bot/app.py
```

### Discord API Issues
- Ensure bot has proper permissions in Discord server
- Check if Message Content Intent is enabled if needed
- Verify OAuth2 redirect URI matches exactly

### Telegram API Issues
- Verify bot token is correct
- Ensure chat ID is correct (can be negative for groups)
- Check if bot is added to the target chat

## 📈 Performance Optimization

### 1. Gunicorn Configuration
Edit `/etc/systemd/system/discord-bot.service`:
```ini
# Adjust workers based on CPU cores
ExecStart=/opt/discord-bot/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
```

### 2. Nginx Optimization
```bash
# Edit nginx main config
sudo nano /etc/nginx/nginx.conf

# Adjust worker processes and connections
worker_processes auto;
worker_connections 1024;
```

### 3. System Resources
```bash
# Monitor resource usage
htop
df -h
free -h
```

## 📊 Monitoring

### Set Up Basic Monitoring
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Monitor in real-time
htop  # CPU/Memory usage
sudo iotop  # Disk I/O
sudo nethogs  # Network usage
```

### Log Monitoring
```bash
# Monitor all logs
sudo tail -f /var/log/syslog

# Monitor application logs
sudo journalctl -u discord-bot -f
```

## 🔄 Backup and Recovery

### Backup Strategy
```bash
# Create backup script
nano ~/backup.sh
```

```bash
#!/bin/bash
# Backup important files
tar -czf ~/discord-bot-backup-$(date +%Y%m%d).tar.gz \
    /opt/discord-bot/.env \
    /opt/discord-bot/app.py \
    /opt/discord-bot/config.py \
    /etc/nginx/sites-available/discord-bot \
    /etc/systemd/system/discord-bot.service
```

### Recovery
```bash
# Restore from backup
tar -xzf discord-bot-backup-YYYYMMDD.tar.gz -C /
sudo systemctl daemon-reload
sudo systemctl restart discord-bot nginx
```

## 💰 Cost Optimization

### EC2 Instance Sizing
- **t3.micro**: Free tier, suitable for light usage
- **t3.small**: Better performance for moderate usage
- **t3.medium**: High usage or multiple bots

### Storage Optimization
```bash
# Clean up logs periodically
sudo journalctl --vacuum-time=7d

# Clean package cache
sudo apt autoclean
sudo apt autoremove
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review application logs: `sudo journalctl -u discord-bot -f`
3. Verify all environment variables are set correctly
4. Ensure Discord and Telegram tokens are valid
5. Check firewall and security group settings

## 🎉 Conclusion

Your Discord to Telegram bot should now be running on AWS EC2 with:
- ✅ Production-ready setup with Gunicorn
- ✅ Nginx reverse proxy
- ✅ SSL/HTTPS encryption
- ✅ Automatic startup on boot
- ✅ Process management with systemd
- ✅ Security best practices

Visit your domain to start using the bot!

---

**Note**: Remember to replace placeholder values (your-domain.com, tokens, etc.) with your actual values throughout the deployment process.
