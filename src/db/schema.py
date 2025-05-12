from typing import Dict, Any
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.collection import Collection
from pymongo.database import Database
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection() -> MongoClient:
    """Get a connection to the MongoDB database."""
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise EnvironmentError("MONGODB_URI environment variable is not set")
    
    return MongoClient(mongodb_uri)

def get_podcast_collection() -> Collection:
    """Get the podcast summaries collection with proper schema and indexes."""
    client = get_db_connection()
    db = client.podcast_agent_results
    collection = db.podcast_summaries
    
    # Create indexes if they don't exist
    try:
        # Create a text index for searching
        collection.create_index([("podcast_title", TEXT), ("podcast_summary", TEXT)])
        
        # Create an index on episode_id for lookups
        collection.create_index([("episode_id", ASCENDING)], unique=True)
        
        # Create an index on database_record_date for sorting
        collection.create_index([("database_record_date", ASCENDING)])
        
        logger.info("MongoDB indexes created or already exist")
    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {str(e)}")
    
    return collection

# Schema definition (for documentation and validation)
PODCAST_SCHEMA = {
    "episode_id": str,  # Unique identifier for the episode
    "podcast_title": str,  # Full title of the podcast
    "podcast_description": str,  # Description or caption
    "podcast_url": str,  # URL to the podcast
    "podcast_summary": str,  # Markdown-formatted summary
    "length": str,  # Duration in format HH:MM:SS
    "database_record_date": str,  # ISO format date
    "is_new": bool,  # Flag to mark as newly generated
}

# Function to validate podcast documents against schema
def validate_podcast_document(document: Dict[str, Any]) -> bool:
    """
    Validate a podcast document against the schema.
    
    Args:
        document: Podcast document to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["episode_id", "podcast_title", "podcast_url", "podcast_summary"]
    
    # Check required fields
    for field in required_fields:
        if field not in document:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate field types where possible
    if not isinstance(document.get("episode_id", ""), str):
        logger.error("episode_id must be a string")
        return False
        
    if not isinstance(document.get("podcast_title", ""), str):
        logger.error("podcast_title must be a string")
        return False
    
    return True
