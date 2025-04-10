/**
 * Error handling utilities for the chat interface
 * Provides standardized error handling and display functions
 */

/**
 * Handle API errors in a standardized way
 * @param {Error} error - The error object
 * @param {HTMLElement} messageElement - Optional message element to update with error
 * @param {Function} addMessage - Function to add a new message
 * @returns {string} Error message
 */
function handleApiError(error, messageElement, addMessage) {
  console.error('API Error:', error);
  
  // Format error message
  let errorMessage = 'An error occurred while communicating with the server.';
  
  if (error.message) {
    errorMessage = `Error: ${error.message}`;
  }
  
  // If we have a message element, update it with the error
  if (messageElement) {
    const contentContainer = messageElement.querySelector('.message-content');
    if (contentContainer) {
      contentContainer.innerHTML += `
        <div class="error">
          ${errorMessage}
          <button class="retry-button">Retry</button>
        </div>
      `;
      
      // Add click event to retry button
      const retryButton = contentContainer.querySelector('.retry-button');
      if (retryButton) {
        retryButton.addEventListener('click', () => {
          // Remove the current message and retry
          if (messageElement) {
            messageElement.remove();
          }
          // Trigger a new message send
          document.getElementById('send-button')?.click();
        });
      }
    }
  } else if (addMessage) {
    // Add a new error message
    addMessage('bot', errorMessage);
  }
  
  return errorMessage;
}

/**
 * Handle streaming errors
 * @param {Error} error - The error object
 * @param {HTMLElement} contentContainer - The content container to update
 * @param {AbortController} controller - The abort controller for the stream
 * @param {Function} setLoading - Function to update loading state
 */
function handleStreamError(error, contentContainer, controller, setLoading) {
  console.error('Stream error:', error);
  
  // Add retry button to message
  if (contentContainer) {
    contentContainer.innerHTML += `
      <div class="error">Error: Connection lost. <button class="retry-button">Retry</button></div>
    `;
    
    // Add click event to retry button
    const retryButton = contentContainer.querySelector('.retry-button');
    if (retryButton) {
      retryButton.addEventListener('click', () => {
        // Remove the current message and retry
        const messageElement = contentContainer.closest('.message');
        if (messageElement) {
          messageElement.remove();
        }
        // Trigger a new message send
        document.getElementById('send-button')?.click();
      });
    }
  }
  
  // Close the stream
  if (controller) {
    controller.abort();
  }
  
  // Update loading state
  if (setLoading) {
    setLoading(false);
  }
}

/**
 * Validate JSON input
 * @param {string} jsonString - The JSON string to validate
 * @param {Function} addMessage - Function to add error message
 * @returns {Object|null} Parsed JSON or null if invalid
 */
function validateJson(jsonString, addMessage) {
  try {
    return JSON.parse(jsonString);
  } catch (e) {
    console.error('Invalid JSON:', e);
    
    // Add error message to chat
    if (addMessage) {
      addMessage('bot', 'Error: Invalid JSON. Please check your syntax.');
    }
    
    return null;
  }
}

// Export the utilities
export {
  handleApiError,
  handleStreamError,
  validateJson
};