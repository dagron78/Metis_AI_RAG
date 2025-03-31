# Chat Memory Fix

**Date:** March 31, 2025  
**Issue:** Metis RAG system not maintaining conversation memory between turns  
**Fix Type:** Enhancement  
**Components Affected:** Query Planner, Query Analyzer, Enhanced LangGraph RAG Agent  

## Issue Description

The Metis RAG system was not maintaining conversation memory between turns, causing it to "forget" previous parts of the conversation. This was observed in the following behaviors:

1. When asked to reformat a previous response, Metis provided a new response instead of reformatting the original one.
2. When asked follow-up questions that referenced previous turns, Metis lost context.
3. Metis explicitly stated it "does not have a persistent memory of our entire conversation" in response to a direct question.

## Root Cause Analysis

After investigating the codebase, we identified that the system had two parallel mechanisms for handling conversation history:

1. **Database-based Conversation Storage**: A robust SQL database schema with `Conversation`, `Message`, and `Citation` models.
2. **Mem0-based Memory System**: An external memory service integration via `mem0_client.py`.

While both systems stored conversation history correctly, this history wasn't being passed to the query planning and analysis components:

1. The `QueryPlanner.create_plan()` method didn't accept chat history as a parameter.
2. The `QueryAnalyzer.analyze()` method processed each query in isolation.
3. The agent called `query_planner.create_plan(query_id=query_id, query=query)` without passing history.

This created a disconnect where conversation history was stored but not used in the query planning process.

## Solution Implemented

We implemented the **Context Augmentation** approach, where:

1. The conversation history is passed through the system.
2. Retrieval is still based primarily on the current query (for efficiency and focus).
3. The final LLM prompt includes both the retrieved documents AND the conversation history.

### Changes Made

1. **QueryPlan Class (`app/rag/query_planner.py`)**:
   - Added `chat_history` parameter to store conversation history
   - Updated serialization methods to include chat history

2. **QueryPlanner Class (`app/rag/query_planner.py`)**:
   - Modified `create_plan` to accept chat history
   - Updated the synthesize step to indicate it should use history

3. **QueryAnalyzer Class (`app/rag/query_analyzer.py`)**:
   - Added chat history parameter to `analyze` method
   - Enhanced the analysis prompt to include conversation history
   - Added instructions to consider previous turns when analyzing queries

4. **EnhancedLangGraphRAGAgent (`app/rag/agents/enhanced_langgraph_rag_agent.py`)**:
   - Updated `_analyze_query` to extract chat history from conversation context
   - Modified `_plan_query` to pass chat history to the query planner

## Testing

The fix was tested with various conversation scenarios:

1. Simple follow-up questions ("Tell me more about that")
2. Requests to reformulate previous responses ("Give me that as a list")
3. Questions that reference entities from previous turns
4. Explicit questions about conversation memory

## Related Documentation

For a detailed implementation plan, see [Chat Memory Augmentation Plan](../implementation/chat_memory_augmentation_plan.md).