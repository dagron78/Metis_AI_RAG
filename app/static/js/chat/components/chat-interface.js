/**
 * Chat Interface Component
 * Main component that orchestrates the chat UI functionality
 */

import { sendStreamingMessage, sendNonStreamingMessage, loadModels } from '../api/chat-service.js';
import { 
  loadConversationHistory, 
  loadAvailableConversations, 
  updateConversationId,
  saveToLocalStorage
} from '../api/conversation-service.js';
import { MetisMarkdown } from '../utils/markdown-renderer.js';
import { handleApiError, handleStreamError } from '../utils/error-handler.js';
import { MessageList } from './message-list.js';
import { InputArea } from './input-area.js';
import { Citations } from './citations.js';

/**
 * ChatInterface class
 * Manages the overall chat interface and coordinates between components
 */
class ChatInterface {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    // Configuration with defaults
    this.config = {
      containerSelector: '#chat-container',
      loadingSelector: '#loading',
      tokenUsageSelector: '#token-usage',
      ...config
    };
    
    // State
    this.currentConversationId = null;
    this.useStreaming = true;
    this.useRag = true;
    this.showRawOutput = false;
    this.showRawLlmOutput = false;
    this.currentController = null; // For aborting fetch requests
    
    // DOM Elements
    this.elements = {};
    
