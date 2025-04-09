/**
 * Input Area Component
 * Handles user input and message sending
 */

/**
 * InputArea class
 * Manages the user input field and send button
 */
class InputArea {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    // Configuration with defaults
    this.config = {
      inputSelector: '#user-input',
      sendButtonSelector: '#send-button',
      onSend: null, // Callback function when a message is sent
      ...config
    };
    
    // DOM Elements
    this.inputElement = document.querySelector(this.config.inputSelector);
    this.sendButton = document.querySelector(this.config.sendButtonSelector);
    
    // Validate required elements
    if (!this.inputElement || !this.sendButton) {
      console.error('InputArea: Required elements not found');
      return;
    }
    
    // Set up event listeners
    this.setupEventListeners();
  }
  
  /**
   * Set up event listeners for input and send button
   */
  setupEventListeners() {
    // Send button click
    this.sendButton.addEventListener('click', () => {
      console.log("Send button clicked");
      this.sendMessage();
    });
    
    // Enter key press (without shift)
    this.inputElement.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        console.log("Enter key pressed (without shift)");
        e.preventDefault();
        this.sendMessage();
      }
    });
    
    // Auto-resize textarea as user types
    this.inputElement.addEventListener('input', () => {
      this.autoResizeTextarea();
    });
    
    console.log("Input area event listeners set up successfully");
  }
  
  /**
   * Send the current message
   */
  sendMessage() {
    const message = this.inputElement.value.trim();
    if (!message) {
      console.log("No message to send - input is empty");
      return;
    }
    
    console.log(`Sending message: "${message.substring(0, 30)}${message.length > 30 ? '...' : ''}"`);
    
    // Call the onSend callback if provided
    if (typeof this.config.onSend === 'function') {
      try {
        this.config.onSend(message);
      } catch (error) {
        console.error("Error in onSend callback:", error);
        alert("There was an error sending your message. Please try again.");
        return;
      }
    } else {
      console.error("No onSend callback provided");
    }
    
    // Clear input
    this.inputElement.value = '';
    
    // Reset height
    this.inputElement.style.height = 'auto';
    
    // Keep focus on the input element
    this.inputElement.focus();
    
    console.log("Message sent successfully");
  }
  
  /**
   * Auto-resize the textarea based on content
   */
  autoResizeTextarea() {
    if (!this.inputElement) return;
    
    // Reset height to auto to get the correct scrollHeight
    this.inputElement.style.height = 'auto';
    
    // Set the height to the scrollHeight
    const newHeight = Math.min(this.inputElement.scrollHeight, 200); // Max height of 200px
    this.inputElement.style.height = `${newHeight}px`;
  }
  
  /**
   * Set the disabled state of the input and send button
   * @param {boolean} disabled - Whether the input should be disabled
   */
  setDisabled(disabled) {
    if (this.inputElement) {
      this.inputElement.disabled = disabled;
    }
    
    if (this.sendButton) {
      this.sendButton.disabled = disabled;
    }
  }
  
  /**
   * Focus the input field
   */
  focus() {
    if (this.inputElement) {
      // Use setTimeout to ensure focus works even when called during other operations
      setTimeout(() => {
        this.inputElement.focus();
        
        // Place cursor at the end of any existing text
        const textLength = this.inputElement.value.length;
        if (textLength > 0) {
          this.inputElement.setSelectionRange(textLength, textLength);
        }
      }, 0);
    }
  }
  
  /**
   * Get the current input value
   * @returns {string} The current input value
   */
  getValue() {
    return this.inputElement ? this.inputElement.value.trim() : '';
  }
  
  /**
   * Set the input value
   * @param {string} value - The value to set
   */
  setValue(value) {
    if (this.inputElement) {
      this.inputElement.value = value;
      this.autoResizeTextarea();
    }
  }
}

// Export the InputArea class
export { InputArea };