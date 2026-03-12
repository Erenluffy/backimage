from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid
import os
from . import security_bp
from utils.image_processor import ImageProcessor
from utils.file_handler import FileHandler
from utils.security import SecurityManager

image_processor = ImageProcessor()
file_handler = FileHandler('static/uploads')
security_manager = SecurityManager()

@security_bp.route('/blur-license-plate', methods=['POST'])
def blur_license_plate():
    """
    Detect and blur license plates
    POST: image
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.blur_license_plate(input_path, {})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"blurred_plate_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@security_bp.route('/add-signature', methods=['POST'])
def add_signature():
    """
    Add signature to image
    POST: image, signature_text, position
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        signature_text = request.form.get('signature_text', '')
        position = request.form.get('position', 'bottom-right')
        
        if not signature_text:
            return jsonify({'error': 'Signature text is required'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.add_signature(input_path, {
            'signature_text': signature_text,
            'position': position
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"signed_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@security_bp.route('/remove-metadata', methods=['POST'])
def remove_metadata():
    """
    Remove all metadata from image
    POST: image
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.remove_metadata(input_path, {})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"clean_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@security_bp.route('/encrypt', methods=['POST'])
def encrypt_image():
    """
    Encrypt image with password
    POST: image, password
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        password = request.form.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Read image data
        image_data = file.read()
        
        # Encrypt
        encrypted_data = security_manager.encrypt_image(image_data, password)
        
        # Save encrypted file
        file_id = str(uuid.uuid4())
        output_path = f"static/uploads/{file_id}_encrypted.bin"
        
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{secure_filename(file.filename)}.encrypted",
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

@security_bp.route('/decrypt', methods=['POST'])
def decrypt_image():
    """
    Decrypt image with password
    POST: encrypted_file, password
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        password = request.form.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Read encrypted data
        encrypted_data = file.read()
        
        # Decrypt
        decrypted_data = security_manager.decrypt_image(encrypted_data, password)
        
        # Determine original format (try to detect)
        import imghdr
        from io import BytesIO
        
        # Try to detect image type
        img_format = imghdr.what(None, h=decrypted_data)
        extension = img_format if img_format else 'bin'
        
        # Save decrypted file
        file_id = str(uuid.uuid4())
        output_path = f"static/uploads/{file_id}_decrypted.{extension}"
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"decrypted_image.{extension}",
            mimetype=f'image/{extension}' if extension != 'bin' else 'application/octet-stream'
        )
        
    except Exception as e:
        return jsonify({'error': 'Invalid password or corrupted file'}), 400
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

@security_bp.route('/blur-faces-advanced', methods=['POST'])
def blur_faces_advanced():
    """
    Advanced face blurring with multiple options
    POST: image, blur_type (gaussian/pixelate), intensity
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        blur_type = request.form.get('blur_type', 'gaussian')
        intensity = request.form.get('intensity', 30, type=int)
        
        if blur_type not in ['gaussian', 'pixelate']:
            return jsonify({'error': 'Blur type must be gaussian or pixelate'}), 400
        
        if intensity < 1 or intensity > 100:
            return jsonify({'error': 'Intensity must be between 1 and 100'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.blur_faces_advanced(input_path, {
            'blur_type': blur_type,
            'intensity': intensity
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"blurred_faces_{secure_filename(file.filename)}",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@security_bp.route('/watermark-text', methods=['POST'])
def watermark_with_text():
    """
    Add text watermark for security
    POST: image, text, opacity, repeat
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        text = request.form.get('text', 'CONFIDENTIAL')
        opacity = request.form.get('opacity', 30, type=int)
        repeat = request.form.get('repeat', 'false').lower() == 'true'
        
        if opacity < 1 or opacity > 100:
            return jsonify({'error': 'Opacity must be between 1 and 100'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.watermark_with_text(input_path, {
            'text': text,
            'opacity': opacity,
            'repeat': repeat
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
