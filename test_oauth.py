
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow HTTP for localhost

from app import app

if __name__ == '__main__':
    # Run with debug mode to see errors
    app.run(debug=True, host='0.0.0.0', port=5000)
