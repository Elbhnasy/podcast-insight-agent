import os
import logging
import time
from typing import Dict, Any, Tuple, Optional

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, InternalServerError
from dotenv import load_dotenv

# Fix the import path
try:
    from src.api.retriever import retrieve_and_respond, llm
except ImportError:
    # Handle relative import when running as module
    from retriever import retrieve_and_respond, llm

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Add CORS support for frontend integration

# API configuration
DEFAULT_PORT = 5000
API_VERSION = "v1"
PREFIX = f"/api/{API_VERSION}"

@app.route(f'{PREFIX}/chat', methods=['POST'])
def chat() -> Response:
    """
    Process a chat query about podcasts and return AI-generated insights.
    
    Expects JSON input with format: {"message": "your question here"}
    Returns JSON with AI response and source metadata.
    
    Returns:
        Flask response containing the AI response and podcast metadata
    """
    try:
        # Track execution time
        start_time = time.time()
        
        # Validate request data
        if not request.is_json:
            logger.warning("Invalid request: Content-Type is not JSON")
            return jsonify({
                "status": "error",
                "message": "Request must be JSON"
            }), 400
            
        data = request.get_json()
        if not data or 'message' not in data:
            logger.warning("Invalid request: Missing 'message' field")
            return jsonify({
                "status": "error",
                "message": "Request must include 'message' field"
            }), 400
            
        question = data.get('message', '')
        if not question or not isinstance(question, str):
            logger.warning("Invalid request: 'message' must be a non-empty string")
            return jsonify({
                "status": "error",
                "message": "'message' must be a non-empty string"
            }), 400
        
        # Process the query
        logger.info(f"Processing query: {question[:50]}{'...' if len(question) > 50 else ''}")
        response, metadata_list = retrieve_and_respond(question, llm)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        logger.info(f"Query processed in {execution_time:.2f}s")
        
        return jsonify({
            "status": "success",
            "data": {
                "response": response,
                "metadata": metadata_list,
                "processing_time": f"{execution_time:.2f}s"
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "error": str(e) if os.getenv('ENVIRONMENT') == 'development' else None
        }), 500

@app.route(f'{PREFIX}/health', methods=['GET'])
def health() -> Response:
    """
    Health check endpoint to verify API is running.
    
    Returns:
        Flask response with status information
    """
    return jsonify({
        "status": "ok",
        "version": API_VERSION,
        "service": "podcast-insight-agent"
    }), 200

@app.errorhandler(404)
def not_found(e) -> Response:
    """Handle 404 errors."""
    return jsonify({
        "status": "error",
        "message": "The requested resource was not found"
    }), 404

@app.errorhandler(500)
def server_error(e) -> Response:
    """Handle 500 errors."""
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

def create_app() -> Flask:
    """
    Create and configure the Flask application.
    
    Returns:
        Configured Flask application
    """
    return app

if __name__ == '__main__':
    port = int(os.getenv('PORT', DEFAULT_PORT))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    logger.info(f"Starting Podcast Insight Agent API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)