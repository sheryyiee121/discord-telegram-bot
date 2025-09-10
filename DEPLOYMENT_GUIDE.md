# Discord Bot Deployment Guide

This guide covers deploying your Discord bot to AWS EC2 and setting up automated deployments via GitHub.

## Prerequisites

- AWS EC2 instance running Ubuntu
- SSH access to your EC2 instance
- GitHub repository
- Domain name (optional, for HTTPS)

## Manual Deployment

### 1. Initial Setup on EC2

First, set up your EC2 instance:

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@13.60.40.184

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3 python3-pip nginx git -y

# Create application directory
sudo mkdir -p /home/ubuntu/discord-bot
sudo chown ubuntu:ubuntu /home/ubuntu/discord-bot
cd /home/ubuntu/discord-bot

# Clone your repository
git clone https://github.com/yourusername/your-repo.git .

# Install Python dependencies
pip3 install -r requirements.txt

# Create production environment file
sudo nano production.env
# Copy your production.env content here
```

### 2. Configure Systemd Service

Copy the `discord-bot.service` file to systemd:

```bash
sudo cp discord-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable discord-bot
```

### 3. Configure Nginx

```bash
# Copy nginx configuration
sudo cp discord-bot-nginx.conf /etc/nginx/sites-available/discord-bot
sudo ln -s /etc/nginx/sites-available/discord-bot /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Start services
sudo systemctl start discord-bot
sudo systemctl restart nginx
```

## Automated Deployment

### Option 1: Using the Deploy Script

1. **Update the deploy script** (`deploy-aws.sh`):
   - Change `EC2_HOST` to your EC2 IP
   - Change `EC2_KEY_PATH` to your SSH key path
   - Update `EC2_USER` if needed

2. **Make the script executable**:
   ```bash
   chmod +x deploy-aws.sh
   ```

3. **Run the deployment**:
   ```bash
   ./deploy-aws.sh
   ```

### Option 2: Using GitHub Actions

1. **Set up GitHub Secrets**:
   - Go to your GitHub repository
   - Navigate to Settings → Secrets and variables → Actions
   - Add these secrets:
     - `EC2_HOST`: Your EC2 public IP (e.g., `13.60.40.184`)
     - `EC2_USER`: Your EC2 username (e.g., `ubuntu`)
     - `EC2_SSH_KEY`: Your private SSH key content

2. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial deployment setup"
   git push origin main
   ```

3. **GitHub Actions will automatically deploy** when you push to the main branch.

## Updating Your Application

### Manual Update

1. **Make changes locally**
2. **Commit and push to GitHub**:
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

3. **SSH into your EC2 and pull changes**:
   ```bash
   ssh -i your-key.pem ubuntu@13.60.40.184
   cd /home/ubuntu/discord-bot
   git pull origin main
   sudo systemctl restart discord-bot
   ```

### Automatic Update (with GitHub Actions)

Just push your changes to the main branch - GitHub Actions will handle the deployment automatically!

## Environment Configuration

### Production Environment File

Create `production.env` on your EC2 instance:

```env
# Discord OAuth2 Configuration
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=https://your-domain.com/discord/callback

# Flask Security
SECRET_KEY=your_secret_key

# Other settings
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Discord Bot Token
DISCORD_BOT_TOKEN=your_bot_token

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id

# Security Settings
OAUTHLIB_INSECURE_TRANSPORT=0
```

## SSL/HTTPS Setup (Recommended)

For production, you should set up HTTPS:

1. **Install Certbot**:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```

2. **Get SSL certificate**:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **Update your Discord OAuth redirect URI** to use HTTPS.

## Monitoring and Logs

### Check Application Status

```bash
# Check service status
sudo systemctl status discord-bot

# View logs
sudo journalctl -u discord-bot -f

# Check nginx status
sudo systemctl status nginx
```

### Application Logs

```bash
# View application logs
tail -f /var/log/discord-bot/app.log

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Common Issues

1. **Service won't start**:
   - Check logs: `sudo journalctl -u discord-bot -f`
   - Verify environment variables are set
   - Check file permissions

2. **Nginx errors**:
   - Test configuration: `sudo nginx -t`
   - Check error logs: `sudo tail -f /var/log/nginx/error.log`

3. **Discord OAuth errors**:
   - Verify redirect URI matches exactly
   - Check if using HTTPS in production
   - Verify client ID and secret

4. **Permission errors**:
   - Check file ownership: `ls -la /home/ubuntu/discord-bot`
   - Fix permissions: `sudo chown -R ubuntu:ubuntu /home/ubuntu/discord-bot`

### Rollback

If something goes wrong, you can rollback:

```bash
# Stop current service
sudo systemctl stop discord-bot

# Restore from backup
sudo cp -r /home/ubuntu/discord-bot.backup.YYYYMMDD_HHMMSS/* /home/ubuntu/discord-bot/

# Restart service
sudo systemctl start discord-bot
```

## Security Considerations

1. **Never commit sensitive data** to Git (use .gitignore)
2. **Use environment variables** for secrets
3. **Set up firewall rules** on EC2
4. **Use HTTPS** in production
5. **Regular security updates**: `sudo apt update && sudo apt upgrade`

## Support

If you encounter issues:

1. Check the logs first
2. Verify all environment variables are set correctly
3. Ensure all services are running
4. Check Discord Developer Portal settings
5. Verify nginx configuration

For additional help, check the application logs and system logs for specific error messages.
