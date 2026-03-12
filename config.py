import os
from dotenv import load_dotenv
import secrets

load_dotenv()

class Config:
    # Server config
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # File upload config
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'heic'}
    
    # ImageMagick config
    IMAGEMAGICK_PATH = os.getenv('IMAGEMAGICK_PATH', '/usr/bin/convert')
    IMAGEMAGICK_MEMORY_LIMIT = '256MiB'
    IMAGEMAGICK_TIME_LIMIT = '30'
    
    # Security - CRITICAL: Secret key must be set in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY and not DEBUG:
        raise ValueError("SECRET_KEY must be set in production environment")
    elif not SECRET_KEY and DEBUG:
        SECRET_KEY = 'dev-secret-key-change-in-production'
        print("WARNING: Using default secret key for development")
    
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
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
