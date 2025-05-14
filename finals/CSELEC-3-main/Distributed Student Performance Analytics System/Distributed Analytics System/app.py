import os
# Set Python to unbuffered mode
os.environ['PYTHONUNBUFFERED'] = '1'

from app_factory import create_app
import sys

app = create_app()

if __name__ == '__main__':
    # Force flush of stdout
    sys.stdout.reconfigure(line_buffering=True)
    
    # Enable debug mode and set use_reloader to False to avoid duplicate logs
    port = int(os.getenv('PORT', 5000))
    print("\nStarting Flask server...", flush=True)
    print("Server will be available at http://localhost:5000", flush=True)
    print("Press Ctrl+C to stop the server\n", flush=True)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        use_reloader=False  # Disable reloader to avoid duplicate logs
    )