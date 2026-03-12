#!/bin/bash

# Monitoring script for ImageLab Studio

APP_NAME="imagelab"
LOG_FILE="/var/log/imagelab-monitor.log"
ALERT_EMAIL="admin@imagelab.studio"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

check_service() {
    if systemctl is-active --quiet $1; then
        log "✓ $1 is running"
        return 0
    else
        log "✗ $1 is NOT running"
        return 1
    fi
}

check_disk_space() {
    USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $USAGE -gt 80 ]; then
        log "WARNING: Disk usage is at ${USAGE}%"
        return 1
    fi
    return 0
}

check_memory() {
    FREE_MEM=$(free | awk '/^Mem:/ {print $4/$2 * 100.0}')
    if (( $(echo "$FREE_MEM < 10" | bc -l) )); then
        log "WARNING: Low memory! Free: ${FREE_MEM}%"
        return 1
    fi
    return 0
}

check_api() {
    if curl -s -f http://localhost:5000/api/health > /dev/null; then
        log "✓ API is responding"
        return 0
    else
        log "✗ API is NOT responding"
        return 1
    fi
}

check_uploads_dir() {
    UPLOAD_DIR="/var/www/imagelab-backend/static/uploads"
    FILE_COUNT=$(find $UPLOAD_DIR -type f -mmin +60 | wc -l)
    if [ $FILE_COUNT -gt 100 ]; then
        log "WARNING: $FILE_COUNT old files in uploads directory"
        # Clean old files
        find $UPLOAD_DIR -type f -mmin +120 -delete
    fi
}

send_alert() {
    echo "$1" | mail -s "ImageLab Alert" $ALERT_EMAIL
}

# Main monitoring loop
while true; do
    log "Starting monitoring check..."
    
    ERRORS=0
    
    check_service "imagelab" || ((ERRORS++))
    check_service "nginx" || ((ERRORS++))
    check_service "redis-server" || ((ERRORS++))
    check_service "postgresql" || ((ERRORS++))
    check_service "supervisor" || ((ERRORS++))
    
    check_disk_space || ((ERRORS++))
    check_memory || ((ERRORS++))
    check_api || ((ERRORS++))
    check_uploads_dir
    
    if [ $ERRORS -gt 0 ]; then
        ALERT_MSG="$ERRORS issues detected in ImageLab application"
        log "ALERT: $ALERT_MSG"
        send_alert "$ALERT_MSG"
    fi
    
    log "Monitoring check completed"
    sleep 300  # Check every 5 minutes
done
