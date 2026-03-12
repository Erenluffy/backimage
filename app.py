from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import logging

# Import custom modules
from config import Config
from utils.image_processor import ImageProcessor
from utils.file_handler import FileHandler
from utils.validators import validate_image, validate_params
from utils.security import SecurityManager

# Import route blueprints
from routes.optimize import optimize_bp
from routes.create import create_bp
from routes.edit import edit_bp
from routes.convert import convert_bp
from routes.security import security_bp
from routes.batch import batch_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize utilities
image_processor = ImageProcessor()
file_handler = FileHandler(Config.UPLOAD_FOLDER)
security_manager = SecurityManager()

# Register blueprints
app.register_blueprint(optimize_bp, url_prefix='/api/optimize')
app.register_blueprint(create_bp, url_prefix='/api/create')
app.register_blueprint(edit_bp, url_prefix='/api/edit')
app.register_blueprint(convert_bp, url_prefix='/api/convert')
app.register_blueprint(security_bp, url_prefix='/api/security')
app.register_blueprint(batch_bp, url_prefix='/api/batch')

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/process', methods=['POST'])
def process_image():
    """Generic image processing endpoint"""
    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        operation = request.form.get('operation', '')
        params = request.form.to_dict()
        
        # Validate file
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        # Process image based on operation
        result = image_processor.process(operation, input_path, params)
        
        if result['success']:
            # Return processed image
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"processed_{filename}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        # Cleanup temporary files
        file_handler.cleanup(file_id)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
