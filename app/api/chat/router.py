"""
Chat API router.

This module defines the router for the chat API endpoints.
"""

from fastapi import APIRouter

from app.api.chat.handlers import (
    query_chat,
    get_history,
    save_conversation,
    clear_conversation,
    list_conversations,
    memory_diagnostics
)
from app.models.chat import ChatResponse

# Create router
router = APIRouter()

# Standard RAG endpoints
router.add_api_route("/query", query_chat, methods=["POST"], response_model=ChatResponse)

# Conversation management endpoints
router.add_api_route("/history", get_history, methods=["GET"])
router.add_api_route("/save", save_conversation, methods=["POST"])
router.add_api_route("/clear", clear_conversation, methods=["DELETE"])
router.add_api_route("/list", list_conversations, methods=["GET"])

# Memory endpoints
router.add_api_route("/memory/diagnostics", memory_diagnostics, methods=["GET"])

# Note: LangGraph and Enhanced LangGraph endpoints will be added later
# when we implement those handlers