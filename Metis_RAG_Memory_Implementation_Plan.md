# Metis RAG Memory Implementation Plan

## Overview

This document outlines the implementation plan for adding explicit memory capabilities to the Metis RAG system. The implementation focuses on two key aspects:

1. **Memory Buffer**: A dedicated storage mechanism for user-provided information that should be remembered verbatim.
2. **Response Format Simplification**: Streamlining the response generation process to maintain better context awareness.

## Implementation Components

### 1. Database Schema

We've created a new `memories` table with the following schema:

```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    label VARCHAR(50) NOT NULL DEFAULT 'explicit_memory',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX ix_memories_conversation_id ON memories(conversation_id);
CREATE INDEX ix_memories_label ON memories(label);
```

This table stores explicit memories with:
- A unique identifier
- Reference to the conversation
- The actual content to remember
- A label for categorization
- Creation timestamp

### 2. Memory Model

The `Memory` model represents the database entity:

```python
class Memory(Base):
    """Memory model for storing explicit memories"""
    __tablename__ = "memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    label = Column(String(50), nullable=False, server_default="explicit_memory")
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))
```

### 3. Memory Repository

A dedicated repository for memory operations:

```python
class MemoryRepository(BaseRepository[Memory]):
    """Repository for Memory model"""
    
    async def create_memory(self, conversation_id: UUID, content: str, label: str = "explicit_memory") -> Memory:
        """Create a new memory"""
        memory_data = {
            "conversation_id": conversation_id,
            "content": content,
            "label": label
        }
        return await self.create(memory_data)
    
    async def get_memories_by_conversation(self, conversation_id: UUID, label: Optional[str] = None, limit: int = 10) -> List[Memory]:
        """Get memories for a conversation"""
        # Implementation details...
```

### 4. Memory Buffer Module

The core functionality is implemented in `memory_buffer.py`:

```python
async def add_to_memory_buffer(conversation_id: UUID, content: str, label: str = "explicit_memory", db: AsyncSession = None) -> Memory:
    """Add content to the memory buffer"""
    # Implementation details...

async def get_memory_buffer(conversation_id: UUID, search_term: Optional[str] = None, label: Optional[str] = None, limit: int = 10, db: AsyncSession = None) -> List[Memory]:
    """Get memories from the buffer"""
    # Implementation details...

async def process_query(query: str, user_id: str, conversation_id: UUID, db: AsyncSession = None) -> tuple[str, Optional[str], Optional[str]]:
    """Process a query for memory commands before sending to RAG"""
    # Implementation details...
```

### 5. RAG Engine Integration

The RAG engine has been updated to:

1. Process memory commands in user queries
2. Handle memory storage and retrieval
3. Incorporate memory responses into the generated content
4. Support both streaming and non-streaming responses

Key integration points:
- Query preprocessing to detect memory commands
- Early return for memory recall operations
- Appending memory confirmations to responses

### 6. Migration and Testing

We've created:
1. A migration script to add the memories table
2. A test script to verify memory buffer functionality

## Usage Examples

### Storing a Memory

User: "Remember this phrase: The sky is orange because it is made of fruit."

System:
1. Detects the memory command
2. Extracts "The sky is orange because it is made of fruit"
3. Stores it in the memory buffer
4. Confirms storage: "I've stored this in my memory: 'The sky is orange because it is made of fruit'"

### Retrieving a Memory

User: "Can you remember the phrase from earlier in the chat?"

System:
1. Detects the recall command
2. Searches the memory buffer for the conversation
3. Returns: "Here's what I remember: 1. The sky is orange because it is made of fruit"

## Implementation Benefits

1. **Explicit Memory Storage**: Stores user-provided information verbatim, ensuring accurate recall.
2. **Context Maintenance**: Preserves conversation context across multiple turns.
3. **Geographic Specificity**: Better maintains location context through explicit memory.
4. **Error Recovery**: Provides clear mechanisms for correcting misunderstandings.
## Implementation Status

The memory buffer implementation has been completed and tested successfully. The following components have been implemented:

1. ✅ Memory model and database schema
2. ✅ Memory repository for database operations
3. ✅ Memory buffer module for core functionality
4. ✅ RAG engine integration for processing memory commands
5. ✅ Migration script for database updates
6. ✅ Test script for functionality verification

## Usage Instructions

### For Developers

1. **Database Migration**:
   ```bash
   python scripts/create_tables.py
   ```
   This will create the memories table in the database.

2. **Testing the Implementation**:
   ```bash
   python scripts/test_memory_buffer.py
   ```
   This will run tests to verify the memory buffer functionality.

3. **Integration with Existing Code**:
   - Import the memory buffer functions in your code:
     ```python
     from app.rag.memory_buffer import process_query, add_to_memory_buffer, get_memory_buffer
     ```
   - Process user queries through the `process_query` function before sending them to the RAG engine.

### For Users

Users can interact with the memory buffer using natural language commands:

1. **Storing Information**:
   - "Remember this: [information to store]"
   - "Remember this phrase: [phrase to remember]"
   - "Remember this name: [name to remember]"

2. **Retrieving Information**:
   - "Recall what I asked you to remember"
   - "What did I ask you to remember earlier?"
   - "Can you remember the [phrase/name/information] from earlier?"

## Future Enhancements

1. **Memory Categorization**:
   - Implement automatic categorization of memories
   - Allow users to specify categories when storing memories

2. **Memory Expiration**:
   - Add time-based expiration for memories
   - Implement priority-based memory retention

3. **Advanced Search**:
   - Semantic search for memories
   - Fuzzy matching for memory retrieval
   - Context-aware memory prioritization
   - Memory search improvements