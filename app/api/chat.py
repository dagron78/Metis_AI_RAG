"""
Chat API endpoints.

DEPRECATED: This module is deprecated and will be removed in a future version.
Please use the new modular structure in app.api.chat package instead.
"""

import warnings
import logging
from fastapi import APIRouter

from app.api.chat import router

# Logger
logger = logging.getLogger("app.api.chat")

# Show deprecation warning
warnings.warn(
    "Importing directly from app.api.chat is deprecated. "
    "Please import from app.api.chat.router instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export the router
__all__ = ["router"]

# For backward compatibility, we need to re-export all the endpoints
# This is done by simply using the router from the new structure