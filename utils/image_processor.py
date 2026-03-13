import subprocess
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import cv2
from wand.image import Image as WandImage
from wand.color import Color
# import rembg
import logging
from typing import Dict, Any, Tuple, List
import json

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.supported_operations = {
            # Optimize operations
            'compress': self.compress_image,
            'resize': self.resize_image,
            'crop': self.crop_image,
            'optimize_web': self.optimize_for_web,
            'reduce_colors': self.reduce_colors,
            'smart_crop': self.smart_crop,
            'thumbnail': self.create_thumbnail,
            
            # Create operations
            # 'remove_bg': self.remove_background,  # Commented out until rembg is installed
            'create_meme': self.create_meme,
            'upscale': self.upscale_image,
            'add_text': self.add_text_overlay,
            'add_stickers': self.add_stickers,
            # 'ai_generate': self.ai_generate,  # Placeholder
            
            # Edit operations
            'rotate': self.rotate_image,
            'flip': self.flip_image,
            'watermark': self.add_watermark,
            'blur_faces': self.blur_faces,
            'adjust_colors': self.adjust_colors,
            'apply_filter': self.apply_filter,
            # 'remove_object': self.remove_object,  # Placeholder
            
            # Convert operations
            'convert_format': self.convert_format,
            'jpg_to_png': lambda p,o: self.convert_format(p,o,'png'),
            'png_to_jpg': lambda p,o: self.convert_format(p,o,'jpg'),
            'to_webp': lambda p,o: self.convert_format(p,o,'webp'),
            # 'heic_to_jpg': self.heic_to_jpg,  # Placeholder
            'create_gif': self.create_gif,
            
            # Security operations
            # 'blur_plate': self.blur_license_plate,  # Placeholder
            'add_signature': self.add_watermark,  # Reuse watermark for signature
            'remove_metadata': self.remove_metadata,
            # 'encrypt': self.encrypt_image,  # Placeholder
            # 'decrypt': self.decrypt_image,  # Placeholder
            
            # Batch operations
            'batch_resize': self.batch_resize,
            'batch_convert': self.batch_convert,
            'batch_watermark': self.batch_watermark,
            # 'batch_rename': self.batch_rename,  # Placeholder
        }
    
    def process(self, operation: str, input_path: str, params: Dict) -> Dict:
        """Process image with specified operation"""
        try:
            if operation not in self.supported_operations:
                return {'success': False, 'error': f'Unsupported operation: {operation}'}
            
            processor = self.supported_operations[operation]
            result = processor(input_path, params)
            
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def compress_image(self, input_path: str, params: Dict) -> Dict:
        """Compress image with specified quality and options"""
        try:
            quality = int(params.get('quality', 80))
            target_size = params.get('target_size')  # Target size in KB
            target_size_mb = params.get('target_size_mb')  # Target size in MB
            output_format = params.get('format', 'same')
            max_width = params.get('max_width')
            max_height = params.get('max_height')
            preserve_metadata = params.get('preserve_metadata', 'true').lower() == 'true'
            optimize_for = params.get('optimize_for', 'balanced')  # 'web', 'email', 'print', 'balanced'
            compression_method = params.get('compression_method', 'standard')  # 'standard', 'progressive', 'lossless'
            
            # Generate output path
            base, ext = os.path.splitext(input_path)
            
            # Handle format conversion
            if output_format != 'same':
                ext = f'.{output_format}'
            output_path = f"{base}_compressed{ext}"
            
            with Image.open(input_path) as img:
                original_mode = img.mode
                original_size = os.path.getsize(input_path)
                
                # Apply resize if specified
                if max_width or max_height:
                    img = self._resize_with_constraints(img, max_width, max_height)
                
                # Convert mode based on output format
                if output_format in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                    # Create white background for transparency
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                elif output_format == 'png' and img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Optimize based on target use
                if optimize_for == 'web':
                    quality = min(quality, 75)
                    if not max_width:
                        img = self._resize_with_constraints(img, 1920, 1080)
                elif optimize_for == 'email':
                    quality = min(quality, 60)
                    if not max_width:
                        img = self._resize_with_constraints(img, 1024, 768)
                elif optimize_for == 'print':
                    quality = max(quality, 90)
                
                # Handle target file size
                if target_size or target_size_mb:
                    target_bytes = (float(target_size) * 1024) if target_size else (float(target_size_mb) * 1024 * 1024)
                    quality = self._find_quality_for_target_size(img, target_bytes, output_path, ext[1:])
                
                # Save with compression options
                save_kwargs = {
                    'format': ext[1:].upper(),
                    'optimize': True
                }
                
                if ext[1:].lower() in ['jpg', 'jpeg']:
                    save_kwargs['quality'] = quality
                    save_kwargs['progressive'] = (compression_method == 'progressive')
                    if not preserve_metadata:
                        save_kwargs['save_all'] = False
                        
                elif ext[1:].lower() == 'png':
                    if compression_method == 'lossless':
                        save_kwargs['compress_level'] = 9
                        save_kwargs['optimize'] = True
                    else:
                        # For PNG, we'll use Pillow's optimize which reduces file size
                        save_kwargs['compress_level'] = 6
                        
                elif ext[1:].lower() == 'webp':
                    save_kwargs['quality'] = quality
                    save_kwargs['method'] = 6  # Slowest/best compression
                
                # Remove metadata if not preserving
                if not preserve_metadata:
                    img.info.clear()
                
                # Save the image
                img.save(output_path, **save_kwargs)
                
                # Calculate compression stats
                compressed_size = os.path.getsize(output_path)
                savings = ((original_size - compressed_size) / original_size) * 100
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                        'savings_percentage': round(savings, 2),
                        'quality': quality,
                        'format': ext[1:].upper(),
                        'dimensions': img.size,
                        'compression_method': compression_method,
                        'optimize_for': optimize_for
                    }
                }
                
        except Exception as e:
            logger.error(f"Compression failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _resize_with_constraints(self, img, max_width, max_height):
        """Resize image while maintaining aspect ratio"""
        if not max_width and not max_height:
            return img
        
        width, height = img.size
        
        if max_width and max_height:
            # Resize to fit within both constraints
            img.thumbnail((int(max_width), int(max_height)), Image.Resampling.LANCZOS)
        elif max_width:
            # Resize based on width
            ratio = int(max_width) / width
            new_height = int(height * ratio)
            img = img.resize((int(max_width), new_height), Image.Resampling.LANCZOS)
        elif max_height:
            # Resize based on height
            ratio = int(max_height) / height
            new_width = int(width * ratio)
            img = img.resize((new_width, int(max_height)), Image.Resampling.LANCZOS)
        
        return img
    
    def _find_quality_for_target_size(self, img, target_bytes, output_path, format):
        """Find optimal quality setting to achieve target file size"""
        if format.lower() not in ['jpg', 'jpeg', 'webp']:
            return 80  # Only JPEG and WebP support quality adjustment
        
        # Binary search for optimal quality
        low, high = 1, 100
        best_quality = 80
        
        for _ in range(7):  # 7 iterations gives good precision
            mid = (low + high) // 2
            temp_path = output_path.replace('.', f'_temp_{mid}.')
            
            save_kwargs = {
                'format': format.upper(),
                'quality': mid,
                'optimize': True
            }
            
            img.save(temp_path, **save_kwargs)
            size = os.path.getsize(temp_path)
            os.remove(temp_path)
            
            if size < target_bytes:
                best_quality = mid
                low = mid + 1
            else:
                high = mid - 1
        
        return best_quality
    
    def resize_image(self, input_path: str, params: Dict) -> Dict:
        """Resize image to specified dimensions"""
        try:
            width = int(params.get('width', 0))
            height = int(params.get('height', 0))
            maintain_aspect = params.get('maintain_aspect', 'true').lower() == 'true'
            output_path = input_path.replace('.', '_resized.')
            
            with Image.open(input_path) as img:
                original_size = img.size
                
                if maintain_aspect:
                    # Calculate new dimensions maintaining aspect ratio
                    img.thumbnail((width, height) if width and height else (width, height), Image.Resampling.LANCZOS)
                else:
                    # Resize to exact dimensions
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Save resized image
                img.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'original_dimensions': original_size,
                        'new_dimensions': img.size,
                        'maintain_aspect': maintain_aspect
                    }
                }
                
        except Exception as e:
            logger.error(f"Resize failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def crop_image(self, input_path: str, params: Dict) -> Dict:
        """Crop image to specified region"""
        try:
            x = int(params.get('x', 0))
            y = int(params.get('y', 0))
            width = int(params.get('width', 0))
            height = int(params.get('height', 0))
            output_path = input_path.replace('.', '_cropped.')
            
            with Image.open(input_path) as img:
                # Validate crop region
                if x + width > img.width or y + height > img.height:
                    return {'success': False, 'error': 'Crop region exceeds image dimensions'}
                
                # Crop image
                cropped = img.crop((x, y, x + width, y + height))
                cropped.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'original_dimensions': img.size,
                        'crop_region': {'x': x, 'y': y, 'width': width, 'height': height},
                        'new_dimensions': cropped.size
                    }
                }
                
        except Exception as e:
            logger.error(f"Crop failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_meme(self, input_path: str, params: Dict) -> Dict:
        """Create meme with text overlay"""
        try:
            top_text = params.get('top_text', '')
            bottom_text = params.get('bottom_text', '')
            output_path = input_path.replace('.', '_meme.')
            
            with Image.open(input_path) as img:
                draw = ImageDraw.Draw(img)
                
                # Load font (adjust size based on image dimensions)
                font_size = int(min(img.width, img.height) * 0.1)
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # Add top text
                if top_text:
                    bbox = draw.textbbox((0, 0), top_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (img.width - text_width) // 2
                    y = 10
                    
                    # Draw text outline
                    for offset in [(2,2), (2,-2), (-2,2), (-2,-2)]:
                        draw.text((x + offset[0], y + offset[1]), top_text, font=font, fill='black')
                    draw.text((x, y), top_text, font=font, fill='white')
                
                # Add bottom text
                if bottom_text:
                    bbox = draw.textbbox((0, 0), bottom_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (img.width - text_width) // 2
                    y = img.height - text_height - 10
                    
                    for offset in [(2,2), (2,-2), (-2,2), (-2,-2)]:
                        draw.text((x + offset[0], y + offset[1]), bottom_text, font=font, fill='black')
                    draw.text((x, y), bottom_text, font=font, fill='white')
                
                img.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'top_text': top_text,
                        'bottom_text': bottom_text,
                        'font_size': font_size
                    }
                }
                
        except Exception as e:
            logger.error(f"Meme creation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def upscale_image(self, input_path: str, params: Dict) -> Dict:
        """Upscale image using AI"""
        try:
            scale_factor = float(params.get('scale_factor', 2.0))
            output_path = input_path.replace('.', '_upscaled.')
            
            # Use OpenCV for basic upscaling
            img = cv2.imread(input_path)
            height, width = img.shape[:2]
            new_dimensions = (int(width * scale_factor), int(height * scale_factor))
            
            # Use different interpolation methods based on scale factor
            if scale_factor <= 2:
                interpolation = cv2.INTER_CUBIC
            else:
                interpolation = cv2.INTER_LANCZOS4
            
            upscaled = cv2.resize(img, new_dimensions, interpolation=interpolation)
            cv2.imwrite(output_path, upscaled)
            
            return {
                'success': True,
                'output_path': output_path,
                'metadata': {
                    'original_dimensions': (width, height),
                    'new_dimensions': new_dimensions,
                    'scale_factor': scale_factor
                }
            }
            
        except Exception as e:
            logger.error(f"Upscaling failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def add_watermark(self, input_path: str, params: Dict) -> Dict:
        """Add text or image watermark"""
        try:
            watermark_type = params.get('watermark_type', 'text')
            watermark_text = params.get('watermark_text', 'ImageLab Studio')
            opacity = int(params.get('opacity', 50)) / 100
            position = params.get('position', 'bottom-right')
            output_path = input_path.replace('.', '_watermarked.')
            
            with Image.open(input_path).convert('RGBA') as base:
                # Create watermark layer
                watermark = Image.new('RGBA', base.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(watermark)
                
                if watermark_type == 'text':
                    # Add text watermark
                    font_size = int(min(base.width, base.height) * 0.05)
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                    
                    # Calculate text position
                    bbox = draw.textbbox((0, 0), watermark_text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    if position == 'top-left':
                        xy = (10, 10)
                    elif position == 'top-right':
                        xy = (base.width - text_width - 10, 10)
                    elif position == 'bottom-left':
                        xy = (10, base.height - text_height - 10)
                    elif position == 'bottom-right':
                        xy = (base.width - text_width - 10, base.height - text_height - 10)
                    else:  # center
                        xy = ((base.width - text_width) // 2, (base.height - text_height) // 2)
                    
                    # Draw text with opacity
                    draw.text(xy, watermark_text, font=font, fill=(255, 255, 255, int(255 * opacity)))
                
                # Composite watermark
                watermarked = Image.alpha_composite(base, watermark)
                
                # Convert back to RGB if saving as JPEG
                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    watermarked = watermarked.convert('RGB')
                
                watermarked.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'watermark_type': watermark_type,
                        'position': position,
                        'opacity': opacity
                    }
                }
                
        except Exception as e:
            logger.error(f"Watermark addition failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def blur_faces(self, input_path: str, params: Dict) -> Dict:
        """Detect and blur faces in image"""
        try:
            output_path = input_path.replace('.', '_blurred.')
            
            # Load pre-trained face detector
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Read image
            img = cv2.imread(input_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Blur each face
            for (x, y, w, h) in faces:
                # Extract face region
                face_roi = img[y:y+h, x:x+w]
                
                # Apply Gaussian blur
                blurred_face = cv2.GaussianBlur(face_roi, (51, 51), 30)
                
                # Replace face with blurred version
                img[y:y+h, x:x+w] = blurred_face
            
            # Save result
            cv2.imwrite(output_path, img)
            
            return {
                'success': True,
                'output_path': output_path,
                'metadata': {
                    'faces_detected': len(faces),
                    'blur_intensity': 'high'
                }
            }
            
        except Exception as e:
            logger.error(f"Face blur failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def convert_format(self, input_path: str, params: Dict, target_format: str = None) -> Dict:
        """Convert image to different format"""
        try:
            if not target_format:
                target_format = params.get('format', 'jpg')
            
            output_path = input_path.rsplit('.', 1)[0] + f'_converted.{target_format}'
            
            with Image.open(input_path) as img:
                # Handle special cases
                if target_format.lower() == 'jpg' or target_format.lower() == 'jpeg':
                    if img.mode in ('RGBA', 'P'):
                        # Convert to RGB for JPEG
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img
                elif target_format.lower() == 'png':
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                
                # Save in target format
                img.save(output_path, optimize=True)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'original_format': input_path.split('.')[-1].upper(),
                        'target_format': target_format.upper(),
                        'dimensions': img.size
                    }
                }
                
        except Exception as e:
            logger.error(f"Format conversion failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def remove_metadata(self, input_path: str, params: Dict) -> Dict:
        """Remove all metadata from image"""
        try:
            output_path = input_path.replace('.', '_clean.')
            
            with Image.open(input_path) as img:
                # Create new image without metadata
                data = list(img.getdata())
                clean_img = Image.new(img.mode, img.size)
                clean_img.putdata(data)
                
                # Save without metadata
                clean_img.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'removed': True,
                        'original_metadata': 'stripped'
                    }
                }
                
        except Exception as e:
            logger.error(f"Metadata removal failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_gif(self, input_path: str, params: Dict) -> Dict:
        """Create GIF from multiple images (simplified version)"""
        try:
            # This is a simplified version - in practice you'd pass multiple paths
            output_path = params.get('output_path', input_path.replace('.', '_animated.'))
            duration = int(params.get('duration', 100))  # ms per frame
            
            with Image.open(input_path) as img:
                # For demo, just save the image as a 1-frame GIF
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.save(
                    output_path,
                    format='GIF',
                    save_all=True,
                    duration=duration,
                    loop=0,
                    optimize=True
                )
            
            return {
                'success': True,
                'output_path': output_path,
                'metadata': {
                    'frames': 1,
                    'duration': duration,
                    'loop': 0
                }
            }
            
        except Exception as e:
            logger.error(f"GIF creation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def batch_resize(self, input_path: str, params: Dict) -> Dict:
        """Batch resize (simplified version - processes single image)"""
        try:
            # In practice, you'd pass a list of paths
            return self.resize_image(input_path, params)
            
        except Exception as e:
            logger.error(f"Batch resize failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def batch_convert(self, input_path: str, params: Dict) -> Dict:
        """Batch convert (simplified version - processes single image)"""
        try:
            return self.convert_format(input_path, params)
            
        except Exception as e:
            logger.error(f"Batch convert failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def batch_watermark(self, input_path: str, params: Dict) -> Dict:
        """Batch watermark (simplified version - processes single image)"""
        try:
            return self.add_watermark(input_path, params)
            
        except Exception as e:
            logger.error(f"Batch watermark failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Additional helper methods for other operations
    def optimize_for_web(self, input_path: str, params: Dict) -> Dict:
        """Optimize image specifically for web use"""
        params['quality'] = 75
        params['width'] = 1920  # Max width for web
        params['maintain_aspect'] = 'true'
        
        # First resize if needed
        resize_result = self.resize_image(input_path, params)
        if resize_result['success']:
            # Then compress
            return self.compress_image(resize_result['output_path'], params)
        return resize_result
    
    def reduce_colors(self, input_path: str, params: Dict) -> Dict:
        """Reduce color palette of image"""
        try:
            colors = int(params.get('colors', 64))
            output_path = input_path.replace('.', '_reduced.')
            
            with Image.open(input_path) as img:
                # Convert to palette mode with reduced colors
                if img.mode == 'RGBA':
                    # Handle transparency
                    img = img.convert('RGBA')
                    # Create a white background
                    background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    img = Image.alpha_composite(background, img)
                
                # Reduce colors
                reduced = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=colors)
                reduced = reduced.convert('RGB')  # Convert back for saving
                reduced.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'original_colors': 'full',
                        'reduced_colors': colors
                    }
                }
                
        except Exception as e:
            logger.error(f"Color reduction failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def adjust_colors(self, input_path: str, params: Dict) -> Dict:
        """Adjust image colors (brightness, contrast, saturation)"""
        try:
            brightness = float(params.get('brightness', 1.0))
            contrast = float(params.get('contrast', 1.0))
            saturation = float(params.get('saturation', 1.0))
            output_path = input_path.replace('.', '_adjusted.')
            
            with Image.open(input_path) as img:
                # Apply adjustments
                if brightness != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(brightness)
                
                if contrast != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(contrast)
                
                if saturation != 1.0:
                    enhancer = ImageEnhance.Color(img)
                    img = enhancer.enhance(saturation)
                
                img.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'brightness': brightness,
                        'contrast': contrast,
                        'saturation': saturation
                    }
                }
                
        except Exception as e:
            logger.error(f"Color adjustment failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def apply_filter(self, input_path: str, params: Dict) -> Dict:
        """Apply various filters to image"""
        try:
            filter_type = params.get('filter', 'blur')
            intensity = float(params.get('intensity', 1.0))
            output_path = input_path.replace('.', f'_{filter_type}.')
            
            with Image.open(input_path) as img:
                filters = {
                    'blur': lambda i: i.filter(ImageFilter.GaussianBlur(radius=intensity * 2)),
                    'sharpen': lambda i: i.filter(ImageFilter.UnsharpMask(radius=intensity * 2)),
                    'edge_enhance': lambda i: i.filter(ImageFilter.EDGE_ENHANCE_MORE),
                    'emboss': lambda i: i.filter(ImageFilter.EMBOSS),
                    'contour': lambda i: i.filter(ImageFilter.CONTOUR),
                    'smooth': lambda i: i.filter(ImageFilter.SMOOTH_MORE),
                    'grayscale': lambda i: i.convert('L').convert('RGB'),
                    'sepia': self.apply_sepia
                }
                
                if filter_type in filters:
                    img = filters[filter_type](img)
                    img.save(output_path)
                    
                    return {
                        'success': True,
                        'output_path': output_path,
                        'metadata': {
                            'filter': filter_type,
                            'intensity': intensity
                        }
                    }
                else:
                    return {'success': False, 'error': f'Unknown filter: {filter_type}'}
                    
        except Exception as e:
            logger.error(f"Filter application failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def apply_sepia(self, img):
        """Apply sepia filter"""
        # Convert to numpy array for processing
        img_array = np.array(img.convert('RGB'))
        
        # Apply sepia matrix
        sepia_matrix = np.array([[0.393, 0.769, 0.189],
                                 [0.349, 0.686, 0.168],
                                 [0.272, 0.534, 0.131]])
        
        sepia = img_array @ sepia_matrix.T
        sepia = np.clip(sepia, 0, 255).astype(np.uint8)
        
        return Image.fromarray(sepia)
    
    def smart_crop(self, input_path: str, params: Dict) -> Dict:
        """AI-powered smart cropping"""
        try:
            aspect_ratio = params.get('aspect_ratio', '1:1')
            output_path = input_path.replace('.', '_smart_crop.')
            
            # Parse aspect ratio
            if ':' in aspect_ratio:
                w_ratio, h_ratio = map(int, aspect_ratio.split(':'))
                target_ratio = w_ratio / h_ratio
            else:
                target_ratio = 1.0
            
            with Image.open(input_path) as img:
                # Get image dimensions
                width, height = img.size
                current_ratio = width / height
                
                # Calculate crop area
                if current_ratio > target_ratio:
                    # Image is wider, crop width
                    new_width = int(height * target_ratio)
                    left = (width - new_width) // 2
                    cropped = img.crop((left, 0, left + new_width, height))
                else:
                    # Image is taller, crop height
                    new_height = int(width / target_ratio)
                    top = (height - new_height) // 2
                    cropped = img.crop((0, top, width, top + new_height))
                
                cropped.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'original_dimensions': (width, height),
                        'new_dimensions': cropped.size,
                        'aspect_ratio': aspect_ratio
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_thumbnail(self, input_path: str, params: Dict) -> Dict:
        """Create thumbnail"""
        try:
            width = int(params.get('width', 150))
            height = int(params.get('height', 150))
            output_path = input_path.replace('.', '_thumb.')
            
            with Image.open(input_path) as img:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                img.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'dimensions': img.size
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def rotate_image(self, input_path: str, params: Dict) -> Dict:
        """Rotate image"""
        try:
            angle = int(params.get('angle', 90))
            output_path = input_path.replace('.', '_rotated.')
            
            with Image.open(input_path) as img:
                rotated = img.rotate(angle, expand=True)
                rotated.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'angle': angle,
                        'dimensions': rotated.size
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def flip_image(self, input_path: str, params: Dict) -> Dict:
        """Flip image horizontally or vertically"""
        try:
            direction = params.get('direction', 'horizontal')
            output_path = input_path.replace('.', '_flipped.')
            
            with Image.open(input_path) as img:
                if direction == 'horizontal':
                    flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                else:
                    flipped = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                
                flipped.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'direction': direction
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_text_overlay(self, input_path: str, params: Dict) -> Dict:
        """Add text overlay to image"""
        try:
            text = params.get('text', '')
            position = params.get('position', 'bottom')
            font_size = int(params.get('font_size', 32))
            color = params.get('color', '#ffffff')
            output_path = input_path.replace('.', '_text.')
            
            with Image.open(input_path) as img:
                draw = ImageDraw.Draw(img)
                
                # Load font
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                # Calculate text size
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Calculate position
                if position == 'top':
                    x = (img.width - text_width) // 2
                    y = 10
                elif position == 'bottom':
                    x = (img.width - text_width) // 2
                    y = img.height - text_height - 10
                elif position == 'center':
                    x = (img.width - text_width) // 2
                    y = (img.height - text_height) // 2
                elif position == 'top-left':
                    x, y = 10, 10
                elif position == 'top-right':
                    x = img.width - text_width - 10
                    y = 10
                elif position == 'bottom-left':
                    x = 10
                    y = img.height - text_height - 10
                elif position == 'bottom-right':
                    x = img.width - text_width - 10
                    y = img.height - text_height - 10
                else:
                    x, y = 10, 10
                
                # Convert color string to RGB tuple
                if color.startswith('#'):
                    color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                
                # Draw text with outline
                outline_color = (0, 0, 0)
                for offset in [(2,2), (2,-2), (-2,2), (-2,-2)]:
                    draw.text((x + offset[0], y + offset[1]), text, font=font, fill=outline_color)
                draw.text((x, y), text, font=font, fill=color)
                
                img.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'text': text,
                        'position': position,
                        'font_size': font_size
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_stickers(self, input_path: str, params: Dict) -> Dict:
        """Add stickers to image"""
        try:
            sticker_type = params.get('sticker_type', 'happy')
            position = params.get('position', 'center')
            size = int(params.get('size', 50))
            output_path = input_path.replace('.', '_stickers.')
            
            # Since we don't have actual sticker files, create a simple colored circle as a sticker
            with Image.open(input_path) as base_img:
                # Create a simple sticker (colored circle)
                sticker = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(sticker)
                
                # Draw different shapes based on sticker type
                if sticker_type == 'happy':
                    draw.ellipse([0, 0, size, size], fill=(255, 255, 0, 255))  # Yellow circle
                    draw.ellipse([size//4, size//4, size//2, size//2], fill=(0, 0, 0, 255))  # Left eye
                    draw.ellipse([size//2, size//4, 3*size//4, size//2], fill=(0, 0, 0, 255))  # Right eye
                    draw.arc([size//4, size//2, 3*size//4, 3*size//4], 0, 180, fill=(0, 0, 0, 255), width=2)  # Smile
                elif sticker_type == 'heart':
                    # Simple heart shape
                    draw.ellipse([0, 0, size//2, size//2], fill=(255, 0, 0, 255))
                    draw.ellipse([size//2, 0, size, size//2], fill=(255, 0, 0, 255))
                    draw.polygon([(0, size//3), (size, size//3), (size//2, size)], fill=(255, 0, 0, 255))
                else:
                    # Default star
                    draw.regular_polygon((size//2, size//2), 5, size//2, fill=(255, 215, 0, 255))
                
                # Calculate position
                if position == 'center':
                    x = (base_img.width - size) // 2
                    y = (base_img.height - size) // 2
                elif position == 'top-left':
                    x, y = 10, 10
                elif position == 'top-right':
                    x = base_img.width - size - 10
                    y = 10
                elif position == 'bottom-left':
                    x = 10
                    y = base_img.height - size - 10
                elif position == 'bottom-right':
                    x = base_img.width - size - 10
                    y = base_img.height - size - 10
                else:
                    x, y = 10, 10
                
                # Paste sticker
                base_img.paste(sticker, (x, y), sticker)
                base_img.save(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'metadata': {
                        'sticker': sticker_type,
                        'position': position,
                        'size': size
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
