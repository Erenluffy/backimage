"""Gunicorn configuration file"""
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
graceful_timeout = 30
keepalive = 2

# Logging
accesslog = "/var/www/imagelab-backend/logs/access.log"
errorlog = "/var/www/imagelab-backend/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "imagelab"

# Server mechanics
daemon = False
pidfile = "/var/www/imagelab-backend/gunicorn.pid"
umask = 0o007
user = "www-data"
group = "www-data"

# SSL (if using direct SSL)
# keyfile = "/etc/ssl/private/imagelab.key"
# certfile = "/etc/ssl/certs/imagelab.crt"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
