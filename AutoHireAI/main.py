
from app import app

# This allows the app to be run directly or through gunicorn
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
