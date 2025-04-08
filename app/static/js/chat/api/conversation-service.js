/**
 * Conversation API service
 * Handles communication with the conversation management API endpoints
 */

import { authenticatedFetch } from './chat-service.js';

/**
 * Load conversation history from the server
 * @param {string} conversationId - The ID of the conversation to load
 * @returns {Promise<Object>} The conversation history data
 */
async function loadConversationHistory(conversationId) {
  try {
    if (!conversationId) {
      throw new Error('Conversation ID is required');
    }
    
    const response = await authenticatedFetch(`/api/chat/history?conversation_id=${conversationId}`);
    
    if (!response.ok) {
      // If 404, conversation doesn't exist or doesn't belong to this user
      if (response.status === 404) {
        throw { 
          createNew: true, 
          message: "Conversation not found or you don't have permission to access it" 
        };
      }
      throw new Error(`Failed to load conversation history: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error loading conversation history:', error);
    throw error;
  }
}

/**
 * Load available conversations from the server
 * @param {number} limit - Maximum number of conversations to return
 * @returns {Promise<Object>} The available conversations data
 */
async function loadAvailableConversations(limit = 10) {
  try {
    const response = await authenticatedFetch(`/api/chat/list?limit=${limit}`);
    
    if (!response.ok) {
      throw new Error(`Failed to load conversations: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error loading conversations:', error);
    throw error;
  }
}

/**
 * Save a conversation (mark as saved in metadata)
 * @param {string} conversationId - The ID of the conversation to save
 * @returns {Promise<Object>} The response data
 */
async function saveConversation(conversationId) {
  try {
    if (!conversationId) {
      throw new Error('Conversation ID is required');
    }
    
    const response = await authenticatedFetch(`/api/chat/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ conversation_id: conversationId })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to save conversation: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error saving conversation:', error);
    throw error;
  }
}

/**
 * Clear a conversation from the UI (does not delete from database)
 * @param {string} conversationId - The ID of the conversation to clear, or null to clear all
 * @returns {Promise<Object>} The response data
 */
async function clearConversation(conversationId = null) {
  try {
    const url = conversationId 
      ? `/api/chat/clear?conversation_id=${conversationId}`
      : '/api/chat/clear';
    
    const response = await authenticatedFetch(url, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error(`Failed to clear conversation: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error clearing conversation:', error);
    throw error;
  }
}

/**
 * Update the stored conversation ID
 * @param {string} id - The new conversation ID
 * @param {string} userId - Optional user ID who owns this conversation
 */
function updateConversationId(id, userId) {
  if (!id) return;
  
  // Store in localStorage
  localStorage.setItem('metis_conversation_id', id);
  
  // Store user ID with conversation metadata
  if (userId) {
    localStorage.setItem('userId', userId);
    
    // Update window.conversation metadata if available
    if (window.conversation && window.conversation.metadata) {
      window.conversation.metadata.userId = userId;
    }
    
    console.log(`Conversation ${id} is owned by user ${userId}`);
  }
  
  return id;
}

/**
 * Estimate token count for a string
 * @param {string} text - Text to estimate
 * @returns {number} Estimated token count
 */
function estimateTokens(text) {
  // Simple estimation: roughly 4 characters per token
  return Math.ceil(text.length / 4);
}

/**
 * Save the conversation to localStorage
 */
function saveToLocalStorage() {
  if (window.conversation) {
    localStorage.setItem('metis_conversation', JSON.stringify(window.conversation));
  }
}

// Export the API functions
export {
  loadConversationHistory,
  loadAvailableConversations,
  saveConversation,
  clearConversation,
  updateConversationId,
  estimateTokens,
  saveToLocalStorage
};