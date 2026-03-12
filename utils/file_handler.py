import os
import shutil
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import threading
import time
import logging

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, upload_folder, max_age=3600, cleanup_interval=3600):
        self.upload_folder = upload_folder
        self.max_age = max_age
        self.cleanup_interval = cleanup_interval
        
        # Create upload folder if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        # Start cleanup thread
        self.start_cleanup_thread()
    
    def save_upload(self, file, file_id=None):
        """Save uploaded file to temporary storage"""
        if not file_id:
            file_id = str(uuid.uuid4())
        
        # Get file extension
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        # Create unique filename
        unique_filename = f"{file_id}_{filename}"
        filepath = os.path.join(self.upload_folder, unique_filename)
        
        # Save file
        file.save(filepath)
        
        # Store metadata
        self.store_metadata(file_id, {
            'original_name': filename,
            'filepath': filepath,
            'size': os.path.getsize(filepath),
            'upload_time': datetime.now().isoformat(),
            'extension': ext
        })
        
        return filepath
    
    def store_metadata(self, file_id, metadata):
        """Store file metadata"""
        metadata_file = os.path.join(self.upload_folder, f"{file_id}.json")
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
    
    def get_metadata(self, file_id):
        """Retrieve file metadata"""
        metadata_file = os.path.join(self.upload_folder, f"{file_id}.json")
        if os.path.exists(metadata_file):
            import json
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None
    
    def cleanup(self, file_id=None):
        """Clean up temporary files"""
        try:
            if file_id:
                # Clean specific file
                metadata = self.get_metadata(file_id)
                if metadata:
                    filepath = metadata.get('filepath')
                    if filepath and os.path.exists(filepath):
                        os.remove(filepath)
                    
                    metadata_file = os.path.join(self.upload_folder, f"{file_id}.json")
                    if os.path.exists(metadata_file):
                        os.remove(metadata_file)
            else:
                # Clean all old files
                self.cleanup_old_files()
                
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    def cleanup_old_files(self):
        """Remove files older than max_age"""
        try:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.max_age)
            
            for filename in os.listdir(self.upload_folder):
                if filename.endswith('.json'):
                    continue
                    
                filepath = os.path.join(self.upload_folder, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if file_time < cutoff:
                    os.remove(filepath)
                    
                    # Remove associated metadata
                    metadata_file = filepath + '.json'
                    if os.path.exists(metadata_file):
                        os.remove(metadata_file)
                        
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    def start_cleanup_thread(self):
        """Start background thread for cleanup"""
        def cleanup_worker():
            while True:
                time.sleep(self.cleanup_interval)
                self.cleanup_old_files()
        
        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
