import datetime
import logging
import os
from typing import Dict, List, Optional, Union, Any

import markdown2
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from serpapi import GoogleSearch
from langchain_community.tools import GmailSendMessage
from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.utils import build_resource_service
from google.oauth2.credentials import Credentials
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, PyMongoError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize credentials
creds = Credentials(
    token=os.getenv("GOOGLE_TOKEN"),
    refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
    token_uri=os.getenv("token_uri"),
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scopes=["https://mail.google.com/"]
)

# Setup Gmail API resource
api_resource = build_resource_service(credentials=creds)
toolkit = GmailToolkit(api_resource=api_resource)

# MongoDB connection pool
try:
    mongo_client = MongoClient(os.getenv("mongodb_uri"), server_api=ServerApi("1"))
    # Test the connection
    mongo_client.admin.command('ping')
    logger.info("MongoDB connection established successfully")
except ConnectionFailure as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    mongo_client = None

def search(search_query: str, custom_tbs: str = "cdr:1,cd_min:4/6/2025,cd_max:4/21/2025,sbd:1") -> Dict[str, Any]:
    """
    Search for specific podcasts using Google Search API.
    
    Args:
        search_query: The search term to look for
        custom_tbs: Time-Based Search filters in Google search URLs
        
    Returns:
        Dict containing search results or error information
    """
    try:
        params = {
            "engine": "google",
            "q": search_query,
            "api_key": os.environ["serpapi_key"],
            "num": 5,
            "tbs": custom_tbs,
            "tbm": "vid"
        }

        query = GoogleSearch(params)
        results = query.get_dict()
        return {"messages": results, "status": "success"}
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {"status": "error", "error": str(e)}

def transcribe(youtube_id: str) -> Dict[str, Any]:
    """
    Transcribe a YouTube video.
    
    Args:
        youtube_id: ID of a YouTube video
        
    Returns:
        Dict containing the transcription text or error information
    """
    try:
        transcriptions = YouTubeTranscriptApi.get_transcript(youtube_id)
        all_text = [x["text"] for x in transcriptions]
        all_text = ' '.join(all_text)
        return {"text": all_text, "status": "success"}
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logger.warning(f"Transcript not available for video {youtube_id}: {str(e)}")
        return {"status": "error", "error": f"Transcript not available: {str(e)}"}
    except Exception as e:
        logger.error(f"Transcription error for video {youtube_id}: {str(e)}")
        return {"status": "error", "error": str(e)}

def get_today_date() -> str:
    """
    Get the current date and time formatted as a string.
    
    Returns:
        Current datetime as string
    """
    return datetime.datetime.now().isoformat()

def send_email(message: str, subject: str) -> Dict[str, Any]:
    """
    Send an email with the provided message and subject.
    
    Args:
        message: Email message content (markdown format)
        subject: Email subject line
        
    Returns:
        Dict containing status information about the email sending process
    """
    try:
        recipient = os.getenv("EMAIL_RECIPIENT", "omaratef3221@gmail.com")
        html_content = markdown2.markdown(message)
        tool = GmailSendMessage(api_resource=api_resource)
        result = tool.run({
            "to": recipient,
            "subject": subject,
            "message": html_content,
            "is_html": True
        })
        logger.info(f"Email sent successfully to {recipient}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {"status": "error", "error": str(e)}

def insert_to_mongodb(
    episode_id: str,
    podcast_title: str,
    podcast_description: str,
    podcast_url: str,
    podcast_summary: str,
    length: Optional[str] = None,
    is_new: bool = True
) -> Dict[str, Any]:
    """
    Insert a structured podcast summary into MongoDB.

    Args:
        episode_id: Unique ID of the episode (e.g., YouTube video ID or custom index)
        podcast_title: Full title of the podcast or video
        podcast_description: Description or caption of the episode
        podcast_url: Direct URL to the episode (e.g., YouTube link)
        podcast_summary: Markdown-formatted summary of the episode
        length: Duration of the episode in HH:MM or MM:SS format
        is_new: Flag to mark the record as newly generated (default: True)
    
    Returns:
        Dict containing status information about the database operation

    Example inserted document:
        {
            "episode_id": "856",
            "podcast_title": "The Fastest-Growing Jobs Are AI Jobs",
            "podcast_description": "Interview with Jon Krohn...",
            "podcast_url": "https://www.youtube.com/watch?v=J5CDDV0QdlA",
            "podcast_summary": "### Summary\n- Bullet point 1\n- Bullet point 2",
            "length": "9:49",
            "database_record_date": "2025-02-13T00:11:29.374+00:00",
            "is_new": true,
            "message": "Podcast summary successfully generated and stored in Mongo Database"
        }
    """
    if mongo_client is None:
        logger.error("MongoDB client is not initialized")
        return {"status": "error", "error": "MongoDB connection not available"}
    
    try:
        db = mongo_client.podcast_agent_results
        collection = db.podcast_summaries

        record = {
            "episode_id": episode_id,
            "podcast_title": podcast_title,
            "podcast_description": podcast_description,
            "podcast_url": podcast_url,
            "podcast_summary": podcast_summary,
            "length": length,
            "database_record_date": datetime.datetime.now().isoformat(),
            "is_new": is_new,
            "message": "Podcast summary successfully generated and stored in Mongo Database"
        }

        result = collection.insert_one(record)
        logger.info(f"Successfully inserted document with ID: {result.inserted_id}")
        return {
            "status": "success", 
            "inserted_id": str(result.inserted_id),
            "message": "Podcast summary stored successfully"
        }
    except PyMongoError as e:
        logger.error(f"MongoDB operation error: {str(e)}")
        return {"status": "error", "error": f"Database error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error during database operation: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}

# List of available tools
tools = [search, transcribe, get_today_date, send_email, insert_to_mongodb]
