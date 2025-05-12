"""
Prompt Templates Module

This module provides system prompts and templates for the podcast insight agent.
"""

from .system_prompt import SUMMARIZER_SYSTEM_PROMPT

# Export the system message for backward compatibility
system_message = SUMMARIZER_SYSTEM_PROMPT

__all__ = [
    'system_message',
    'SUMMARIZER_SYSTEM_PROMPT',
]