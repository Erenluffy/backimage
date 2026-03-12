from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid
from . import create_bp
from utils.image_processor import ImageProcessor
from utils.file_handler import FileHandler

image_processor = ImageProcessor()
file_handler = FileHandler('static/uploads')

@create_bp.route('/remove-background', methods=['POST'])
def remove_background():
    """
    Remove background using AI
    POST: image
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.remove_background(input_path, {})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"nobg_{secure_filename(file.filename).rsplit('.',1)[0]}.png",
                mimetype='image/png'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@create_bp.route('/meme', methods=['POST'])
def create_meme():
    """
    Create meme with text
    POST: image, top_text, bottom_text
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        top_text = request.form.get('top_text', '')
        bottom_text = request.form.get('bottom_text', '')
        
        if not top_text and not bottom_text:
            return jsonify({'error': 'At least one text field required'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.create_meme(input_path, {
            'top_text': top_text,
            'bottom_text': bottom_text
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"meme_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@create_bp.route('/upscale', methods=['POST'])
def upscale_image():
    """
    Upscale image using AI
    POST: image, scale_factor (1.5-4.0)
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        scale_factor = request.form.get('scale_factor', 2.0, type=float)
        
        if scale_factor < 1.5 or scale_factor > 4.0:
            return jsonify({'error': 'Scale factor must be between 1.5 and 4.0'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.upscale_image(input_path, {'scale_factor': scale_factor})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"upscaled_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@create_bp.route('/add-text', methods=['POST'])
def add_text():
    """
    Add text overlay to image
    POST: image, text, position, font_size, color
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        text = request.form.get('text', '')
        position = request.form.get('position', 'bottom')
        font_size = request.form.get('font_size', 32, type=int)
        color = request.form.get('color', '#ffffff')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.add_text_overlay(input_path, {
            'text': text,
            'position': position,
            'font_size': font_size,
            'color': color
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"text_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@create_bp.route('/add-stickers', methods=['POST'])
def add_stickers():
    """
    Add stickers to image
    POST: image, sticker_type, position, size
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        sticker_type = request.form.get('sticker_type', 'happy')
        position = request.form.get('position', 'center')
        size = request.form.get('size', 50, type=int)
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.add_stickers(input_path, {
            'sticker_type': sticker_type,
            'position': position,
            'size': size
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"stickers_{secure_filename(file.filename)}",
                mimetype='image/png'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@create_bp.route('/ai-generate', methods=['POST'])
def ai_generate():
    """
    Generate image using AI (text-to-image)
    POST: prompt, style, size
    """
    try:
        prompt = request.form.get('prompt', '')
        style = request.form.get('style', 'realistic')
        size = request.form.get('size', '512x512')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Process
        result = image_processor.ai_generate({
            'prompt': prompt,
            'style': style,
            'size': size
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"ai_generated.png",
                mimetype='image/png'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
