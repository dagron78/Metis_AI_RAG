/**
 * Chat API service
 * Handles communication with the chat API endpoints
 */

import { getAuthToken } from '../utils/stream-handler.js';
import { handleApiError, validateJson } from '../utils/error-handler.js';

/**
 * Send a chat message using the streaming API
 * @param {Object} params - The message parameters
 * @param {Function} onStart - Callback when streaming starts
 * @param {Function} onToken - Callback for each token received
 * @param {Function} onComplete - Callback when streaming completes
 * @param {Function} onError - Callback when an error occurs
 * @returns {AbortController} Controller that can be used to abort the stream
 */
function sendStreamingMessage(params, onStart, onToken, onComplete, onError) {
  console.log("Sending streaming message with params:", params);
  
  // Create abort controller for the fetch
  const controller = new AbortController();
  const signal = controller.signal;
  
  // Ensure fetchEventSource is available
  if (typeof window.fetchEventSource !== 'function') {
    console.error("fetchEventSource is not available - make sure the script is loaded correctly");
    if (onError) onError(new Error("fetchEventSource is not available"));
    return controller;
  }
  
  // Set up event source for streaming
  try {
    window.fetchEventSource('/api/chat/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify(params),
      signal: signal,
      onopen(response) {
        console.log("Stream connection opened with status:", response.status);
        if (response.ok) {
          if (onStart) onStart();
          return; // Connection established successfully
        }
        throw new Error(`Failed to connect: ${response.status} ${response.statusText}`);
      },
      onmessage(event) {
        try {
          if (!event.data) return;
          
          console.log("Received stream data:", event.data.substring(0, 50) + (event.data.length > 50 ? '...' : ''));
          
          // Attempt to parse JSON response
          const data = JSON.parse(event.data);
          
          // Call the token callback
          if (onToken) onToken(data);
        } catch (error) {
          console.error('Error processing streaming message:', error);
        }
      },
      onerror(err) {
        console.error('Stream error:', err);
        
        if (onError) onError(err);
        
        // Close the stream
        controller.abort();
      },
      onclose() {
        // Stream closed successfully
        console.log("Stream connection closed successfully");
        if (onComplete) onComplete();
      }
    });
    
    console.log("Stream request initiated");
  } catch (error) {
    console.error("Error initiating stream:", error);
    if (onError) onError(error);
  }
  
  return controller;
}

/**
 * Send a chat message using the non-streaming API
 * @param {Object} params - The message parameters
 * @returns {Promise<Object>} The response data
 */
async function sendNonStreamingMessage(params) {
  try {
    // Add console logging to debug response issues
    console.log("Sending non-streaming query:", params);
    
    const response = await authenticatedFetch('/api/chat/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    });
    
    console.log("Received API response status:", response.status);
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const data = await response.json();
    console.log("Received response data:", data);
    
    return data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
}

/**
 * Helper function for authenticated fetch requests
 * @param {string} url - The API URL
 * @param {Object} options - Fetch options
 * @returns {Promise} Fetch promise
 */
function authenticatedFetch(url, options = {}) {
  // Use the global authenticatedFetch function from main.js if available
  if (window.authenticatedFetch) {
    return window.authenticatedFetch(url, options);
  } else {
    // Fallback to simple fetch with token if global function not available
    const token = getAuthToken();
    const headers = options.headers || {};
    
    return fetch(url, {
      ...options,
      headers: {
        ...headers,
        'Authorization': `Bearer ${token}`
      }
    });
  }
}

/**
 * Load available models from the API
 * @returns {Promise<Array>} Array of available models
 */
async function loadModels() {
  try {
    const response = await authenticatedFetch('/api/system/models');
    
    if (!response.ok) {
      // Use default models if unauthorized
      if (response.status === 401) {
        return [{ name: 'llama3' }];
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const models = await response.json();
    return models;
  } catch (error) {
    console.error('Error loading models:', error);
    // Return default model on error
    return [{ name: 'llama3' }];
  }
}

// Export the API functions
export {
  sendStreamingMessage,
  sendNonStreamingMessage,
  authenticatedFetch,
  loadModels
};