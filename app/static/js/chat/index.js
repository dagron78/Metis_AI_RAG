/**
 * Metis RAG Chat Interface - Main Entry Point
 * 
 * This file serves as the main entry point for the chat interface.
 * It imports and initializes all the necessary components.
 */

import { ChatInterface } from './components/chat-interface.js';
import { chatState } from './state/chat-state.js';
import { settingsState } from './state/settings-state.js';

/**
 * Initialize the chat interface when the DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('Initializing Metis RAG Chat Interface');
  
  // Create and initialize the chat interface
  const chatInterface = new ChatInterface({
    containerSelector: '#chat-container',
    loadingSelector: '#loading',
    tokenUsageSelector: '#token-usage'
  });
  
  // Initialize the interface
  chatInterface.initialize();
  
  // Make the chat interface available globally for debugging
  window.MetisChat = {
    interface: chatInterface,
    state: chatState,
    settings: settingsState,
    
    // Public API methods
    sendMessage: (message) => chatInterface.sendMessage(message),
    clearChat: () => chatInterface.clearChat(),
    saveChat: () => chatInterface.saveChat()
  };
  
  console.log('Metis RAG Chat Interface initialized successfully');
});

// Export the components for use in other modules
export {
  ChatInterface,
  chatState,
  settingsState
};