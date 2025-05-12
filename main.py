import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional, List

# Enable environment variables
from dotenv import load_dotenv
load_dotenv()

# Import core components
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

# Import project modules (using proper project structure)
try:
    from src.agent import graph
    from src.vectorstore import insert_to_vector_db, get_latest_podcast, sync_latest_podcasts
except ImportError:
    # Fallback for direct script execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent import graph
    from vectorstore import insert_to_vector_db, get_latest_podcast, sync_latest_podcasts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = RunnableConfig(recursion_limit=15)

def generate_insights(query: str, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    Generate insights from podcasts based on the provided query.
    
    Args:
        query: Search query or topic for podcast analysis
        config: Optional LangChain runnable configuration
        
    Returns:
        Dict containing the agent's response events
    """
    if not config:
        config = DEFAULT_CONFIG
        
    try:
        messages = [HumanMessage(content=query)]
        logger.info(f"Generating insights for query: {query}")
        
        events = graph.invoke({'messages': messages}, config=config)
        logger.info("Successfully generated insights")
        
        return events
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}", exc_info=True)
        raise

def sync_to_vector_db(podcast_limit: int = 1) -> Dict[str, Any]:
    """
    Sync the latest podcasts to the vector database.
    
    Args:
        podcast_limit: Number of recent podcasts to synchronize
        
    Returns:
        Dict containing synchronization results
    """
    try:
        logger.info(f"Fetching {podcast_limit} latest podcasts for vector DB sync")
        
        # Use the enhanced sync function from the improved vectorstore module
        result = sync_latest_podcasts(podcast_limit)
        
        logger.info(f"Vector DB sync complete: {result['message']}")
        return result
    except Exception as e:
        logger.error(f"Error during vector DB sync: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e), "synced": 0}

def main():
    """Main application entry point with command-line argument handling."""
    parser = argparse.ArgumentParser(
        description='Podcast Insight Agent - Discover and analyze AI podcast content'
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Generate insights from podcasts')
    query_parser.add_argument('--message', '-m', type=str, required=True,
                                help='Query or topic to analyze')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync podcasts to vector database')
    sync_parser.add_argument('--limit', '-l', type=int, default=1,
                            help='Number of recent podcasts to sync (default: 1)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default to query if no command specified
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the appropriate command
    try:
        if args.command == 'query':
            events = generate_insights(args.message)
            print(f"Generated insights for query: '{args.message}'")
            # Print the last event content for CLI usage
            if events and events.get('messages'):
                last_message = events['messages'][-1]
                print("\nResponse:")
                print(last_message.content)
                
        elif args.command == 'sync':
            result = sync_to_vector_db(args.limit)
            print(f"Vector DB sync result: {result['message']}")
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
