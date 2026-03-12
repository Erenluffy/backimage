from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import uuid
import logging
from datetime import datetime
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Import custom modules with error handling
try:
    from config import Config
    logger.info("✓ Config module loaded")
except Exception as e:
    logger.error(f"✗ Failed to load Config: {str(e)}")
    raise

try:
    from utils.image_processor import ImageProcessor
    from utils.file_handler import FileHandler
    from utils.validators import validate_image, validate_params
    from utils.security import SecurityManager
    logger.info("✓ Utils modules loaded")
except Exception as e:
    logger.error(f"✗ Failed to load utils modules: {str(e)}")
    raise

try:
    from routes.optimize import optimize_bp
    from routes.create import create_bp
    from routes.edit import edit_bp
    from routes.convert import convert_bp
    from routes.security import security_bp
    from routes.batch import batch_bp
    logger.info("✓ Route blueprints loaded")
except Exception as e:
    logger.error(f"✗ Failed to load route blueprints: {str(e)}")
    raise

# Initialize Flask app
app = Flask(__name__)

# Load configuration
try:
    app.config.from_object(Config)
    logger.info("✓ Configuration loaded")
except Exception as e:
    logger.error(f"✗ Failed to load configuration: {str(e)}")
    # Set default config if file missing
    app.config['DEBUG'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'heic'}
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    logger.warning("Using default configuration")

# Configure CORS - Allow all origins for development, restrict in production
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "https://your-frontend-domain.com",  # Add your frontend domain
            "*"  # Remove this in production
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Create required directories
def create_directories():
    """Create necessary directories if they don't exist"""
    dirs = [
        app.config.get('UPLOAD_FOLDER', 'static/uploads'),
        'logs',
        'static'
    ]
    
    for dir_path in dirs:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Directory ensured: {dir_path}")
        except Exception as e:
            logger.error(f"✗ Failed to create directory {dir_path}: {str(e)}")

create_directories()

# Initialize utilities with error handling
try:
    upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    image_processor = ImageProcessor()
    file_handler = FileHandler(upload_folder)
    security_manager = SecurityManager()
    logger.info("✓ Utilities initialized successfully")
except Exception as e:
    logger.error(f"✗ Failed to initialize utilities: {str(e)}")
    raise

# Register blueprints with error handling
try:
    app.register_blueprint(optimize_bp, url_prefix='/api/optimize')
    app.register_blueprint(create_bp, url_prefix='/api/create')
    app.register_blueprint(edit_bp, url_prefix='/api/edit')
    app.register_blueprint(convert_bp, url_prefix='/api/convert')
    app.register_blueprint(security_bp, url_prefix='/api/security')
    app.register_blueprint(batch_bp, url_prefix='/api/batch')
    logger.info("✓ All blueprints registered successfully")
except Exception as e:
    logger.error(f"✗ Failed to register blueprints: {str(e)}")
    raise

# Startup check
@app.before_first_request
def startup_check():
    """Run startup checks before first request"""
    logger.info("="*60)
    logger.info("ImageLab Backend Starting...")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    logger.info(f"Port: {os.environ.get('PORT', '5000')}")
    logger.info(f"Upload folder: {app.config.get('UPLOAD_FOLDER')}")
    logger.info(f"Max content length: {app.config.get('MAX_CONTENT_LENGTH')} bytes")
    logger.info(f"Allowed extensions: {app.config.get('ALLOWED_EXTENSIONS')}")
    
    # Check if upload directory is writable
    upload_dir = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    test_file = Path(upload_dir) / 'test.txt'
    try:
        test_file.write_text('test')
        test_file.unlink()
        logger.info(f"✓ Upload directory is writable: {upload_dir}")
    except Exception as e:
        logger.error(f"✗ Upload directory not writable: {str(e)}")
    
    logger.info("="*60)

# Root endpoint
@app.route('/')
def index():
    """Serve the main HTML page or API info"""
    try:
        return render_template('index.html')
    except:
        return jsonify({
            'name': 'ImageLab API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': [
                '/api/health',
                '/api/process',
                '/api/optimize/*',
                '/api/create/*',
                '/api/edit/*',
                '/api/convert/*',
                '/api/security/*',
                '/api/batch/*'
            ]
        })

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'debug': app.config.get('DEBUG', False)
    })

# Simple test endpoint
@app.route('/api/test', methods=['GET'])
def test():
    """Simple test endpoint"""
    return jsonify({
        'message': 'API is working!',
        'method': 'GET',
        'time': datetime.now().isoformat()
    })

# Main processing endpoint
@app.route('/api/process', methods=['POST', 'OPTIONS'])
def process_image():
    """Generic image processing endpoint"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        operation = request.form.get('operation', '')
        params = request.form.to_dict()
        
        # Log request
        logger.info(f"Processing request: operation={operation}, file={file.filename}")
        
        # Validate file
        is_valid, error = validate_image(file)
        if not is_valid:
            logger.warning(f"File validation failed: {error}")
            return jsonify({'error': error}), 400
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        logger.info(f"File saved: {input_path}")
        
        # Process image based on operation
        result = image_processor.process(operation, input_path, params)
        
        if result['success']:
            logger.info(f"Processing successful for {file.filename}")
            # Return processed image
            filename = secure_filename(file.filename)
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"processed_{filename}",
                mimetype='image/jpeg'
            )
        else:
            logger.error(f"Processing failed: {result.get('error')}")
            return jsonify({'error': result.get('error', 'Processing failed')}), 500
            
    except Exception as e:
        logger.error(f"Processing error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    finally:
        # Cleanup temporary files
        try:
            file_handler.cleanup(file_id)
        except:
            pass

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/',
            '/api/health',
            '/api/test',
            '/api/process',
            '/api/optimize/*',
            '/api/create/*',
            '/api/edit/*',
            '/api/convert/*',
            '/api/security/*',
            '/api/batch/*'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

# Graceful shutdown
@app.teardown_appcontext
def cleanup(error):
    """Clean up after request"""
    pass

if __name__ == '__main__':
    # Get port from environment variable for Render
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port} (debug={debug})")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
else:
    # For gunicorn, get the port from environment
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"App loaded by gunicorn, will listen on port {port}")
