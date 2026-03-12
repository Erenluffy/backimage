import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Server config
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # File upload config
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'heic'}
    
    # ImageMagick config
    IMAGEMAGICK_PATH = os.getenv('IMAGEMAGICK_PATH', '/usr/bin/convert')
    IMAGEMAGICK_MEMORY_LIMIT = '256MiB'
    IMAGEMAGICK_TIME_LIMIT = '30'
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100/hour"
    
    # File cleanup
    CLEANUP_INTERVAL = 3600  # 1 hour
    MAX_FILE_AGE = 3600  # 1 hour
    
    # Cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
