import hashlib
import hmac
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.key = self.load_or_create_key()
        self.cipher = Fernet(self.key)
    
    def load_or_create_key(self):
        """Load or create encryption key"""
        key_file = 'secret.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_image(self, image_data, password=None):
        """Encrypt image data"""
        try:
            if password:
                # Password-based encryption
                salt = os.urandom(16)
                kdf = PBKDF2(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                cipher = Fernet(key)
                encrypted = cipher.encrypt(image_data)
                return salt + encrypted
            else:
                # Key-based encryption
                return self.cipher.encrypt(image_data)
                
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt_image(self, encrypted_data, password=None):
        """Decrypt image data"""
        try:
            if password:
                # Password-based decryption
                salt = encrypted_data[:16]
                actual_data = encrypted_data[16:]
                
                kdf = PBKDF2(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
                cipher = Fernet(key)
                return cipher.decrypt(actual_data)
            else:
                # Key-based decryption
                return self.cipher.decrypt(encrypted_data)
                
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def hash_image(self, image_data):
        """Create hash of image data"""
        return hashlib.sha256(image_data).hexdigest()
    
    def verify_integrity(self, image_data, hash_value):
        """Verify image integrity using hash"""
        return self.hash_image(image_data) == hash_value
