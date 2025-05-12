"""
Podcast Insight Agent API Package

This package provides a REST API interface for interacting with the 
podcast insight agent system, enabling query and retrieval of podcast insights.
"""

from .server import create_app, app

__all__ = ['create_app', 'app']
