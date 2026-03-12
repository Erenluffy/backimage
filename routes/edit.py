from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid
from . import edit_bp
from utils.image_processor import ImageProcessor
from utils.file_handler import FileHandler

image_processor = ImageProcessor()
file_handler = FileHandler('static/uploads')

@edit_bp.route('/rotate', methods=['POST'])
def rotate_image():
    """
    Rotate image by degrees
    POST: image, angle (0-360)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        angle = request.form.get('angle', 90, type=int)
        
        # Validate
        if angle % 90 != 0:
            return jsonify({'error': 'Angle must be multiple of 90'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.rotate_image(input_path, {'angle': angle})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"rotated_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@edit_bp.route('/flip', methods=['POST'])
def flip_image():
    """
    Flip image horizontally or vertically
    POST: image, direction (horizontal/vertical)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        direction = request.form.get('direction', 'horizontal')
        
        if direction not in ['horizontal', 'vertical']:
            return jsonify({'error': 'Direction must be horizontal or vertical'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.flip_image(input_path, {'direction': direction})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"flipped_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@edit_bp.route('/watermark', methods=['POST'])
def add_watermark():
    """
    Add watermark to image
    POST: image, watermark_text, position, opacity
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        watermark_text = request.form.get('watermark_text', 'ImageLab Studio')
        position = request.form.get('position', 'bottom-right')
        opacity = request.form.get('opacity', 50, type=int)
        
        if opacity < 0 or opacity > 100:
            return jsonify({'error': 'Opacity must be between 0 and 100'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.add_watermark(input_path, {
            'watermark_text': watermark_text,
            'position': position,
            'opacity': opacity
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"watermarked_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@edit_bp.route('/blur-faces', methods=['POST'])
def blur_faces():
    """
    Detect and blur faces in image
    POST: image
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.blur_faces(input_path, {})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"blurred_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@edit_bp.route('/adjust-colors', methods=['POST'])
def adjust_colors():
    """
    Adjust image colors
    POST: image, brightness, contrast, saturation
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        brightness = request.form.get('brightness', 1.0, type=float)
        contrast = request.form.get('contrast', 1.0, type=float)
        saturation = request.form.get('saturation', 1.0, type=float)
        
        # Validate ranges
        if brightness < 0 or brightness > 2:
            return jsonify({'error': 'Brightness must be between 0 and 2'}), 400
        if contrast < 0 or contrast > 2:
            return jsonify({'error': 'Contrast must be between 0 and 2'}), 400
        if saturation < 0 or saturation > 2:
            return jsonify({'error': 'Saturation must be between 0 and 2'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.adjust_colors(input_path, {
            'brightness': brightness,
            'contrast': contrast,
            'saturation': saturation
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"adjusted_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@edit_bp.route('/apply-filter', methods=['POST'])
def apply_filter():
    """
    Apply filter to image
    POST: image, filter_type, intensity
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        filter_type = request.form.get('filter_type', 'blur')
        intensity = request.form.get('intensity', 1.0, type=float)
        
        allowed_filters = ['blur', 'sharpen', 'edge_enhance', 'emboss', 'contour', 'smooth', 'grayscale', 'sepia']
        
        if filter_type not in allowed_filters:
            return jsonify({'error': f'Filter must be one of: {", ".join(allowed_filters)}'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.apply_filter(input_path, {
            'filter_type': filter_type,
            'intensity': intensity
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"{filter_type}_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@edit_bp.route('/remove-object', methods=['POST'])
def remove_object():
    """
    Remove object from image (inpainting)
    POST: image, mask (optional)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Check if mask provided
        mask = request.files.get('mask', None)
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        mask_path = None
        if mask:
            mask_path = file_handler.save_upload(mask, f"{file_id}_mask")
        
        result = image_processor.remove_object(input_path, {
            'mask_path': mask_path
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"cleaned_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)
        if mask_path:
            file_handler.cleanup(f"{file_id}_mask")

@edit_bp.route('/adjust-levels', methods=['POST'])
def adjust_levels():
    """
    Adjust image levels (shadows, midtones, highlights)
    POST: image, shadows, midtones, highlights
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        shadows = request.form.get('shadows', 0, type=int)
        midtones = request.form.get('midtones', 0, type=int)
        highlights = request.form.get('highlights', 0, type=int)
        
        # Validate ranges
        if shadows < -100 or shadows > 100:
            return jsonify({'error': 'Shadows must be between -100 and 100'}), 400
        if midtones < -100 or midtones > 100:
            return jsonify({'error': 'Midtones must be between -100 and 100'}), 400
        if highlights < -100 or highlights > 100:
            return jsonify({'error': 'Highlights must be between -100 and 100'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.adjust_levels(input_path, {
            'shadows': shadows,
            'midtones': midtones,
            'highlights': highlights
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"levels_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)
