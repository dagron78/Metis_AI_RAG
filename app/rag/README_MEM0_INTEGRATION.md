# Mem0 Integration for Metis RAG

This document describes how to set up and use the Mem0 integration for Metis RAG.

## Overview

Mem0 is a memory layer for AI applications that provides a way to store and retrieve information related to users, sessions, and documents. It enables more personalized and context-aware interactions in the Metis RAG system.

The integration provides the following features:

- Conversation history storage and retrieval
- User preferences storage and retrieval
- Document interaction tracking
- Enhanced context for RAG queries

## Setup

### 1. Start Mem0 Server

The easiest way to run Mem0 is using Docker Compose:

```bash
cd config
docker-compose -f docker-compose.mem0.yml up -d
```

This will start Mem0 and its required PostgreSQL database in containers. The Mem0 server will be accessible at http://localhost:8050.

### 2. Configure Metis RAG

Update your `.env` file to include the Mem0 configuration:

```
# Mem0 settings
MEM0_ENDPOINT=http://localhost:8050
USE_MEM0=True
```

The API key is optional for local development.

### 3. Restart Metis RAG

Restart your Metis RAG application to apply the changes.

## Usage

The Mem0 integration is used automatically by the RAG engine when enabled. It provides the following functionality:

### Conversation History

Conversation history is stored in Mem0's recall memory. This allows the system to maintain context across sessions and provide more coherent responses.

### User Preferences

User preferences are stored in Mem0's archival memory. This allows the system to personalize responses based on user preferences, such as preferred models or response styles.

### Document Interactions

Document interactions are stored in Mem0's archival memory. This allows the system to track which documents a user has interacted with and provide more relevant responses.

## API

The Mem0 integration provides the following API:

### `get_mem0_client()`

Get the Mem0 client instance.

### `store_message(human_id, role, content)`

Store a message in recall memory.

### `get_conversation_history(human_id, limit=10)`

Get conversation history from recall memory.

### `store_user_preferences(human_id, preferences)`

Store user preferences in archival memory.

### `get_user_preferences(human_id)`

Get user preferences from archival memory.

### `store_document_interaction(human_id, document_id, interaction_type, data)`

Store document interaction in archival memory.

### `get_document_interactions(human_id, document_id=None, interaction_type=None, limit=10)`

Get document interactions from archival memory.

## Troubleshooting

If you encounter issues with the Mem0 integration, check the following:

1. Make sure the Mem0 server is running and accessible at the configured endpoint.
2. Check the logs for any error messages related to Mem0.
3. Make sure the `USE_MEM0` setting is set to `True` in your `.env` file.
4. If you're using an API key, make sure it's correctly configured.

## References

- [Mem0 Documentation](https://docs.mem0.ai)
- [Mem0 GitHub Repository](https://github.com/mem0ai/mem0)