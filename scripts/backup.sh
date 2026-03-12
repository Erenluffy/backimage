#!/bin/bash

# Automated backup script for ImageLab Studio

BACKUP_DIR="/var/backups/imagelab"
APP_DIR="/var/www/imagelab-backend"
DB_NAME="imagelab"
DB_USER="imagelab_user"
DATE=$(date +%Y%m%d-%H%M%S)
RETENTION_DAYS=7

# Create backup directory
mkdir -p $BACKUP_DIR/{database,files,config}

# Backup database
echo "Backing up database..."
PGPASSWORD=$(grep DB_PASSWORD $APP_DIR/.env | cut -d'=' -f2) pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/database/db_$DATE.sql
gzip $BACKUP_DIR/database/db_$DATE.sql

# Backup application files
echo "Backing up application files..."
tar -czf $BACKUP_DIR/files/app_$DATE.tar.gz \
    --exclude="$APP_DIR/venv" \
    --exclude="$APP_DIR/__pycache__" \
    --exclude="$APP_DIR/static/uploads" \
    $APP_DIR/

# Backup uploads (if needed)
echo "Backing up uploads..."
tar -czf $BACKUP_DIR/files/uploads_$DATE.tar.gz $APP_DIR/static/uploads/

# Backup configuration
echo "Backing up configuration..."
cp $APP_DIR/.env $BACKUP_DIR/config/env_$DATE
cp /etc/nginx/sites-available/imagelab $BACKUP_DIR/config/nginx_$DATE
cp /etc/systemd/system/imagelab.service $BACKUP_DIR/config/service_$DATE

# Remove old backups
echo "Removing backups older than $RETENTION_DAYS days..."
find $BACKUP_DIR/database -name "*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR/files -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR/config -name "env_*" -mtime +$RETENTION_DAYS -delete

# Upload to cloud storage (optional)
# aws s3 sync $BACKUP_DIR s3://your-bucket/backups/

echo "Backup completed: $DATE"
