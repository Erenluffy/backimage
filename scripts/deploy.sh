#!/bin/bash

# ImageLab Studio Production Deployment Script
set -e

# Configuration
APP_NAME="imagelab"
APP_DIR="/var/www/$APP_NAME-backend"
BACKUP_DIR="/var/backups/$APP_NAME"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="$APP_DIR/logs"
GIT_REPO="https://github.com/yourusername/imagelab-backend.git"
BRANCH="main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root"
fi

# Create backup
create_backup() {
    log "Creating backup..."
    mkdir -p $BACKUP_DIR
    BACKUP_FILE="$BACKUP_DIR/$APP_NAME-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf $BACKUP_FILE -C $(dirname $APP_DIR) $(basename $APP_DIR) 2>/dev/null || warning "Backup failed, continuing..."
    log "Backup created: $BACKUP_FILE"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    apt-get update
    apt-get install -y \
        python3-pip \
        python3-dev \
        python3-venv \
        nginx \
        redis-server \
        postgresql \
        postgresql-contrib \
        imagemagick \
        libmagic-dev \
        libmagickwand-dev \
        supervisor \
        git \
        curl \
        wget \
        htop \
        fail2ban \
        ufw
}

# Setup Python virtual environment
setup_venv() {
    log "Setting up Python virtual environment..."
    cd $APP_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn gevent
}

# Configure firewall
setup_firewall() {
    log "Configuring firewall..."
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow http
    ufw allow https
    echo "y" | ufw enable
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    log "Setting up SSL certificate..."
    apt-get install -y certbot python3-certbot-nginx
    certbot --nginx -d imagelab.studio -d www.imagelab.studio --non-interactive --agree-tos --email admin@imagelab.studio
}

# Setup database
setup_database() {
    log "Setting up PostgreSQL database..."
    sudo -u postgres psql <<EOF
    CREATE DATABASE imagelab;
    CREATE USER imagelab_user WITH PASSWORD '$(openssl rand -base64 32)';
    GRANT ALL PRIVILEGES ON DATABASE imagelab TO imagelab_user;
    ALTER USER imagelab_user WITH SUPERUSER;
EOF
    log "Database setup complete. Save this password!"
}

# Configure Redis
setup_redis() {
    log "Configuring Redis..."
    cat >> /etc/redis/redis.conf <<EOF
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF
    systemctl restart redis-server
}

# Setup log rotation
setup_logrotate() {
    log "Setting up log rotation..."
    cat > /etc/logrotate.d/imagelab <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload imagelab >/dev/null 2>&1 || true
    endscript
}
EOF
}

# Configure ImageMagick security
setup_imagemagick() {
    log "Configuring ImageMagick security..."
    cp $APP_DIR/config/imagick-policy.xml /etc/ImageMagick-6/policy.xml
}

# Setup systemd services
setup_services() {
    log "Setting up systemd services..."
    cp $APP_DIR/config/imagelab.service /etc/systemd/system/
    cp $APP_DIR/config/supervisor.conf /etc/supervisor/conf.d/imagelab.conf
    
    systemctl daemon-reload
    systemctl enable imagelab
    systemctl enable supervisor
    systemctl enable redis-server
    systemctl enable nginx
}

# Configure environment
setup_environment() {
    log "Configuring environment..."
    if [ ! -f "$APP_DIR/.env" ]; then
        cp $APP_DIR/.env.example $APP_DIR/.env
        # Generate secure keys
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$(openssl rand -base64 32)/" $APP_DIR/.env
        sed -i "s/FLASK_ENV=.*/FLASK_ENV=production/" $APP_DIR/.env
        sed -i "s/FLASK_DEBUG=.*/FLASK_DEBUG=False/" $APP_DIR/.env
    fi
}

# Start services
start_services() {
    log "Starting services..."
    systemctl restart redis-server
    systemctl restart postgresql
    systemctl start imagelab
    systemctl start supervisor
    systemctl restart nginx
    
    # Check status
    systemctl status imagelab --no-pager
}

# Monitor deployment
monitor_deployment() {
    log "Monitoring deployment..."
    sleep 5
    
    # Check if app is responding
    if curl -s http://localhost:5000/api/health > /dev/null; then
        log "✓ Application is responding"
    else
        error "Application failed to start"
    fi
    
    # Check nginx
    if systemctl is-active --quiet nginx; then
        log "✓ Nginx is running"
    else
        error "Nginx failed to start"
    fi
    
    # Check Redis
    if systemctl is-active --quiet redis-server; then
        log "✓ Redis is running"
    else
        warning "Redis is not running"
    fi
    
    # Check database
    if systemctl is-active --quiet postgresql; then
        log "✓ PostgreSQL is running"
    else
        warning "PostgreSQL is not running"
    fi
}

# Main deployment function
deploy() {
    log "Starting deployment of $APP_NAME..."
    
    # Create backup if app exists
    if [ -d "$APP_DIR" ]; then
        create_backup
    fi
    
    # Clone/update repository
    if [ ! -d "$APP_DIR" ]; then
        log "Cloning repository..."
        git clone -b $BRANCH $GIT_REPO $APP_DIR
    else
        log "Updating repository..."
        cd $APP_DIR
        git fetch origin
        git reset --hard origin/$BRANCH
    fi
    
    # Create necessary directories
    mkdir -p $LOG_DIR $APP_DIR/static/uploads
    chown -R www-data:www-data $LOG_DIR $APP_DIR/static
    
    # Setup everything
    install_dependencies
    setup_environment
    setup_venv
    setup_database
    setup_redis
    setup_imagemagick
    setup_logrotate
    setup_firewall
    setup_services
    setup_ssl
    
    # Start services
    start_services
    monitor_deployment
    
    log "${GREEN}✓ Deployment completed successfully!${NC}"
    log "You can access the application at https://imagelab.studio"
}

# Rollback function
rollback() {
    log "Rolling back to previous version..."
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/*.tar.gz | head -1)
    
    if [ -f "$LATEST_BACKUP" ]; then
        # Stop services
        systemctl stop imagelab
        
        # Restore backup
        rm -rf $APP_DIR
        tar -xzf $LATEST_BACKUP -C $(dirname $APP_DIR)
        
        # Restart services
        systemctl start imagelab
        log "Rollback completed"
    else
        error "No backup found"
    fi
}

# Command line argument handling
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    backup)
        create_backup
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|backup}"
        exit 1
        ;;
esac
