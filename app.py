from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import uuid
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger(__name__)

# Import modules safely
try:
    from config import Config
    logger.info("✓ Config module loaded")
except Exception as e:
    logger.error(f"✗ Failed to load Config: {str(e)}")
    raise

try:
    from utils.image_processor import ImageProcessor
    from utils.file_handler import FileHandler
    from utils.validators import validate_image
    from utils.security import SecurityManager
    logger.info("✓ Utils modules loaded")
except Exception as e:
    logger.error(f"✗ Failed to load utils modules: {str(e)}")
    raise

try:
    from routes.optimize import optimize_bp
    from routes.create import create_bp
    from routes.edit import edit_bp
    from routes.convert import convert_bp
    from routes.security import security_bp
    from routes.batch import batch_bp
    logger.info("✓ Route blueprints loaded")
except Exception as e:
    logger.error(f"✗ Failed to load route blueprints: {str(e)}")
    raise

# Initialize Flask
app = Flask(__name__)

# Load config
try:
    app.config.from_object(Config)
    logger.info("✓ Configuration loaded")
except Exception:
    logger.warning("Using fallback configuration")

    app.config["DEBUG"] = False
    app.config["UPLOAD_FOLDER"] = "static/uploads"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
    app.config["ALLOWED_EXTENSIONS"] = {"png","jpg","jpeg","gif","webp","bmp","tiff","heic"}
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY","dev-secret-key")

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET","POST","PUT","DELETE","OPTIONS"],
        "allow_headers": ["Content-Type","Authorization"]
    }
})

# Ensure directories exist
def create_directories():
    dirs = [
        app.config.get("UPLOAD_FOLDER","static/uploads"),
        "logs",
        "static"
    ]

    for d in dirs:
        try:
            Path(d).mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Directory ensured: {d}")
        except Exception as e:
            logger.error(f"Directory error {d}: {e}")

create_directories()

# Initialize utilities
upload_folder = app.config.get("UPLOAD_FOLDER","static/uploads")

image_processor = ImageProcessor()
file_handler = FileHandler(upload_folder)
security_manager = SecurityManager()

logger.info("✓ Utilities initialized")

# Register blueprints (WITHOUT prefix duplication)
app.register_blueprint(optimize_bp)
app.register_blueprint(create_bp)
app.register_blueprint(edit_bp)
app.register_blueprint(convert_bp)
app.register_blueprint(security_bp)
app.register_blueprint(batch_bp)

logger.info("✓ Blueprints registered")

# Startup check
def startup_check():

    logger.info("="*50)
    logger.info("ImageLab Backend Starting")

    logger.info(f"Environment: {os.environ.get('FLASK_ENV','production')}")
    logger.info(f"Upload folder: {app.config.get('UPLOAD_FOLDER')}")
    logger.info(f"Max upload size: {app.config.get('MAX_CONTENT_LENGTH')}")

    upload_dir = Path(app.config.get("UPLOAD_FOLDER"))

    try:
        test_file = upload_dir / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        logger.info("✓ Upload folder writable")
    except Exception as e:
        logger.error(f"Upload folder error: {e}")

    logger.info("="*50)

# Run startup checks (Flask 3 compatible)
with app.app_context():
    startup_check()

# Root endpoint
@app.route("/")
def index():

    try:
        return render_template("index.html")
    except:
        return jsonify({
            "name":"ImageLab API",
            "version":"1.0.0",
            "status":"running"
        })

# Health check
@app.route("/api/health")
def health():

    return jsonify({
        "status":"healthy",
        "time":datetime.now().isoformat()
    })

# Test endpoint
@app.route("/api/test")
def test():

    return jsonify({
        "message":"API working",
        "time":datetime.now().isoformat()
    })

# Image processing endpoint
@app.route("/api/process", methods=["POST","OPTIONS"])
def process_image():

    if request.method == "OPTIONS":
        return "",200

    file_id = None

    try:

        if "image" not in request.files:
            return jsonify({"error":"No image uploaded"}),400

        file = request.files["image"]
        operation = request.form.get("operation","")
        params = request.form.to_dict()

        logger.info(f"Request: {operation} | file={file.filename}")

        valid,error = validate_image(file)

        if not valid:
            return jsonify({"error":error}),400

        file_id = str(uuid.uuid4())

        input_path = file_handler.save_upload(file,file_id)

        result = image_processor.process(operation,input_path,params)

        if not result["success"]:
            return jsonify({"error":result.get("error","processing failed")}),500

        filename = secure_filename(file.filename)

        return send_file(
            result["output_path"],
            as_attachment=True,
            download_name=f"processed_{filename}",
            mimetype="image/jpeg"
        )

    except Exception as e:

        logger.error(f"Processing error: {e}",exc_info=True)

        return jsonify({"error":"internal server error"}),500

    finally:

        if file_id:
            try:
                file_handler.cleanup(file_id)
            except:
                pass


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error":"endpoint not found"}),404

@app.errorhandler(500)
def internal(e):
    logger.error(str(e))
    return jsonify({"error":"internal server error"}),500

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error":"file too large (50MB max)"}),413

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error":"method not allowed"}),405


# Local run
if __name__ == "__main__":

    port = int(os.environ.get("PORT",5000))
    debug = os.environ.get("FLASK_DEBUG","false").lower()=="true"

    logger.info(f"Starting server on port {port}")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        threaded=True
    )
