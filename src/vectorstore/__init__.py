"""
Vector Database Module

This package provides functionality for storing and retrieving podcast summaries
using vector databases for semantic search capabilities.
"""

from .pinecone_sync import (
    get_latest_podcast,
    insert_to_vector_db,
    sync_latest_podcasts,
    semantic_search
)

__all__ = [
    'get_latest_podcast',
    'insert_to_vector_db', 
    'sync_latest_podcasts',
    'semantic_search'
]
