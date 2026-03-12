# Routes package initializer
from flask import Blueprint

# Create blueprints
optimize_bp = Blueprint('optimize', __name__, url_prefix='/api/optimize')
create_bp = Blueprint('create', __name__, url_prefix='/api/create')
edit_bp = Blueprint('edit', __name__, url_prefix='/api/edit')
convert_bp = Blueprint('convert', __name__, url_prefix='/api/convert')
security_bp = Blueprint('security', __name__, url_prefix='/api/security')
batch_bp = Blueprint('batch', __name__, url_prefix='/api/batch')

# Import routes to register them
from . import optimize, create, edit, convert, security, batch
