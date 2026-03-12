import os
from PIL import Image
import imghdr
import magic

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'heic'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_image(file):
    """Validate uploaded image file"""
    try:
        # Check if file exists
        if not file:
            return False, "No file provided"
        
        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_FILE_SIZE:
            return False, f"File too large. Max size: {MAX_FILE_SIZE//1024//1024}MB"
        
        # Check extension
        filename = file.filename
        if '.' not in filename:
            return False, "No file extension"
        
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Validate image content
        file.seek(0)
        
        # Try PIL first
        try:
            img = Image.open(file)
            img.verify()
            file.seek(0)
        except:
            # Try python-magic
            mime = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)
            if not mime.startswith('image/'):
                return False, "Invalid image file"
        
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_params(params, required_params):
    """Validate required parameters"""
    missing = []
    for param in required_params:
        if param not in params:
            missing.append(param)
    
    if missing:
        return False, f"Missing parameters: {', '.join(missing)}"
    
    return True, None

def sanitize_filename(filename):
    """Sanitize filename for security"""
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove any non-printable characters
    filename = ''.join(c for c in filename if c.isprintable())
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + '.' + ext
    
    return filename
