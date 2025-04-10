/**
 * Chat State Management
 * Manages the state of the chat interface and conversation
 */

/**
 * ChatState class
 * Manages the state of the chat interface and conversation
 */
class ChatState {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    // Configuration with defaults
    this.config = {
      ...config
    };
    
    // Initialize state
    this.state = {
      conversationId: null,
      messages: [],
      isLoading: false,
      error: null,
      tokenUsage: {
        total: 0,
        max: 4096
      }
    };
    
    // Event listeners
    this.listeners = {
      stateChange: [],
      messageAdded: [],
      conversationIdChanged: [],
      loadingChanged: [],
      errorOccurred: [],
      tokenUsageChanged: []
    };
    
    // Load initial state from localStorage
    this.loadFromLocalStorage();
  }
  
  /**
   * Load state from localStorage
   */
  loadFromLocalStorage() {
    // Load conversation ID
    const conversationId = localStorage.getItem('metis_conversation_id');
    if (conversationId) {
      this.state.conversationId = conversationId;
    }
    
    // Load conversation
    const conversationJson = localStorage.getItem('metis_conversation');
    if (conversationJson) {
      try {
        const conversation = JSON.parse(conversationJson);
        if (conversation && conversation.messages) {
          this.state.messages = conversation.messages;
          
          // Update token usage if available
          if (conversation.metadata && conversation.metadata.estimatedTokens) {
            this.state.tokenUsage.total = conversation.metadata.estimatedTokens;
          }
          
          if (conversation.metadata && conversation.metadata.maxTokens) {
            this.state.tokenUsage.max = conversation.metadata.maxTokens;
          }
        }
      } catch (error) {
        console.error('Error parsing conversation from localStorage:', error);
      }
    }
  }
  
  /**
   * Save state to localStorage
   */
  saveToLocalStorage() {
    // Save conversation ID
    if (this.state.conversationId) {
      localStorage.setItem('metis_conversation_id', this.state.conversationId);
    } else {
      localStorage.removeItem('metis_conversation_id');
    }
    
    // Save conversation
    const conversation = {
      messages: this.state.messages,
      metadata: {
        estimatedTokens: this.state.tokenUsage.total,
        maxTokens: this.state.tokenUsage.max,
        lastUpdated: new Date().toISOString(),
        userId: localStorage.getItem('userId')
      }
    };
    
    localStorage.setItem('metis_conversation', JSON.stringify(conversation));
  }
  
  /**
   * Get the current state
   * @returns {Object} The current state
   */
  getState() {
    return { ...this.state };
  }
  
  /**
   * Update the state
   * @param {Object} newState - The new state to merge with the current state
   */
  setState(newState) {
    const oldState = { ...this.state };
    this.state = { ...this.state, ...newState };
    
    // Save to localStorage
    this.saveToLocalStorage();
    
    // Notify listeners
    this.notifyListeners('stateChange', this.state, oldState);
    
    // Check for specific changes
    if (newState.conversationId !== undefined && newState.conversationId !== oldState.conversationId) {
      this.notifyListeners('conversationIdChanged', newState.conversationId, oldState.conversationId);
    }
    
    if (newState.isLoading !== undefined && newState.isLoading !== oldState.isLoading) {
      this.notifyListeners('loadingChanged', newState.isLoading, oldState.isLoading);
    }
    
    if (newState.error !== undefined && newState.error !== oldState.error) {
      this.notifyListeners('errorOccurred', newState.error, oldState.error);
    }
    
    if (newState.tokenUsage !== undefined && JSON.stringify(newState.tokenUsage) !== JSON.stringify(oldState.tokenUsage)) {
      this.notifyListeners('tokenUsageChanged', newState.tokenUsage, oldState.tokenUsage);
    }
  }
  
  /**
   * Add a message to the state
   * @param {Object} message - The message to add
   */
  addMessage(message) {
    const newMessages = [...this.state.messages, message];
    this.setState({ messages: newMessages });
    
    // Notify message added listeners
    this.notifyListeners('messageAdded', message, this.state.messages);
  }
  
  /**
   * Set the conversation ID
   * @param {string} conversationId - The new conversation ID
   */
  setConversationId(conversationId) {
    this.setState({ conversationId });
  }
  
  /**
   * Set the loading state
   * @param {boolean} isLoading - Whether the chat is loading
   */
  setLoading(isLoading) {
    this.setState({ isLoading });
  }
  
  /**
   * Set an error
   * @param {Error|string} error - The error that occurred
   */
  setError(error) {
    this.setState({ error });
  }
  
  /**
   * Update token usage
   * @param {Object} tokenUsage - The token usage data
   */
  updateTokenUsage(tokenUsage) {
    this.setState({ tokenUsage: { ...this.state.tokenUsage, ...tokenUsage } });
  }
  
  /**
   * Clear the conversation
   */
  clearConversation() {
    this.setState({
      conversationId: null,
      messages: [],
      tokenUsage: {
        total: 0,
        max: this.state.tokenUsage.max
      }
    });
  }
  
  /**
   * Add an event listener
   * @param {string} event - The event to listen for
   * @param {Function} callback - The callback function
   * @returns {Function} A function to remove the listener
   */
  addEventListener(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    
    this.listeners[event].push(callback);
    
    // Return a function to remove the listener
    return () => {
      this.removeEventListener(event, callback);
    };
  }
  
  /**
   * Remove an event listener
   * @param {string} event - The event to stop listening for
   * @param {Function} callback - The callback function to remove
   */
  removeEventListener(event, callback) {
    if (!this.listeners[event]) return;
    
    this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
  }
  
  /**
   * Notify listeners of an event
   * @param {string} event - The event that occurred
   * @param {*} newValue - The new value
   * @param {*} oldValue - The old value
   */
  notifyListeners(event, newValue, oldValue) {
    if (!this.listeners[event]) return;
    
    this.listeners[event].forEach(callback => {
      try {
        callback(newValue, oldValue);
      } catch (error) {
        console.error(`Error in ${event} listener:`, error);
      }
    });
  }
}

// Create a singleton instance
const chatState = new ChatState();

// Export the singleton instance
export { chatState };