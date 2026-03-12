from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid
import os
from . import convert_bp
from utils.image_processor import ImageProcessor
from utils.file_handler import FileHandler

image_processor = ImageProcessor()
file_handler = FileHandler('static/uploads')

@convert_bp.route('/jpg-to-png', methods=['POST'])
def jpg_to_png():
    """
    Convert JPG to PNG
    POST: image
    """
    return convert_format('png')

@convert_bp.route('/png-to-jpg', methods=['POST'])
def png_to_jpg():
    """
    Convert PNG to JPG
    POST: image
    """
    return convert_format('jpg')

@convert_bp.route('/to-webp', methods=['POST'])
def to_webp():
    """
    Convert to WEBP format
    POST: image
    """
    return convert_format('webp')

@convert_bp.route('/heic-to-jpg', methods=['POST'])
def heic_to_jpg():
    """
    Convert HEIC to JPG (iPhone photos)
    POST: image
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Check if HEIC format
        filename = file.filename.lower()
        if not filename.endswith('.heic'):
            return jsonify({'error': 'File must be HEIC format'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.heic_to_jpg(input_path, {})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"{secure_filename(file.filename).rsplit('.',1)[0]}.jpg",
                mimetype='image/jpeg'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@convert_bp.route('/create-gif', methods=['POST'])
def create_gif():
    """
    Create GIF from multiple images
    POST: images[], duration, loop
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        
        if len(files) < 2:
            return jsonify({'error': 'At least 2 images required for GIF'}), 400
        
        duration = request.form.get('duration', 100, type=int)
        loop = request.form.get('loop', 0, type=int)
        
        # Save all files
        file_id = str(uuid.uuid4())
        input_paths = []
        
        for i, file in enumerate(files):
            path = file_handler.save_upload(file, f"{file_id}_{i}")
            input_paths.append(path)
        
        # Process
        result = image_processor.create_gif(input_paths, {
            'duration': duration,
            'loop': loop,
            'output_path': f"static/uploads/{file_id}_animation.gif"
        })
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name="animation.gif",
                mimetype='image/gif'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@convert_bp.route('/gif-to-mp4', methods=['POST'])
def gif_to_mp4():
    """
    Convert GIF to MP4 video
    POST: image
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        if not file.filename.lower().endswith('.gif'):
            return jsonify({'error': 'File must be GIF format'}), 400
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.gif_to_mp4(input_path, {})
        
        if result['success']:
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=f"{secure_filename(file.filename).rsplit('.',1)[0]}.mp4",
                mimetype='video/mp4'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@convert_bp.route('/batch-convert', methods=['POST'])
def batch_convert():
    """
    Convert multiple images to same format
    POST: images[], format
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        target_format = request.form.get('format', 'jpg')
        
        if target_format not in ['jpg', 'png', 'webp', 'gif']:
            return jsonify({'error': 'Unsupported format'}), 400
        
        # Process each file
        file_id = str(uuid.uuid4())
        results = []
        
        for i, file in enumerate(files):
            input_path = file_handler.save_upload(file, f"{file_id}_{i}")
            
            result = image_processor.convert_format(input_path, {
                'format': target_format
            })
            
            if result['success']:
                results.append({
                    'original': file.filename,
                    'converted': os.path.basename(result['output_path'])
                })
        
        # Create zip file with all converted images
        import zipfile
        zip_path = f"static/uploads/{file_id}_converted.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for result in results:
                zipf.write(
                    f"static/uploads/{result['converted']}",
                    arcname=result['converted']
                )
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name="converted_images.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

def convert_format(target_format):
    """Generic format conversion handler"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        # Process
        file_id = str(uuid.uuid4())
        input_path = file_handler.save_upload(file, file_id)
        
        result = image_processor.convert_format(input_path, {'format': target_format})
        
        if result['success']:
            # Change extension in filename
            original_name = secure_filename(file.filename)
            base_name = original_name.rsplit('.', 1)[0]
            new_filename = f"{base_name}.{target_format}"
            
            return send_file(
                result['output_path'],
                as_attachment=True,
                download_name=new_filename,
                mimetype=f'image/{target_format}'
            )
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)
