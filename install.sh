#!/bin/bash

# Update system
sudo apt-get update

# Install system dependencies
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    imagemagick \
    libmagic-dev \
    libmagickwand-dev \
    redis-server \
    nginx

# Install Python packages
pip3 install -r requirements.txt

# Install additional ImageMagick policies (for security)
sudo cp config/imagick-policy.xml /etc/ImageMagick-6/policy.xml

# Create necessary directories
mkdir -p static/uploads
mkdir -p logs

# Set permissions
chmod -R 755 static/uploads
chmod -R 755 logs

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Setup environment
cp .env.example .env
echo "Please update .env with your configuration"

echo "Installation complete!"
