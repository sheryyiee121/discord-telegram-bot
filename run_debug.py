import os
import sys

# Enable debug output
os.environ['FLASK_DEBUG'] = '1'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
from app import app

if __name__ == '__main__':
    print("Starting Flask app with debug mode...")
    print("Navigate to http://localhost:5000")
    print("-" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
