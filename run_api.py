
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Import here to ensure environment variables are loaded first
    from src.api import create_app
    
    # Set host and port from environment or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    
    print(f"Starting Podcast Insight Agent API on {host}:{port}")
    app = create_app()
    app.run(host=host, port=port, debug=debug)
