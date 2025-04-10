"""
Chat API utilities package.

This package contains utility functions for the chat API.
"""

from app.api.chat.utils.streaming import (
    create_event_generator,
    create_streaming_response
)
from app.api.chat.utils.error_handling import (
    handle_chat_error,
    create_error_response
)
from app.api.chat.utils.conversation_helpers import (
    get_or_create_conversation,
    get_conversation_history,
    add_message_to_conversation,
    format_conversation_history,
    MAX_HISTORY_MESSAGES
)

__all__ = [
    "create_event_generator",
    "create_streaming_response",
    "handle_chat_error",
    "create_error_response",
    "get_or_create_conversation",
    "get_conversation_history",
    "add_message_to_conversation",
    "format_conversation_history",
    "MAX_HISTORY_MESSAGES"
]