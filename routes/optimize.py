from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
from . import optimize_bp
from utils.image_processor import ImageProcessor
from utils.file_handler import FileHandler
from utils.validators import validate_image, validate_params

# Initialize processors
image_processor = ImageProcessor()
file_handler = FileHandler('static/uploads')

@optimize_bp.route('/compress', methods=['POST'])
def compress_image():
    """
    Compress image with quality control
    POST: image, quality (1-100)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        quality = request.form.get('quality', 80, type=int)
        
        # Validate
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        if quality < 1 or quality > 100:
            return jsonify({'error': 'Quality must be between 1 and 100'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.compress_image(input_path, {'quality': quality})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"compressed_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@optimize_bp.route('/resize', methods=['POST'])
def resize_image():
    """
    Resize image to specified dimensions
    POST: image, width, height, maintain_aspect
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        width = request.form.get('width', 0, type=int)
        height = request.form.get('height', 0, type=int)
        maintain_aspect = request.form.get('maintain_aspect', 'true').lower() == 'true'
        
        # Validate
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        if width <= 0 and height <= 0:
            return jsonify({'error': 'Either width or height must be positive'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.resize_image(input_path, {
            'width': width,
            'height': height,
            'maintain_aspect': maintain_aspect
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"resized_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@optimize_bp.route('/crop', methods=['POST'])
def crop_image():
    """
    Crop image to specified region
    POST: image, x, y, width, height
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        x = request.form.get('x', 0, type=int)
        y = request.form.get('y', 0, type=int)
        width = request.form.get('width', 0, type=int)
        height = request.form.get('height', 0, type=int)
        
        # Validate
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        if width <= 0 or height <= 0:
            return jsonify({'error': 'Width and height must be positive'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.crop_image(input_path, {
            'x': x, 'y': y, 'width': width, 'height': height
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"cropped_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@optimize_bp.route('/optimize-web', methods=['POST'])
def optimize_for_web():
    """
    Optimize image specifically for web use
    POST: image
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Validate
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.optimize_for_web(input_path, {})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"web_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@optimize_bp.route('/reduce-colors', methods=['POST'])
def reduce_colors():
    """
    Reduce color palette of image
    POST: image, colors (2-256)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        colors = request.form.get('colors', 64, type=int)
        
        # Validate
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        if colors < 2 or colors > 256:
            return jsonify({'error': 'Colors must be between 2 and 256'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.reduce_colors(input_path, {'colors': colors})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"reduced_{secure_filename(file.filename)}",
                mimetype='image/png'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@optimize_bp.route('/smart-crop', methods=['POST'])
def smart_crop():
    """
    AI-powered smart cropping
    POST: image, aspect_ratio (optional)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        aspect_ratio = request.form.get('aspect_ratio', '1:1')
        
        # Validate
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.smart_crop(input_path, {'aspect_ratio': aspect_ratio})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"smart_cropped_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@optimize_bp.route('/thumbnail', methods=['POST'])
def create_thumbnail():
    """
    Create thumbnail from image
    POST: image, size (e.g., 150x150)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        size = request.form.get('size', '150x150')
        
        # Parse size
        try:
            width, height = map(int, size.lower().split('x'))
        except:
            return jsonify({'error': 'Invalid size format. Use WxH (e.g., 150x150)'}), 400
        
        # Validate
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.create_thumbnail(input_path, {
            'width': width,
            'height': height
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"thumbnail_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)
