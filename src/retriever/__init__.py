"""
Podcast Retrieval Module

This module provides functionality for retrieving relevant podcast information
and generating AI responses based on vector similarity search.
"""

from .retriever import retrieve_and_respond, llm

__all__ = ['retrieve_and_respond', 'llm']
