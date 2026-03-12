import os
from PIL import Image
import magic

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff", "heic"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_image(file):
    """Validate uploaded image file"""
    try:
        if not file:
            return False, "No file provided"

        # -----------------------
        # Check file size
        # -----------------------
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)

        if size > MAX_FILE_SIZE:
            return False, f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024}MB"

        # -----------------------
        # Validate filename
        # -----------------------
        filename = getattr(file, "filename", None)

        if not filename:
            return False, "Invalid filename"

        if "." not in filename:
            return False, "Missing file extension"

        ext = filename.rsplit(".", 1)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

        # -----------------------
        # Validate MIME type
        # -----------------------
        try:
            header = file.read(2048)
            mime = magic.from_buffer(header, mime=True)
            file.seek(0)

            if not mime.startswith("image/"):
                return False, "File is not a valid image"
        except Exception:
            file.seek(0)

        # -----------------------
        # Validate with PIL
        # -----------------------
        try:
            img = Image.open(file)
            img.verify()
            file.seek(0)

            # reopen to ensure it's loadable
            img = Image.open(file)
            img.load()
            file.seek(0)

        except Exception:
            return False, "Corrupted or unsupported image file"

        return True, None

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def validate_params(params, required_params):
    """Validate required parameters"""
    missing = [p for p in required_params if p not in params]

    if missing:
        return False, f"Missing parameters: {', '.join(missing)}"

    return True, None


def sanitize_filename(filename):
    """Sanitize filename for security"""
    if not filename:
        return "file"

    # Remove path traversal
    filename = filename.replace("/", "_").replace("\\", "_")

    # Keep printable characters
    filename = "".join(c for c in filename if c.isprintable())

    # Limit length
    if len(filename) > 255:
        if "." in filename:
            name, ext = filename.rsplit(".", 1)
            filename = name[:250] + "." + ext
        else:
            filename = filename[:255]

    return filename
