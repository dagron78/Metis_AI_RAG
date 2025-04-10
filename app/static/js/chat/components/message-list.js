/**
 * Message List Component
 * Handles rendering and management of chat messages
 */

import { MetisMarkdown } from '../utils/markdown-renderer.js';

/**
 * MessageList class
 * Manages the display and interaction with chat messages
 */
class MessageList {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    // Configuration with defaults
    this.config = {
      container: null,
      ...config
    };
    
    // Validate container
    if (!this.config.container) {
      console.error('MessageList: No container element provided');
      return;
    }
    
    // Initialize
    this.container = this.config.container;
  }
  
  /**
   * Adds a message to the chat container
   * @param {string} type - The message type ('user' or 'bot')
   * @param {string} content - The message content
   * @param {boolean} isRaw - Whether the content is raw text
   * @param {boolean} storeOnly - If true, only add to memory without displaying in UI
   * @returns {HTMLElement} The created message element
   */
  addMessage(type, content, isRaw = false, storeOnly = false) {
    if (!content) return null;
    
    // Store in conversation memory for context
    const sources = null; // Will be updated later for bot messages with citations
    
    if (window.conversation && !storeOnly) {
      // Add to conversation array for context in future messages
      window.conversation.messages.push({
        role: type === 'user' ? 'user' : 'assistant',
        content: content,
        sources: sources,
        timestamp: new Date().toISOString()
      });
      
      // Update token estimate
      const tokens = this.estimateTokens(content);
      window.conversation.metadata.estimatedTokens += tokens;
      window.conversation.metadata.lastUpdated = new Date().toISOString();
      
      // Save to localStorage for persistence
      this.saveToLocalStorage();
      
      console.log(`Added ${type} message to conversation memory, tokens: ${tokens}`);
    }
    
    // If store only, don't add to UI
    if (storeOnly || !this.container) return null;
    
    console.log(`Adding ${type} message to UI, raw: ${isRaw}, content length: ${content.length}`);
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}-message`;
    messageElement.id = 'message-' + Date.now();
    
    let messageContent = '';
    
    if (type === 'user') {
      messageContent = `
        <div class="message-header">You:</div>
        <div class="message-content">${this.escapeHtml(content)}</div>
      `;
    } else {
      // For bot messages, process markdown unless it's raw
      const contentHtml = isRaw 
        ? `<pre class="raw-output">${this.escapeHtml(content)}</pre>`
        : MetisMarkdown.processResponse(content);
      
      messageContent = `
        <div class="message-header">Metis:</div>
        <div class="message-content">${contentHtml}</div>
      `;
    }
    
    messageElement.innerHTML = messageContent;
    
    // Add copy button for bot messages
    if (type === 'bot') {
      const copyButton = document.createElement('button');
      copyButton.className = 'copy-button';
      copyButton.innerHTML = '<i class="fas fa-copy"></i>';
      copyButton.title = 'Copy to clipboard';
      copyButton.addEventListener('click', () => {
        this.copyMessageContent(messageElement);
      });
      messageElement.appendChild(copyButton);
      
      // Apply syntax highlighting and add copy buttons to code blocks
      const contentDiv = messageElement.querySelector('.message-content');
      if (contentDiv && !isRaw) {
        MetisMarkdown.initializeHighlighting(contentDiv);
        MetisMarkdown.addCopyButtons(contentDiv);
      }
    }
    
    this.container.appendChild(messageElement);
    this.scrollToBottom();
    
    return messageElement;
  }
  
  /**
   * Adds a message with raw HTML content
   * @param {string} type - The message type ('user' or 'bot')
   * @param {string} html - The HTML content
   * @param {string} id - Optional ID for the message element
   * @returns {HTMLElement} The created message element
   */
  addRawHtmlMessage(type, html, id = null) {
    if (!this.container) return null;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}-message`;
    if (id) {
      messageElement.id = id;
    } else {
      messageElement.id = 'message-' + Date.now();
    }
    
    messageElement.innerHTML = html;
    
    // Add copy button for bot messages
    if (type === 'bot') {
      const copyButton = document.createElement('button');
      copyButton.className = 'copy-button';
      copyButton.innerHTML = '<i class="fas fa-copy"></i>';
      copyButton.title = 'Copy to clipboard';
      copyButton.addEventListener('click', () => {
        this.copyMessageContent(messageElement);
      });
      messageElement.appendChild(copyButton);
    }
    
    this.container.appendChild(messageElement);
    this.scrollToBottom();
    
    return messageElement;
  }
  
  /**
   * Copies a message's content to clipboard
   * @param {HTMLElement} messageElement - The message element
   */
  copyMessageContent(messageElement) {
    if (!messageElement) return;
    
    const contentElement = messageElement.querySelector('.message-content');
    if (!contentElement) return;
    
    // Get text content (stripping HTML)
    const text = contentElement.innerText || contentElement.textContent;
    
    // Copy to clipboard
    navigator.clipboard.writeText(text)
      .then(() => {
        // Show success feedback
        const copyButton = messageElement.querySelector('.copy-button');
        if (copyButton) {
          const originalHtml = copyButton.innerHTML;
          copyButton.innerHTML = '<i class="fas fa-check"></i>';
          
          setTimeout(() => {
            copyButton.innerHTML = originalHtml;
          }, 2000);
        }
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  }
  
  /**
   * Scrolls the chat container to the bottom
   */
  scrollToBottom() {
    if (!this.container) return;
    
    this.container.scrollTop = this.container.scrollHeight;
  }
  
  /**
   * Helper function to escape HTML in text
   * @param {string} text - Text to escape
   * @returns {string} Escaped HTML
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  /**
   * Estimates token count for a string
   * @param {string} text - Text to estimate
   * @returns {number} Estimated token count
   */
  estimateTokens(text) {
    // Simple estimation: roughly 4 characters per token
    return Math.ceil(text.length / 4);
  }
  
  /**
   * Saves the conversation to localStorage
   */
  saveToLocalStorage() {
    if (window.conversation) {
      localStorage.setItem('metis_conversation', JSON.stringify(window.conversation));
    }
  }
}

// Export the MessageList class
export { MessageList };