from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
import uuid
import os
import zipfile
from . import batch_bp
from utils.image_processor import ImageProcessor
from utils.file_handler import FileHandler
import concurrent.futures
import threading

image_processor = ImageProcessor()
file_handler = FileHandler('static/uploads')

# Thread pool for parallel processing
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

@batch_bp.route('/resize', methods=['POST'])
def batch_resize():
    """
    Resize multiple images
    POST: images[], width, height, maintain_aspect
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        
        if len(files) > 20:
            return jsonify({'error': 'Maximum 20 images allowed'}), 400
        
        width = request.form.get('width', 0, type=int)
        height = request.form.get('height', 0, type=int)
        maintain_aspect = request.form.get('maintain_aspect', 'true').lower() == 'true'
        
        if width <= 0 and height <= 0:
            return jsonify({'error': 'Either width or height must be positive'}), 400
        
        # Process files in parallel
        file_id = str(uuid.uuid4())
        results = []
        futures = []
        
        for i, file in enumerate(files):
            future = executor.submit(process_single_resize, file, i, file_id, {
                'width': width,
                'height': height,
                'maintain_aspect': maintain_aspect
            })
            futures.append(future)
        
        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
        
        # Create zip file
        zip_path = create_results_zip(results, file_id, "resized")
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name="resized_images.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup will happen in the cleanup thread
        pass

@batch_bp.route('/convert', methods=['POST'])
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
        
        if target_format not in ['jpg', 'png', 'webp']:
            return jsonify({'error': 'Unsupported format'}), 400
        
        if len(files) > 20:
            return jsonify({'error': 'Maximum 20 images allowed'}), 400
        
        # Process files in parallel
        file_id = str(uuid.uuid4())
        results = []
        futures = []
        
        for i, file in enumerate(files):
            future = executor.submit(process_single_convert, file, i, file_id, {
                'format': target_format
            })
            futures.append(future)
        
        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
        
        # Create zip file
        zip_path = create_results_zip(results, file_id, f"converted_to_{target_format}")
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"converted_images.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@batch_bp.route('/watermark', methods=['POST'])
def batch_watermark():
    """
    Add watermark to multiple images
    POST: images[], watermark_text, position, opacity
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        watermark_text = request.form.get('watermark_text', 'ImageLab Studio')
        position = request.form.get('position', 'bottom-right')
        opacity = request.form.get('opacity', 50, type=int)
        
        if len(files) > 20:
            return jsonify({'error': 'Maximum 20 images allowed'}), 400
        
        if opacity < 0 or opacity > 100:
            return jsonify({'error': 'Opacity must be between 0 and 100'}), 400
        
        # Process files in parallel
        file_id = str(uuid.uuid4())
        results = []
        futures = []
        
        for i, file in enumerate(files):
            future = executor.submit(process_single_watermark, file, i, file_id, {
                'watermark_text': watermark_text,
                'position': position,
                'opacity': opacity
            })
            futures.append(future)
        
        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
        
        # Create zip file
        zip_path = create_results_zip(results, file_id, "watermarked")
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name="watermarked_images.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@batch_bp.route('/rename', methods=['POST'])
def batch_rename():
    """
    Rename multiple images
    POST: images[], prefix, start_number
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        prefix = request.form.get('prefix', 'image')
        start_number = request.form.get('start_number', 1, type=int)
        
        if len(files) > 50:
            return jsonify({'error': 'Maximum 50 images allowed'}), 400
        
        # Process renaming
        file_id = str(uuid.uuid4())
        results = []
        
        for i, file in enumerate(files):
            # Save with new name
            ext = file.filename.rsplit('.', 1)[-1].lower()
            new_filename = f"{prefix}_{start_number + i}.{ext}"
            
            # Save file
            input_path = file_handler.save_upload(file, f"{file_id}_{i}")
            
            # Create copy with new name
            output_path = f"static/uploads/{file_id}_renamed_{i}.{ext}"
            
            import shutil
            shutil.copy2(input_path, output_path)
            
            results.append({
                'original': file.filename,
                'renamed': new_filename,
                'path': output_path
            })
        
        # Create zip file
        zip_path = f"static/uploads/{file_id}_renamed.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for result in results:
                zipf.write(result['path'], arcname=result['renamed'])
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name="renamed_images.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        file_handler.cleanup(file_id)

@batch_bp.route('/optimize', methods=['POST'])
def batch_optimize():
    """
    Optimize multiple images for web
    POST: images[], quality
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        quality = request.form.get('quality', 80, type=int)
        
        if len(files) > 20:
            return jsonify({'error': 'Maximum 20 images allowed'}), 400
        
        if quality < 1 or quality > 100:
            return jsonify({'error': 'Quality must be between 1 and 100'}), 400
        
        # Process files in parallel
        file_id = str(uuid.uuid4())
        results = []
        futures = []
        
        for i, file in enumerate(files):
            future = executor.submit(process_single_optimize, file, i, file_id, {
                'quality': quality
            })
            futures.append(future)
        
        # Collect results
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
        
        # Calculate total savings
        total_original = sum(r['original_size'] for r in results)
        total_optimized = sum(r['optimized_size'] for r in results)
        savings = ((total_original - total_optimized) / total_original) * 100 if total_original > 0 else 0
        
        # Create zip file
        zip_path = create_results_zip(results, file_id, "optimized")
        
        # Add metadata file
        metadata_path = f"static/uploads/{file_id}_metadata.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump({
                'total_files': len(results),
                'total_original_size': total_original,
                'total_optimized_size': total_optimized,
                'savings_percentage': f"{savings:.1f}%",
                'quality_used': quality
            }, f)
        
        # Add metadata to zip
        with zipfile.ZipFile(zip_path, 'a') as zipf:
            zipf.write(metadata_path, arcname='optimization_report.json')
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name="optimized_images.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@batch_bp.route('/status/<job_id>', methods=['GET'])
def batch_status(job_id):
    """
    Check status of batch job
    GET: job_id
    """
    # This would be implemented with a job queue like Celery
    # For now, return placeholder
    return jsonify({
        'job_id': job_id,
        'status': 'completed',
        'progress': 100
    })

