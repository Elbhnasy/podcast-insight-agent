import os
import logging
import time
from typing import Dict, Any, List, Optional, Iterator, Union

from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, PyMongoError
from pinecone import Pinecone, ServerlessSpec
from pinecone.core.exceptions import PineconeException
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration with environment variable fallbacks
MONGODB_URI = os.getenv("mongodb_uri")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "podcast-summaries")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "summaries")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIMENSION = 3072  # text-embedding-3-large dimension

# Initialize MongoDB connection
try:
    mongo_client = MongoClient(MONGODB_URI, server_api=ServerApi("1"))
    # Test connection
    mongo_client.admin.command('ping')
    logger.info("MongoDB connection established successfully")
    db = mongo_client.podcast_agent_results
    collection = db.podcast_summaries
except ConnectionFailure as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    mongo_client = None
    db = None
    collection = None

# Initialize Pinecone connection and create index if needed
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    spec = ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION)
    
    # Check if index exists, create if not
    existing_indexes = [i.name for i in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing_indexes:
        logger.info(f"Creating new Pinecone index: {PINECONE_INDEX_NAME}")
        pc.create_index(
            name=PINECONE_INDEX_NAME, 
            dimension=EMBEDDING_DIMENSION, 
            metric="cosine", 
            spec=spec
        )
        logger.info(f"Index {PINECONE_INDEX_NAME} created successfully")
    else:
        logger.info(f"Using existing Pinecone index: {PINECONE_INDEX_NAME}")
    
    # Initialize embeddings model
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
except PineconeException as e:
    logger.error(f"Pinecone initialization error: {str(e)}")
    pc = None
    embeddings = None
except Exception as e:
    logger.error(f"Error during initialization: {str(e)}")
    pc = None
    embeddings = None

def get_latest_podcast(limit: int = 1) -> Iterator[Dict[str, Any]]:
    """
    Retrieve the latest podcast(s) from MongoDB.
    
    Args:
        limit: Number of recent podcasts to retrieve
        
    Returns:
        Iterator of podcast documents
        
    Raises:
        PyMongoError: If database operation fails
    """
    try:
        if not mongo_client:
            logger.error("MongoDB client is not initialized")
            return []
            
        latest_podcasts = collection.find().sort([("database_record_date", -1)]).limit(limit)
        return latest_podcasts
    except PyMongoError as e:
        logger.error(f"Error retrieving latest podcasts: {str(e)}")
        return []

def prepare_document(podcast: Dict[str, Any]) -> Optional[Document]:
    """
    Prepare a LangChain Document from a podcast record.
    
    Args:
        podcast: MongoDB podcast document
        
    Returns:
        LangChain Document object ready for vectorization
    """
    if not podcast:
        logger.warning("Empty podcast record provided")
        return None
        
    try:
        # Extract metadata (exclude large text fields and MongoDB ID)
        metadata = {
            k: v for k, v in podcast.items()
            if k not in {"_id", "podcast_summary", "podcast_transcript"}
        }
        
        # Create document with podcast summary as content
        return Document(
            page_content=podcast["podcast_summary"],
            metadata=metadata
        )
    except KeyError as e:
        logger.error(f"Missing required field in podcast record: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error preparing document: {str(e)}")
        return None

def insert_to_vector_db(podcast: Dict[str, Any], 
                        retry_attempts: int = 3, 
                        retry_delay: float = 2.0) -> bool:
    """
    Insert a podcast summary into Pinecone vector database.
    
    Args:
        podcast: MongoDB podcast document
        retry_attempts: Number of retry attempts on failure
        retry_delay: Delay between retries in seconds
        
    Returns:
        Success status as boolean
    """
    if not podcast:
        logger.warning("No podcast provided for vector insertion")
        return False
        
    if not pc or not embeddings:
        logger.error("Pinecone or embeddings not initialized")
        return False
    
    doc = prepare_document(podcast)
    if not doc:
        return False
    
    # Attempt insertion with retries
    for attempt in range(retry_attempts):
        try:
            vector_store = PineconeVectorStore.from_documents(
                documents=[doc],
                index_name=PINECONE_INDEX_NAME,
                embedding=embeddings,
                namespace=PINECONE_NAMESPACE
            )
            logger.info(f"Successfully inserted podcast '{podcast.get('podcast_title', 'Unknown')}' into Pinecone")
            return True
            
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/{retry_attempts} failed: {str(e)}")
            if attempt < retry_attempts - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to insert podcast into vector database after {retry_attempts} attempts")
                return False

def sync_latest_podcasts(count: int = 5) -> Dict[str, Any]:
    """
    Synchronize the latest podcasts from MongoDB to Pinecone.
    
    Args:
        count: Number of latest podcasts to synchronize
        
    Returns:
        Dictionary with sync results
    """
    if not mongo_client or not pc:
        logger.error("Database connections not initialized")
        return {"status": "error", "message": "Database connections not initialized", "synced": 0}
    
    latest_podcasts = list(get_latest_podcast(limit=count))
    
    if not latest_podcasts:
        logger.info("No podcasts found to synchronize")
        return {"status": "success", "message": "No podcasts to synchronize", "synced": 0}
    
    success_count = 0
    for podcast in latest_podcasts:
        if insert_to_vector_db(podcast):
            success_count += 1
    
    result = {
        "status": "success" if success_count > 0 else "partial" if success_count > 0 else "error",
        "message": f"Synchronized {success_count}/{len(latest_podcasts)} podcasts",
        "synced": success_count
    }
    
    logger.info(result["message"])
    return result

# Example function to perform a semantic search (added functionality)
def semantic_search(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Perform semantic search on podcast summaries.
    
    Args:
        query: Search query text
        top_k: Number of top results to return
        
    Returns:
        List of matching podcast summaries with similarity scores
    """
    if not pc or not embeddings:
        logger.error("Pinecone or embeddings not initialized")
        return []
    
    try:
        # Create vector store instance
        vector_store = PineconeVectorStore(
            index_name=PINECONE_INDEX_NAME,
            embedding=embeddings,
            namespace=PINECONE_NAMESPACE
        )
        
        # Perform the search
        results = vector_store.similarity_search_with_score(query, k=top_k)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": score
            })
            
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error during semantic search: {str(e)}")
        return []

# If this module is run directly, synchronize latest podcasts
if __name__ == "__main__":
    result = sync_latest_podcasts()
    print(f"Sync complete: {result['message']}")