import os
import sys
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"scheduled_job_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

def run_podcast_discovery():
    """Find and analyze new podcasts."""
    from src.main import generate_insights
    
    # Default search query from environment or use a reasonable default
    query = os.getenv("PODCAST_SEARCH_QUERY", "latest AI advancements podcast")
    
    logger.info(f"Running scheduled podcast discovery with query: {query}")
    
    try:
        result = generate_insights(query)
        logger.info("Podcast discovery completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during podcast discovery: {str(e)}", exc_info=True)
        return False

def run_vector_sync():
    """Sync recent podcasts to vector database."""
    from src.main import sync_to_vector_db
    
    # Get sync limit from environment or use default
    sync_limit = int(os.getenv("SCHEDULED_SYNC_LIMIT", "5"))
    
    logger.info(f"Running scheduled vector DB sync for {sync_limit} podcasts")
    
    try:
        result = sync_to_vector_db(sync_limit)
        logger.info(f"Vector sync completed: {result['message']}")
        return result["status"] == "success"
    except Exception as e:
        logger.error(f"Error during vector sync: {str(e)}", exc_info=True)
        return False

def run_email_summary():
    """Generate and send email summary of recent podcasts."""
    # This would call your email functionality
    from src.utils import send_email
    
    # Get recipient from environment
    recipient = os.getenv("EMAIL_RECIPIENT")
    if not recipient:
        logger.error("EMAIL_RECIPIENT not set in environment")
        return False
    
    logger.info(f"Generating email summary for {recipient}")
    
    try:
        # Generate summary and send email
        # This is a simplified example - you would need to implement the actual summary generation
        subject = f"AI Podcast Insights Summary - {datetime.now().strftime('%Y-%m-%d')}"
        message = "# Latest AI Podcast Insights\n\nThis is a placeholder for your automated podcast summary."
        
        # This assumes your send_email has been updated to return a status dictionary
        result = send_email(message, subject)
        logger.info(f"Email summary sent: {result.get('status', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Error sending email summary: {str(e)}", exc_info=True)
        return False

def main():
    """Run all scheduled jobs or a specific job."""
    parser = argparse.ArgumentParser(description='Run scheduled jobs for Podcast Insight Agent')
    parser.add_argument('--job', choices=['all', 'discover', 'sync', 'email'], default='all',
                      help='Specific job to run (default: all)')
    
    args = parser.parse_args()
    
    # Run the specified job(s)
    if args.job in ('all', 'discover'):
        run_podcast_discovery()
    
    if args.job in ('all', 'sync'):
        run_vector_sync()
    
    if args.job in ('all', 'email'):
        run_email_summary()

if __name__ == "__main__":
    logger.info("Starting scheduled jobs")
    main()
    logger.info("Scheduled jobs completed")
