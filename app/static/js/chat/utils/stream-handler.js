/**
 * Stream handling utilities for the chat interface
 * Handles SSE (Server-Sent Events) streaming for real-time chat responses
 */

/**
 * Creates and manages a streaming connection to the server
 * @param {string} url - The API endpoint URL
 * @param {Object} params - The request parameters
 * @param {string} botMessageId - ID of the message element to update
 * @param {Function} onStart - Callback when streaming starts
 * @param {Function} onToken - Callback for each token received
 * @param {Function} onComplete - Callback when streaming completes
 * @param {Function} onError - Callback when an error occurs
 * @returns {AbortController} Controller that can be used to abort the stream
 */
function createEventStream(url, params, botMessageId, onStart, onToken, onComplete, onError) {
  // Create abort controller for the fetch
  const controller = new AbortController();
  const signal = controller.signal;
  
  // Get auth token
  const token = getAuthToken();
  
  // Set up event source for streaming
  fetchEventSource(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(params),
    signal: signal,
    onopen(response) {
      if (response.ok) {
        if (onStart) onStart();
        return; // Connection established successfully
      }
      throw new Error(`Failed to connect: ${response.status} ${response.statusText}`);
    },
    onmessage(event) {
      try {
        if (!event.data) return;
        
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
      if (onComplete) onComplete();
    }
  });
  
  return controller;
}

/**
 * Helper function to get the auth token from storage
 * @returns {string} Auth token
 */
function getAuthToken() {
  return localStorage.getItem('metisToken') || sessionStorage.getItem('metisToken') || '';
}

/**
 * Process a streaming response token
 * @param {Object} data - The token data
 * @param {HTMLElement} contentContainer - The container to update
 * @param {Function} updateConversationId - Function to update conversation ID
 * @param {Function} updateMessageSources - Function to update message sources
 * @param {Function} updateTokenUsage - Function to update token usage
 * @param {Function} scrollToBottom - Function to scroll to bottom
 * @param {boolean} showRawOutput - Whether to show raw output
 * @param {boolean} showRawLlmOutput - Whether to show raw LLM output
 */
function processStreamToken(data, contentContainer, messageElement, {
  updateConversationId,
  updateMessageSources,
  updateTokenUsage,
  scrollToBottom,
  showRawOutput,
  showRawLlmOutput
}) {
  // Update conversation ID if provided
  if (data.conversation_id) {
    updateConversationId(data.conversation_id);
  }
  
  // Update content based on response type
  if (data.content && contentContainer) {
    if (showRawOutput && data.raw_output) {
      contentContainer.innerHTML = MetisMarkdown.formatRawText(data.raw_output);
    } else if (showRawLlmOutput && data.raw_llm_output) {
      contentContainer.innerHTML = MetisMarkdown.formatRawText(data.raw_llm_output);
    } else {
      contentContainer.innerHTML = MetisMarkdown.processResponse(data.content);
      MetisMarkdown.initializeHighlighting(contentContainer);
      MetisMarkdown.addCopyButtons(contentContainer);
    }
  }
  
  // Update sources if provided
  if (data.sources && data.sources.length > 0) {
    updateMessageSources(messageElement, data.sources);
  }
  
  // Update token usage if provided
  if (data.usage) {
    updateTokenUsage(data.usage);
  }
  
  // Scroll to bottom with each update
  scrollToBottom();
}

// Export the utilities
export {
  createEventStream,
  getAuthToken,
  processStreamToken
};