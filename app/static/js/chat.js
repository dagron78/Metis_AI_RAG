/**
 * Metis RAG Chat Interface
 * 
 * @deprecated This file is deprecated and will be removed in a future version.
 * Please use the new modular structure in app/static/js/chat/ instead.
 */

// Show deprecation warning
console.warn(
  'DEPRECATION WARNING: app/static/js/chat.js is deprecated and will be removed in a future version. ' +
  'Please use the new modular structure in app/static/js/chat/ instead.'
);

// Import from the new modular structure
import { ChatInterface, chatState, settingsState } from './chat/index.js';

// Main Chat Application (for backward compatibility)
const MetisChat = (function() {
  // Private variables
  let chatInterface = null;
  
  /**
   * Initializes the chat application
   */
  function initialize() {
    console.log('Initializing chat interface (legacy wrapper)');
    
    // Create and initialize the chat interface
    chatInterface = new ChatInterface({
      containerSelector: '#chat-container',
      loadingSelector: '#loading',
      tokenUsageSelector: '#token-usage'
    });
    
    // Initialize the interface
    chatInterface.initialize();
  }
  
  /**
   * Sends a user message to the API
   */
  function sendMessage() {
    if (!chatInterface) return;
    
    const userInput = document.getElementById('user-input');
    if (!userInput) return;
    
    const message = userInput.value.trim();
    if (!message) return;
    
    // Send the message
    chatInterface.sendMessage(message);
    
    // Clear input
    userInput.value = '';
  }
  
  /**
   * Clears the chat history
   */
  function clearChat() {
    if (!chatInterface) return;
    chatInterface.clearChat();
  }
  
  /**
   * Saves the chat history
   */
  function saveChat() {
    if (!chatInterface) return;
    chatInterface.saveChat();
  }
  
  // Return public API (for backward compatibility)
  return {
    initialize,
    sendMessage,
    clearChat,
    saveChat
  };
})();

// Initialize when DOM is ready (for backward compatibility)
document.addEventListener('DOMContentLoaded', function() {
  MetisChat.initialize();
});