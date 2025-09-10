#!/bin/bash

# AWS EC2 Deployment Script for Discord Bot
# This script updates the application on your AWS EC2 instance

set -e  # Exit on any error

# Configuration
EC2_USER="ubuntu"  # Change this to your EC2 username (ubuntu, ec2-user, etc.)
EC2_HOST="13.60.40.184"  # Your EC2 public IP
EC2_KEY_PATH="~/.ssh/your-key.pem"  # Path to your EC2 key file
APP_DIR="/home/ubuntu/discord-bot"  # Directory on EC2 where app is deployed
SERVICE_NAME="discord-bot"  # Systemd service name

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AWS EC2 deployment...${NC}"

# Check if SSH key exists
if [ ! -f "${EC2_KEY_PATH/#\~/$HOME}" ]; then
    echo -e "${RED}❌ SSH key not found at ${EC2_KEY_PATH}${NC}"
    echo "Please update EC2_KEY_PATH in this script with your actual key path"
    exit 1
fi

# Function to run commands on EC2
run_on_ec2() {
    ssh -i "${EC2_KEY_PATH/#\~/$HOME}" -o StrictHostKeyChecking=no "${EC2_USER}@${EC2_HOST}" "$@"
}

# Function to copy files to EC2
copy_to_ec2() {
    scp -i "${EC2_KEY_PATH/#\~/$HOME}" -o StrictHostKeyChecking=no "$1" "${EC2_USER}@${EC2_HOST}:$2"
}

echo -e "${YELLOW}📦 Stopping Discord Bot service...${NC}"
run_on_ec2 "sudo systemctl stop ${SERVICE_NAME} || true"

echo -e "${YELLOW}📁 Creating backup of current deployment...${NC}"
run_on_ec2 "sudo cp -r ${APP_DIR} ${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S) || true"

echo -e "${YELLOW}📤 Uploading application files...${NC}"

# Upload main application files
copy_to_ec2 "app.py" "${APP_DIR}/"
copy_to_ec2 "config.py" "${APP_DIR}/"
copy_to_ec2 "requirements.txt" "${APP_DIR}/"
copy_to_ec2 "templates/index.html" "${APP_DIR}/templates/"

# Upload configuration files
copy_to_ec2 "discord-bot.service" "${APP_DIR}/"
copy_to_ec2 "discord-bot-nginx.conf" "${APP_DIR}/"

echo -e "${YELLOW}🔧 Setting up application on EC2...${NC}"

# Run setup commands on EC2
run_on_ec2 "
    cd ${APP_DIR} &&
    
    # Install/update Python dependencies
    echo 'Installing Python dependencies...' &&
    pip3 install -r requirements.txt &&
    
    # Set proper permissions
    chmod +x app.py &&
    
    # Update systemd service
    echo 'Updating systemd service...' &&
    sudo cp discord-bot.service /etc/systemd/system/ &&
    sudo systemctl daemon-reload &&
    
    # Update nginx configuration
    echo 'Updating nginx configuration...' &&
    sudo cp discord-bot-nginx.conf /etc/nginx/sites-available/discord-bot &&
    sudo ln -sf /etc/nginx/sites-available/discord-bot /etc/nginx/sites-enabled/ &&
    sudo nginx -t &&
    
    # Restart services
    echo 'Restarting services...' &&
    sudo systemctl restart nginx &&
    sudo systemctl start ${SERVICE_NAME} &&
    sudo systemctl enable ${SERVICE_NAME} &&
    
    # Check service status
    echo 'Checking service status...' &&
    sudo systemctl status ${SERVICE_NAME} --no-pager -l
"

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your application should be available at: https://${EC2_HOST}${NC}"

# Show logs
echo -e "${YELLOW}📋 Recent application logs:${NC}"
run_on_ec2 "sudo journalctl -u ${SERVICE_NAME} --no-pager -l -n 20"