    // Sub-components
    this.messageList = null;
    this.inputArea = null;
    this.citations = null;
  }
  
  /**
   * Initialize the chat interface
   */
  initialize() {
    console.log('Initializing chat interface');
    
    // Get DOM elements
    this.cacheElements();
    
    // Initialize sub-components
    this.initializeComponents();
    
    // Load initial state
    this.loadInitialState();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Focus the input element after initialization
    setTimeout(() => {
      if (this.inputArea) {
        this.inputArea.focus();
      }
    }, 300); // Short delay to ensure all DOM operations are complete
  }
  
  /**
   * Cache DOM elements for better performance
   */
  cacheElements() {
    this.elements = {
      chatContainer: document.querySelector(this.config.containerSelector),
      loadingIndicator: document.querySelector(this.config.loadingSelector),
      tokenUsage: document.querySelector(this.config.tokenUsageSelector),
      tokenUsageFill: document.querySelector(`${this.config.tokenUsageSelector}-fill`),
      tokenUsageText: document.querySelector(`${this.config.tokenUsageSelector}-text`),
      modelSelect: document.getElementById('model'),
      ragToggle: document.getElementById('rag-toggle'),
      streamToggle: document.getElementById('stream-toggle'),
      rawOutputToggle: document.getElementById('raw-output-toggle'),
      rawLlmOutputToggle: document.getElementById('raw-llm-output-toggle'),
      maxResults: document.getElementById('max-results'),
      temperature: document.getElementById('temperature'),
      metadataFilters: document.getElementById('metadata-filters'),
      advancedToggle: document.getElementById('advanced-toggle'),
      advancedContent: document.getElementById('advanced-content'),
      advancedIcon: document.getElementById('advanced-icon'),
      clearButton: document.getElementById('clear-chat'),
      saveButton: document.getElementById('save-chat')
    };
    
    // Validate required elements
    this.validateElements();
  }
  
  /**
   * Validate that required elements exist
   */
  validateElements() {
    const requiredElements = ['chatContainer'];
    let missing = false;
    
    requiredElements.forEach(key => {
      if (!this.elements[key]) {
        console.error(`Required element missing: ${key}`);
        missing = true;
      }
    });
    
    if (missing) {
      console.error("Some required chat UI elements are missing. Chat functionality may be limited.");
    }
  }
  
  /**
   * Initialize sub-components
   */
  initializeComponents() {
    if (this.elements.chatContainer) {
      // Initialize message list
      this.messageList = new MessageList({
        container: this.elements.chatContainer
      });
      
      // Initialize input area
      this.inputArea = new InputArea({
        onSend: (message) => this.sendMessage(message)
      });
      
      // Initialize citations
      this.citations = new Citations();
      
      console.log("Chat components initialized successfully");
    } else {
      console.error("Chat container element not found");
    }
  }
  
  /**
   * Load initial state from localStorage and API
   */
  loadInitialState() {
    // Check for URL parameters that might contain conversation ID
    const urlParams = new URLSearchParams(window.location.search);
    const urlConversationId = urlParams.get('conversation_id');
    
    // Conversation ID from URL or localStorage
    let conversationToLoad = urlConversationId || localStorage.getItem('metis_conversation_id');
    
    if (conversationToLoad) {
      this.currentConversationId = conversationToLoad;
      
      // If conversation ID was in URL, store it in localStorage
      if (urlConversationId) {
        localStorage.setItem('metis_conversation_id', urlConversationId);
        
        // Clean URL to avoid sharing conversation IDs in links
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
      }
      
      // Load conversation history for the stored ID
      this.loadConversationHistory(conversationToLoad);
    } else {
      // Check if we should load available conversations
      this.loadAvailableConversations();
    }
    
    // Toggle states
    if (this.elements.ragToggle) {
      this.useRag = localStorage.getItem('metis_use_rag') !== 'false';
      this.elements.ragToggle.checked = this.useRag;
    }
    
    if (this.elements.streamToggle) {
      this.useStreaming = localStorage.getItem('metis_use_streaming') !== 'false';
      this.elements.streamToggle.checked = this.useStreaming;
    }
    
    if (this.elements.rawOutputToggle) {
      this.showRawOutput = localStorage.getItem('metis_show_raw_output') === 'true';
      this.elements.rawOutputToggle.checked = this.showRawOutput;
    }
    
    if (this.elements.rawLlmOutputToggle) {
      this.showRawLlmOutput = localStorage.getItem('metis_show_raw_llm_output') === 'true';
      this.elements.rawLlmOutputToggle.checked = this.showRawLlmOutput;
    }
    
    // Load available models
    this.loadModels();
    
    // Advanced options toggle state
    if (this.elements.advancedContent && this.elements.advancedToggle) {
      const showAdvanced = localStorage.getItem('metis_show_advanced') === 'true';
      if (showAdvanced) {
        this.elements.advancedContent.classList.add('show');
        this.elements.advancedIcon.classList.replace('fa-chevron-down', 'fa-chevron-up');
      }
    }
  }
  
  /**
   * Set up event listeners for UI interactions
   */
  setupEventListeners() {
    // Toggle buttons
    if (this.elements.ragToggle) {
      this.elements.ragToggle.addEventListener('change', () => {
        this.useRag = this.elements.ragToggle.checked;
        localStorage.setItem('metis_use_rag', this.useRag);
        
        // Show/hide RAG-specific parameters
        const ragParams = document.querySelectorAll('.rag-param');
        ragParams.forEach(param => {
          param.style.display = this.useRag ? 'block' : 'none';
        });
      });
    }
    
    if (this.elements.streamToggle) {
      this.elements.streamToggle.addEventListener('change', () => {
        this.useStreaming = this.elements.streamToggle.checked;
        localStorage.setItem('metis_use_streaming', this.useStreaming);
      });
    }
    
    if (this.elements.rawOutputToggle) {
      this.elements.rawOutputToggle.addEventListener('change', () => {
        this.showRawOutput = this.elements.rawOutputToggle.checked;
        localStorage.setItem('metis_show_raw_output', this.showRawOutput);
      });
    }
    
    if (this.elements.rawLlmOutputToggle) {
      this.elements.rawLlmOutputToggle.addEventListener('change', () => {
        this.showRawLlmOutput = this.elements.rawLlmOutputToggle.checked;
        localStorage.setItem('metis_show_raw_llm_output', this.showRawLlmOutput);
      });
    }
    
    // Advanced options toggle
    if (this.elements.advancedToggle && this.elements.advancedContent && this.elements.advancedIcon) {
      this.elements.advancedToggle.addEventListener('click', () => {
        this.elements.advancedContent.classList.toggle('show');
        
        // Toggle icon
        if (this.elements.advancedContent.classList.contains('show')) {
          this.elements.advancedIcon.classList.replace('fa-chevron-down', 'fa-chevron-up');
          localStorage.setItem('metis_show_advanced', 'true');
        } else {
          this.elements.advancedIcon.classList.replace('fa-chevron-up', 'fa-chevron-down');
          localStorage.setItem('metis_show_advanced', 'false');
        }
      });
    }
    
    // Other UI controls
    if (this.elements.clearButton) {
      this.elements.clearButton.addEventListener('click', () => this.clearChat());
    }
    
    if (this.elements.saveButton) {
      this.elements.saveButton.addEventListener('click', () => this.saveChat());
    }
  }
  
  /**
   * Load available models and populate the dropdown
   */
  async loadModels() {
    if (!this.elements.modelSelect) return;
    
    try {
      const models = await loadModels();
      
      this.elements.modelSelect.innerHTML = ''; // Clear existing options
      
      if (Array.isArray(models) && models.length > 0) {
        models.forEach(model => {
          const option = document.createElement('option');
          option.value = model.name;
          option.textContent = model.name;
          this.elements.modelSelect.appendChild(option);
        });
      } else {
        // Fallback default
        const option = document.createElement('option');
        option.value = 'gemma3:4b';
        option.textContent = 'gemma3:4b (default)';
        this.elements.modelSelect.appendChild(option);
      }
    } catch (error) {
      console.error('Error loading models:', error);
      // Add a default model option
      this.elements.modelSelect.innerHTML = '<option value="llama3">llama3 (default)</option>';
    }
  }
  
  /**
   * Load conversation history from the server
   * @param {string} conversationId - The ID of the conversation to load
   */
  async loadConversationHistory(conversationId) {
    if (!this.elements.chatContainer) return;
    
    // Show loading indicator in chat container
    this.elements.chatContainer.innerHTML = '<div class="loading-history">Loading conversation history...</div>';
    
    // Clear existing conversation array
    window.conversation = {
      messages: [],
      metadata: {
        estimatedTokens: 0,
        maxTokens: 4096,
        lastUpdated: new Date().toISOString(),
        userId: localStorage.getItem('userId') // Store user ID with conversation
      }
    };
    
    // If no conversation ID or it's invalid, create a new conversation
    if (!conversationId) {
      return this.createNewConversation();
    }
    
    try {
      // Fetch conversation history from the server
      const data = await loadConversationHistory(conversationId);
      
      // Store conversation owner ID if available
      if (data.user_id) {
        localStorage.setItem('userId', data.user_id);
        window.conversation.metadata.userId = data.user_id;
      }
      
      // Clear loading indicator
      this.elements.chatContainer.innerHTML = '';
      
      if (data.messages && data.messages.length > 0) {
        // Add each message to the chat
        data.messages.forEach(message => {
          // Check if message has content
          if (!message.content) return;
          
          // Add message to UI
          const messageElement = this.messageList.addMessage(message.role, message.content);
          
          // If this is an assistant message and has citations, add them
          if (message.role === 'assistant' && message.citations && message.citations.length > 0) {
            this.citations.updateMessageSources(messageElement, message.citations);
          }
          
          // Add to window.conversation for context memory
          window.conversation.messages.push({
            role: message.role,
            content: message.content,
            sources: message.citations || null,
            timestamp: message.timestamp || new Date().toISOString()
          });
        });
        
        // Update lastUpdated timestamp
        window.conversation.metadata.lastUpdated = new Date().toISOString();
        
        // Save updated conversation to localStorage
        saveToLocalStorage();
        
        console.log(`Loaded ${data.messages.length} messages into conversation memory`);
      } else {
        // If no messages, add the default welcome message
        this.elements.chatContainer.innerHTML = `
          <div class="message bot-message">
            <div class="message-header">Metis:</div>
            <div class="message-content">Hello! I'm your Metis RAG assistant. Ask me anything about your uploaded documents or chat with me directly.</div>
          </div>
        `;
      }
      
      // Scroll to bottom of chat
      this.messageList.scrollToBottom();
    } catch (error) {
      // If we need to create a new conversation
      if (error.createNew) {
        this.createNewConversation(error.message);
        return;
      }
      
      console.error('Error loading conversation history:', error);
      // Show error message
      this.elements.chatContainer.innerHTML = `
        <div class="message bot-message">
          <div class="message-header">Metis:</div>
          <div class="message-content">
            Unable to load conversation history. Starting a new conversation.
            <div class="error-details">${error.message || 'Unknown error'}</div>
          </div>
        </div>
      `;
      
      // Create a new conversation after showing the error
      this.createNewConversation();
    }
  }
  
  /**
   * Load available conversations from the server
   * This shows a dropdown or UI element to select past conversations
   */
  async loadAvailableConversations() {
    // Check if we should create a new conversation immediately or show selector
    const shouldShowSelector = localStorage.getItem('show_conversation_selector') !== 'false';
    
    if (!shouldShowSelector) {
      // Just create a new conversation
      this.createNewConversation();
      return;
    }
    
    // Show loading indicator
    if (this.elements.chatContainer) {
      this.elements.chatContainer.innerHTML = '<div class="loading-history">Loading available conversations...</div>';
    }
    
    try {
      // Fetch user's conversations
      const data = await loadAvailableConversations(10);
      
      if (!data.conversations || data.conversations.length === 0) {
        // No conversations available, create a new one
        this.createNewConversation();
        return;
      }
      
      // Create a conversation selector UI
      if (this.elements.chatContainer) {
        const selectorHtml = `
          <div class="conversation-selector">
            <h3>Select a conversation</h3>
            <div class="conversation-list">
              ${data.conversations.map(conv => `
                <div class="conversation-item" data-id="${conv.id}">
                  <div class="conversation-preview">
                    ${conv.preview || 'New conversation'}
                  </div>
                  <div class="conversation-meta">
                    ${new Date(conv.updated_at).toLocaleString()}
                    <span class="message-count">${conv.message_count} messages</span>
                  </div>
                </div>
              `).join('')}
              <div class="conversation-item new-conversation">
                <div class="conversation-preview">+ Start a new conversation</div>
              </div>
            </div>
          </div>
        `;
        
        this.elements.chatContainer.innerHTML = selectorHtml;
        
        // Add click handlers
        document.querySelectorAll('.conversation-item').forEach(item => {
          item.addEventListener('click', () => {
            if (item.classList.contains('new-conversation')) {
              this.createNewConversation();
            } else {
              const conversationId = item.getAttribute('data-id');
              if (conversationId) {
                this.loadConversationHistory(conversationId);
              }
            }
          });
        });
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
      // On error, just create a new conversation
      this.createNewConversation();
    }
  }
  
  /**
   * Creates a new conversation when history can't be loaded
   * @param {string} reason - Optional reason to show why a new conversation was created
   */
  createNewConversation(reason) {
    console.log("Creating new conversation" + (reason ? `: ${reason}` : ""));
    
    // Clear localStorage conversation ID
    localStorage.removeItem('metis_conversation_id');
    this.currentConversationId = null;
    
    // Clear chat container
    if (this.elements.chatContainer) {
      this.elements.chatContainer.innerHTML = '';
      
      // Add welcome message
      this.elements.chatContainer.innerHTML = `
        <div class="message bot-message">
          <div class="message-header">Metis:</div>
          <div class="message-content">
            Hello! I'm your Metis RAG assistant. Ask me anything about your uploaded documents or chat with me directly.
            ${reason ? `<div class="info-notice">${reason}</div>` : ''}
          </div>
        </div>
      `;
    }
    
    // Reset conversation memory
    window.conversation = {
      messages: [],
      metadata: {
        estimatedTokens: 0,
        maxTokens: 4096,
        lastUpdated: new Date().toISOString(),
        userId: localStorage.getItem('userId')
      }
    };
    
    // Save updated conversation to localStorage
    saveToLocalStorage();
  }
  
  /**
   * Sends a user message to the API
   * @param {string} message - The message to send
   */
  sendMessage(message) {
    if (!message) return;
    
    // Store a reference to the input element for re-focusing after response completes
    const inputElement = document.getElementById('user-input');
    
    // Show user message immediately
    this.messageList.addMessage('user', message);
    
    // Scroll to bottom of chat
    this.messageList.scrollToBottom();
    
    // Collect chat parameters
    const params = {
      message: message,
      conversation_id: this.currentConversationId
    };
    
    // Add selected model if available
    if (this.elements.modelSelect) {
      params.model = this.elements.modelSelect.value;
      console.log(`Using model: ${this.elements.modelSelect.value}`);
    } else {
      console.error("Model selection element not found");
    }
    
    // Add RAG-specific parameters if enabled
    if (this.useRag) {
      if (this.elements.maxResults) {
        params.max_results = parseInt(this.elements.maxResults.value, 10);
      }
      
      // Parse metadata filters if provided
      if (this.elements.metadataFilters && this.elements.metadataFilters.value.trim()) {
        try {
          params.metadata_filters = JSON.parse(this.elements.metadataFilters.value);
        } catch (e) {
          console.error('Invalid metadata filters JSON:', e);
          // Add error message to chat
          this.messageList.addMessage('bot', 'Error: Invalid metadata filters JSON. Please check your syntax.');
          return;
        }
      }
    }
    
    // Add temperature parameter if available
    if (this.elements.temperature) {
      params.temperature = parseFloat(this.elements.temperature.value);
    }
    
    // Set flags for RAG, streaming, and raw output
    params.use_rag = this.useRag;
    params.stream = this.useStreaming;
    params.raw_output = this.showRawOutput;
    params.raw_llm_output = this.showRawLlmOutput;
    
    // Show loading indicator
    this.setLoading(true);
    
    // Send to API using appropriate method based on streaming preference
    if (this.useStreaming) {
      this.sendStreamingMessage(params);
    } else {
      this.sendNonStreamingMessage(params);
    }
  }
  
  /**
   * Sends a message using streaming API
   * @param {Object} params - The message parameters
   */
  sendStreamingMessage(params) {
    // Prepare for streaming response
    const botMessageId = 'message-' + Date.now();
    const initialHtml = '<div class="message-header">Metis:</div><div class="message-content"></div>';
    
    // Add empty bot message container that will be filled incrementally
    const messageElement = this.messageList.addRawHtmlMessage('bot', initialHtml, botMessageId);
    const contentContainer = messageElement.querySelector('.message-content');
    
    // Set up event source for streaming
    this.currentController = sendStreamingMessage(
      params,
      // onStart
      () => {
        console.log('Streaming started');
      },
      // onToken
      (data) => {
        // Update conversation ID if provided
        if (data.conversation_id) {
          updateConversationId(data.conversation_id);
          this.currentConversationId = data.conversation_id;
        }
        
        // Update content based on response type
        if (data.content && contentContainer) {
          if (this.showRawOutput && data.raw_output) {
            contentContainer.innerHTML = MetisMarkdown.formatRawText(data.raw_output);
          } else if (this.showRawLlmOutput && data.raw_llm_output) {
            contentContainer.innerHTML = MetisMarkdown.formatRawText(data.raw_llm_output);
          } else {
            contentContainer.innerHTML = MetisMarkdown.processResponse(data.content);
            MetisMarkdown.initializeHighlighting(contentContainer);
            MetisMarkdown.addCopyButtons(contentContainer);
          }
        }
        
        // Update sources if provided
        if (data.sources && data.sources.length > 0) {
          this.citations.updateMessageSources(messageElement, data.sources);
        }
        
        // Update token usage if provided
        if (data.usage) {
          this.updateTokenUsage(data.usage);
        }
        
        // Scroll to bottom with each update
        this.messageList.scrollToBottom();
      },
      // onComplete
      () => {
        // Stream closed successfully
        this.currentController = null;
        this.setLoading(false);
      },
      // onError
      (err) => {
        handleStreamError(err, contentContainer, this.currentController, (isLoading) => this.setLoading(isLoading));
      }
    );
  }
  
  /**
   * Sends a message using non-streaming API
   * @param {Object} params - The message parameters
   */
  async sendNonStreamingMessage(params) {
    try {
      // Send the message
      const data = await sendNonStreamingMessage(params);
      
      // Update conversation ID if provided
      if (data.conversation_id) {
        updateConversationId(data.conversation_id);
        this.currentConversationId = data.conversation_id;
      }
      
      // Add message based on response type
      let messageElement;
      if (this.showRawOutput && data.raw_output) {
        messageElement = this.messageList.addMessage('bot', data.raw_output, true);
      } else if (this.showRawLlmOutput && data.raw_llm_output) {
        messageElement = this.messageList.addMessage('bot', data.raw_llm_output, true);
      } else {
        // Check if we have content in the response
        if (!data.message && !data.content) {
          messageElement = this.messageList.addMessage('bot', "Error: No response content received from the server.");
        } else {
          // Use message field if available (API response format), otherwise fall back to content
          const responseText = data.message || data.content;
          messageElement = this.messageList.addMessage('bot', responseText);
          
          // Add sources if available
          if (data.sources && data.sources.length > 0) {
            this.citations.updateMessageSources(messageElement, data.sources);
          }
        }
      }
      
      // Update token usage if provided
      if (data.usage) {
        this.updateTokenUsage(data.usage);
      }
    } catch (error) {
      handleApiError(error, null, (type, content) => this.messageList.addMessage(type, content));
    } finally {
      this.setLoading(false);
    }
  }
  
  /**
   * Updates the token usage display
   * @param {Object} usage - The token usage data
   */
  updateTokenUsage(usage) {
    if (!this.elements.tokenUsage || !this.elements.tokenUsageFill || !this.elements.tokenUsageText) return;
    
    const total = usage.total || 0;
    const max = usage.max || 4096;
    const percentage = Math.min(100, (total / max) * 100);
    
    // Update fill and text
    this.elements.tokenUsageFill.style.width = `${percentage}%`;
    this.elements.tokenUsageText.textContent = `${total} / ${max} tokens`;
    
    // Show the token usage indicator
    this.elements.tokenUsage.style.display = 'block';
    
    // Update color based on usage
    if (percentage > 90) {
      this.elements.tokenUsageFill.style.backgroundColor = 'var(--error-color)';
    } else if (percentage > 75) {
      this.elements.tokenUsageFill.style.backgroundColor = 'var(--warning-color)';
    } else {
      this.elements.tokenUsageFill.style.backgroundColor = 'var(--ginkgo-green)';
    }
  }
  
  /**
   * Sets the loading state
   * @param {boolean} isLoading - Whether loading is active
   */
  setLoading(isLoading) {
    if (!this.elements.loadingIndicator) return;
    
    if (isLoading) {
      this.elements.loadingIndicator.classList.add('show');
      this.inputArea.setDisabled(true);
    } else {
      this.elements.loadingIndicator.classList.remove('show');
      this.inputArea.setDisabled(false);
      
      // Re-focus the input element after response is complete
      this.inputArea.focus();
    }
  }
  
  /**
   * Clears the chat history
   */
  clearChat() {
    if (!this.elements.chatContainer) return;
    
    // Confirm with the user
    if (!confirm('Are you sure you want to clear the chat history?')) {
      return;
    }
    
    // Clear conversation ID
    this.currentConversationId = null;
    localStorage.removeItem('metis_conversation_id');
    
    // Clear chat UI
    this.elements.chatContainer.innerHTML = `
      <div class="message bot-message">
        <div class="message-header">Metis:</div>
        <div class="message-content">Hello! I'm your Metis RAG assistant. Ask me anything about your uploaded documents or chat with me directly.</div>
      </div>
    `;
    
    // Reset token usage
    if (this.elements.tokenUsage) {
      this.elements.tokenUsage.style.display = 'none';
    }
    
    // Refocus on the input field
    if (this.inputArea) {
      this.inputArea.focus();
    }
  }
  
  /**
   * Saves the chat history
   */
  saveChat() {
    if (!this.elements.chatContainer) return;
    
    // Get all messages
    const messages = this.elements.chatContainer.querySelectorAll('.message');
    let chatText = '';
    
    messages.forEach(message => {
      const header = message.querySelector('.message-header');
      const content = message.querySelector('.message-content');
      
      if (header && content) {
        chatText += `${header.textContent}\n`;
        chatText += `${content.innerText}\n\n`;
      }
    });
    
    // Create a download link
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `metis-chat-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    
    // Clean up
    URL.revokeObjectURL(url);
    
    // Refocus on the input field after saving
    if (this.inputArea) {
      this.inputArea.focus();
    }
  }
}

// Export the ChatInterface class
export { ChatInterface };