from flask import Blueprint, request, jsonify, send_file
from app import image_processor, file_handler
from utils.validators import validate_image, validate_params
import os

optimize_bp = Blueprint('optimize', __name__)

@optimize_bp.route('/compress', methods=['POST'])
def compress():
    """Compress image endpoint"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        quality = request.form.get('quality', 80)
        
        # Validate image
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Save file
        input_path = file_handler.save_upload(file)
        
        # Process
        result = image_processor.compress_image(input_path, {'quality': quality})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"compressed_{file.filename}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@optimize_bp.route('/resize', methods=['POST'])
def resize():
    """Resize image endpoint"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        width = request.form.get('width', 0)
        height = request.form.get('height', 0)
        maintain_aspect = request.form.get('maintain_aspect', 'true')
        
        # Validate parameters
        if not width and not height:
            return jsonify({'error': 'Either width or height required'}), 400
        
        # Validate image
        is_valid, error = validate_image(file)
        if not is_valid:
            return jsonify({'error': error}), 400
        
        # Save file
        input_path = file_handler.save_upload(file)
        
        # Process
        result = image_processor.resize_image(input_path, {
            'width': width,
            'height': height,
            'maintain_aspect': maintain_aspect
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"resized_{file.filename}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