# Helper functions for parallel processing

def process_single_resize(file, index, file_id, params):
    """Process single image for batch resize"""
    try:
        input_path = file_handler.save_upload(file, f"{file_id}_{index}")
        
        result = image_processor.resize_image(input_path, params)
        
        if result['success']:
            return {
                'original': file.filename,
                'path': result['output_path'],
                'index': index
            }
    except:
        pass
    return None

def process_single_convert(file, index, file_id, params):
    """Process single image for batch convert"""
    try:
        input_path = file_handler.save_upload(file, f"{file_id}_{index}")
        
        result = image_processor.convert_format(input_path, params)
        
        if result['success']:
            # Generate new filename with new extension
            base = file.filename.rsplit('.', 1)[0]
            new_filename = f"{base}.{params['format']}"
            
            return {
                'original': file.filename,
                'renamed': new_filename,
                'path': result['output_path'],
                'index': index
            }
    except:
        pass
    return None

def process_single_watermark(file, index, file_id, params):
    """Process single image for batch watermark"""
    try:
        input_path = file_handler.save_upload(file, f"{file_id}_{index}")
        
        result = image_processor.add_watermark(input_path, params)
        
        if result['success']:
            return {
                'original': file.filename,
                'path': result['output_path'],
                'index': index
            }
    except:
        pass
    return None

def process_single_optimize(file, index, file_id, params):
    """Process single image for batch optimize"""
    try:
        input_path = file_handler.save_upload(file, f"{file_id}_{index}")
        
        result = image_processor.compress_image(input_path, params)
        
        if result['success']:
            return {
                'original': file.filename,
                'path': result['output_path'],
                'original_size': result['metadata']['original_size'],
                'optimized_size': result['metadata']['compressed_size'],
                'index': index
            }
    except:
        pass
    return None

def create_results_zip(results, file_id, prefix):
    """Create zip file from results"""
    zip_path = f"static/uploads/{file_id}_{prefix}.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for result in results:
            if 'renamed' in result:
                zipf.write(result['path'], arcname=result['renamed'])
            else:
                zipf.write(result['path'], arcname=f"{prefix}_{result['index']}_{os.path.basename(result['path'])}")
    
    return zip_path
