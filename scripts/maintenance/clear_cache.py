#!/usr/bin/env python3
"""
Script to clear the vector store cache to ensure the system uses updated settings.
"""

import asyncio
from app.rag.vector_store import VectorStore

async def clear_cache():
    """Clear the vector store cache"""
    print("Clearing vector store cache...")
    vector_store = VectorStore()
    vector_store.clear_cache()
    print("Vector store cache cleared successfully!")

if __name__ == "__main__":
    asyncio.run(clear_cache())