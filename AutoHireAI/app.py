import os
import logging
from flask import Flask
from routes.views import views_bp
from routes.api_routes import api_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Register blueprints
app.register_blueprint(views_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Set upload folder configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Log application startup
logger.info("Recruitment Assistant API initialized")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)