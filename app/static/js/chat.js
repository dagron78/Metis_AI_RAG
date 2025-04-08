/**
 * Metis RAG Chat Interface
 * Handles user interactions, message display, and API communication
 */

// Main Chat Application
const MetisChat = (function() {
  // Private variables
  let currentConversationId = null;
  let useStreaming = true;
  let useRag = true;
  let showRawOutput = false;
  let showRawLlmOutput = false;
  let currentController = null; // For aborting fetch requests
  
  // DOM Elements
  let elements = {};
  
  /**
   * Initializes the chat application
   */
  function initialize() {
    console.log('Initializing chat interface');
    
    // Get DOM elements
    cacheElements();
    
    // Load initial state
    loadInitialState();
    
    // Set up event listeners
    setupEventListeners();
  }
  
  /**
   * Cache DOM elements for better performance
   */
  function cacheElements() {
    elements = {
      chatContainer: document.getElementById('chat-container'),
      userInput: document.getElementById('user-input'),
      sendButton: document.getElementById('send-button'),
      clearButton: document.getElementById('clear-chat'),
      saveButton: document.getElementById('save-chat'),
      modelSelect: document.getElementById('model'),
      ragToggle: document.getElementById('rag-toggle'),
      streamToggle: document.getElementById('stream-toggle'),
      rawOutputToggle: document.getElementById('raw-output-toggle'),
      rawLlmOutputToggle: document.getElementById('raw-llm-output-toggle'),
      loadingIndicator: document.getElementById('loading'),
      maxResults: document.getElementById('max-results'),
      temperature: document.getElementById('temperature'),
      metadataFilters: document.getElementById('metadata-filters'),
      tokenUsage: document.getElementById('token-usage'),
      tokenUsageFill: document.getElementById('token-usage-fill'),
      tokenUsageText: document.getElementById('token-usage-text'),
      advancedToggle: document.getElementById('advanced-toggle'),
      advancedContent: document.getElementById('advanced-content'),
      advancedIcon: document.getElementById('advanced-icon')
    };
    
    // Validate required elements
    validateElements();
  }
  
  /**
   * Validate that required elements exist
   */
  function validateElements() {
    const requiredElements = ['chatContainer', 'userInput', 'sendButton'];
    let missing = false;
    
    requiredElements.forEach(key => {
      if (!elements[key]) {
        console.error(`Required element missing: ${key}`);
        missing = true;
      }
    });
    
    if (missing) {
      console.error("Some required chat UI elements are missing. Chat functionality may be limited.");
    }
  }
  
  /**
   * Load initial state from localStorage and API
   */
  function loadInitialState() {
    // Conversation ID
    const storedConversationId = localStorage.getItem('metis_conversation_id');
    if (storedConversationId) {
      currentConversationId = storedConversationId;
      
      // Load conversation history for the stored ID
      loadConversationHistory(storedConversationId);
    }
    
    // Toggle states
    if (elements.ragToggle) {
      useRag = localStorage.getItem('metis_use_rag') !== 'false';
      elements.ragToggle.checked = useRag;
    }
    
    if (elements.streamToggle) {
      useStreaming = localStorage.getItem('metis_use_streaming') !== 'false';
      elements.streamToggle.checked = useStreaming;
    }
    
    if (elements.rawOutputToggle) {
      showRawOutput = localStorage.getItem('metis_show_raw_output') === 'true';
      elements.rawOutputToggle.checked = showRawOutput;
    }
    
    if (elements.rawLlmOutputToggle) {
      showRawLlmOutput = localStorage.getItem('metis_show_raw_llm_output') === 'true';
      elements.rawLlmOutputToggle.checked = showRawLlmOutput;
    }
    
    // Load available models
    loadModels();
    
    // Advanced options toggle state
    if (elements.advancedContent && elements.advancedToggle) {
      const showAdvanced = localStorage.getItem('metis_show_advanced') === 'true';
      if (showAdvanced) {
        elements.advancedContent.classList.add('show');
        elements.advancedIcon.classList.replace('fa-chevron-down', 'fa-chevron-up');
      }
    }
  }
  
  /**
   * Load conversation history from the server
   * @param {string} conversationId - The ID of the conversation to load
   */
  function loadConversationHistory(conversationId) {
    if (!conversationId || !elements.chatContainer) return;
    
    // Show loading indicator in chat container
    elements.chatContainer.innerHTML = '<div class="loading-history">Loading conversation history...</div>';
    
    // Clear existing conversation array
    window.conversation = {
        messages: [],
        metadata: {
            estimatedTokens: 0,
            maxTokens: 4096,
            lastUpdated: new Date().toISOString()
        }
    };
    
    // Fetch conversation history from the server
    authenticatedFetch(`/api/chat/history?conversation_id=${conversationId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Failed to load conversation history: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // Clear loading indicator
        elements.chatContainer.innerHTML = '';
        
        if (data.messages && data.messages.length > 0) {
          // Add each message to the chat
          data.messages.forEach(message => {
            // Check if message has content
            if (!message.content) return;
            
            // Add message to UI
            const messageElement = addMessage(message.role, message.content);
            
            // If this is an assistant message and has citations, add them
            if (message.role === 'assistant' && message.citations && message.citations.length > 0) {
              updateMessageSources(messageElement, message.citations);
            }
            
            // Add to window.conversation for context memory
            window.conversation.messages.push({
              role: message.role,
              content: message.content,
              sources: message.citations || null,
              timestamp: message.timestamp || new Date().toISOString()
            });
            
            // Update estimated tokens
            window.conversation.metadata.estimatedTokens += estimateTokens(message.content);
          });
          
          // Update lastUpdated timestamp
          window.conversation.metadata.lastUpdated = new Date().toISOString();
          
          // Save updated conversation to localStorage
          saveToLocalStorage();
          
          console.log(`Loaded ${data.messages.length} messages into conversation memory`);
        } else {
          // If no messages, add the default welcome message
          elements.chatContainer.innerHTML = `
            <div class="message bot-message">
              <div class="message-header">Metis:</div>
              <div class="message-content">Hello! I'm your Metis RAG assistant. Ask me anything about your uploaded documents or chat with me directly.</div>
            </div>
          `;
        }
        
        // Scroll to bottom of chat
        scrollToBottom();
      })
      .catch(error => {
        console.error('Error loading conversation history:', error);
        // Show error message
        elements.chatContainer.innerHTML = `
          <div class="message bot-message">
            <div class="message-header">Metis:</div>
            <div class="message-content">
              Unable to load conversation history. Starting a new conversation.
              <div class="error-details">${error.message}</div>
            </div>
          </div>
        `;
      });
  }
  
  /**
   * Set up event listeners for UI interactions
   */
  function setupEventListeners() {
    // Send message events
    if (elements.sendButton) {
      elements.sendButton.addEventListener('click', sendMessage);
    }
    
    if (elements.userInput) {
      elements.userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage();
        }
      });
    }
    
    // Other UI controls
    if (elements.clearButton) {
      elements.clearButton.addEventListener('click', clearChat);
    }
    
    if (elements.saveButton) {
      elements.saveButton.addEventListener('click', saveChat);
    }
    
    // Toggle buttons
    if (elements.ragToggle) {
      elements.ragToggle.addEventListener('change', function() {
        useRag = this.checked;
        localStorage.setItem('metis_use_rag', useRag);
        
        // Show/hide RAG-specific parameters
        const ragParams = document.querySelectorAll('.rag-param');
        ragParams.forEach(param => {
          param.style.display = useRag ? 'block' : 'none';
        });
      });
    }
    
    if (elements.streamToggle) {
      elements.streamToggle.addEventListener('change', function() {
        useStreaming = this.checked;
        localStorage.setItem('metis_use_streaming', useStreaming);
      });
    }
    
    if (elements.rawOutputToggle) {
      elements.rawOutputToggle.addEventListener('change', function() {
        showRawOutput = this.checked;
        localStorage.setItem('metis_show_raw_output', showRawOutput);
      });
    }
    
    if (elements.rawLlmOutputToggle) {
      elements.rawLlmOutputToggle.addEventListener('change', function() {
        showRawLlmOutput = this.checked;
        localStorage.setItem('metis_show_raw_llm_output', showRawLlmOutput);
      });
    }
    
    // Advanced options toggle
    if (elements.advancedToggle && elements.advancedContent && elements.advancedIcon) {
      elements.advancedToggle.addEventListener('click', function() {
        elements.advancedContent.classList.toggle('show');
        
        // Toggle icon
        if (elements.advancedContent.classList.contains('show')) {
          elements.advancedIcon.classList.replace('fa-chevron-down', 'fa-chevron-up');
          localStorage.setItem('metis_show_advanced', 'true');
        } else {
          elements.advancedIcon.classList.replace('fa-chevron-up', 'fa-chevron-down');
          localStorage.setItem('metis_show_advanced', 'false');
        }
      });
    }
  }
  
  /**
   * Fetches available models and populates the dropdown
   */
  function loadModels() {
    if (!elements.modelSelect) return;
    
    // Use a try-catch for model loading to handle unauthorized errors gracefully
    try {
      authenticatedFetch('/api/system/models')
      .then(response => {
        if (!response.ok) {
          // Use default models if unauthorized
          if (response.status === 401) {
            return { models: [{ name: 'llama3' }] };
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(models => {
        elements.modelSelect.innerHTML = ''; // Clear existing options
        
        if (Array.isArray(models) && models.length > 0) {
          models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = model.name;
            elements.modelSelect.appendChild(option);
          });
        } else {
          // Fallback default
          const option = document.createElement('option');
          option.value = 'gemma3:4b';
          option.textContent = 'gemma3:4b (default)';
          elements.modelSelect.appendChild(option);
        }
      })
      .catch(error => {
        console.error('Error loading models:', error);
        // Add a default model option
        elements.modelSelect.innerHTML = '<option value="llama3">llama3 (default)</option>';
      });
    } catch (error) {
      console.error('Error in model loading:', error);
      elements.modelSelect.innerHTML = '<option value="llama3">llama3 (default)</option>';
    }
  }
  
  /**
   * Updates and stores the current conversation ID
   * @param {string} id - The new conversation ID
   */
  function updateConversationId(id) {
    if (!id) return;
    
    if (id !== currentConversationId) {
      currentConversationId = id;
      localStorage.setItem('metis_conversation_id', id);
    }
  }
  
  /**
   * Sends a user message to the API
   */
  function sendMessage() {
    if (!elements.userInput || !elements.chatContainer) return;
    
    const message = elements.userInput.value.trim();
    if (!message) return;
    
    // Show user message immediately
    addMessage('user', message);
    
    // Clear input
    elements.userInput.value = '';
    
    // Scroll to bottom of chat
    scrollToBottom();
    
    // Collect chat parameters
    const params = {
      message: message,
      conversation_id: currentConversationId
    };
    
    // Add selected model if available
    if (elements.modelSelect) {
      params.model = elements.modelSelect.value;
    }
    
    // Add RAG-specific parameters if enabled
    if (useRag) {
      if (elements.maxResults) {
        params.max_results = parseInt(elements.maxResults.value, 10);
      }
      
      // Parse metadata filters if provided
      if (elements.metadataFilters && elements.metadataFilters.value.trim()) {
        try {
          params.metadata_filters = JSON.parse(elements.metadataFilters.value);
        } catch (e) {
          console.error('Invalid metadata filters JSON:', e);
          // Add error message to chat
          addMessage('bot', 'Error: Invalid metadata filters JSON. Please check your syntax.');
          return;
        }
      }
    }
    
    // Add temperature parameter if available
    if (elements.temperature) {
      params.temperature = parseFloat(elements.temperature.value);
    }
    
    // Set flags for RAG, streaming, and raw output
    params.use_rag = useRag;
    params.stream = useStreaming;
    params.raw_output = showRawOutput;
    params.raw_llm_output = showRawLlmOutput;
    
    // Show loading indicator
    setLoading(true);
    
    // Send to API using appropriate method based on streaming preference
    if (useStreaming) {
      sendStreamingMessage(params);
    } else {
      sendNonStreamingMessage(params);
    }
  }
  
  /**
   * Sends a message using streaming API
   * @param {Object} params - The message parameters
   */
  function sendStreamingMessage(params) {
    // Prepare for streaming response
    const botMessageId = 'message-' + Date.now();
    const initialHtml = '<div class="message-header">Metis:</div><div class="message-content"></div>';
    
    // Add empty bot message container that will be filled incrementally
    const messageElement = addRawHtmlMessage('bot', initialHtml, botMessageId);
    const contentContainer = messageElement.querySelector('.message-content');
    
    // Create abort controller for the fetch
    currentController = new AbortController();
    const signal = currentController.signal;
    
    // Set up event source for streaming
    fetchEventSource('/api/chat/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify(params),
      signal: signal,
      onopen(response) {
        if (response.ok) {
          return; // Connection established successfully
        }
        throw new Error(`Failed to connect: ${response.status} ${response.statusText}`);
      },
      onmessage(event) {
        try {
          if (!event.data) return;
          
          // Attempt to parse JSON response
          const data = JSON.parse(event.data);
          
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
        } catch (error) {
          console.error('Error processing streaming message:', error);
        }
      },
      onerror(err) {
        console.error('Stream error:', err);
        
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
              if (messageElement) {
                messageElement.remove();
              }
              sendMessage();
            });
          }
        }
        
        // Close the stream
        if (currentController) {
          currentController.abort();
          currentController = null;
        }
        
        setLoading(false);
      },
      onclose() {
        // Stream closed successfully
        currentController = null;
        setLoading(false);
      }
    });
  }
  
  /**
   * Sends a message using non-streaming API
   * @param {Object} params - The message parameters
   */
  function sendNonStreamingMessage(params) {
    // Add console logging to debug response issues
    console.log("Sending non-streaming query:", params);
    
    authenticatedFetch('/api/chat/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    })
    .then(response => {
      console.log("Received API response status:", response.status);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      // Log the response data for debugging
      console.log("Received response data:", data);
      
      // Update conversation ID if provided
      if (data.conversation_id) {
        updateConversationId(data.conversation_id);
      }
      
      // Add message based on response type
      if (showRawOutput && data.raw_output) {
        console.log("Displaying raw output:", data.raw_output.substring(0, 100) + "...");
        const messageElement = addMessage('bot', data.raw_output, true);
      } else if (showRawLlmOutput && data.raw_llm_output) {
        console.log("Displaying raw LLM output:", data.raw_llm_output.substring(0, 100) + "...");
        const messageElement = addMessage('bot', data.raw_llm_output, true);
      } else {
        // Check if we have content in the response
        if (!data.message && !data.content) {
          console.error("No content or message found in response:", data);
          const messageElement = addMessage('bot', "Error: No response content received from the server.");
        } else {
          // Use message field if available (API response format), otherwise fall back to content
          const responseText = data.message || data.content;
          console.log("Displaying formatted response:", responseText.substring(0, 100) + "...");
          const messageElement = addMessage('bot', responseText);
          
          // Add sources if available
          if (data.sources && data.sources.length > 0) {
            console.log("Adding sources to message:", data.sources.length);
            updateMessageSources(messageElement, data.sources);
          }
        }
      }
      
      // Update token usage if provided
      if (data.usage) {
        updateTokenUsage(data.usage);
      }
    })
    .catch(error => {
      console.error('Error sending message:', error);
      addMessage('bot', `Error: ${error.message}`);
    })
    .finally(() => {
      setLoading(false);
    });
  }
  
  /**
   * Adds a message to the chat container
   * @param {string} type - The message type ('user' or 'bot')
   * @param {string} content - The message content
   * @param {boolean} isRaw - Whether the content is raw text
   * @param {boolean} storeOnly - If true, only add to memory without displaying in UI
   * @returns {HTMLElement} The created message element
   */
  function addMessage(type, content, isRaw = false, storeOnly = false) {
    if (!content) return null;
    
    // Store in conversation memory for context
    const sources = null; // Will be updated later for bot messages with citations
    
    if (window.conversation && !storeOnly) {
      // Add to conversation array for context in future messages
      window.conversation.messages.push({
        role: type,
        content: content,
        sources: sources,
        timestamp: new Date().toISOString()
      });
      
      // Update token estimate
      const tokens = estimateTokens(content);
      window.conversation.metadata.estimatedTokens += tokens;
      window.conversation.metadata.lastUpdated = new Date().toISOString();
      
      // Save to localStorage for persistence
      saveToLocalStorage();
      
      console.log(`Added ${type} message to conversation memory, tokens: ${tokens}`);
    }
    
    // If store only, don't add to UI
    if (storeOnly || !elements.chatContainer) return null;
    
    console.log(`Adding ${type} message to UI, raw: ${isRaw}, content length: ${content.length}`);
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}-message`;
    messageElement.id = 'message-' + Date.now();
    
    let messageContent = '';
    
    if (type === 'user') {
      messageContent = `
        <div class="message-header">You:</div>
        <div class="message-content">${escapeHtml(content)}</div>
      `;
    } else {
      // For bot messages, process markdown unless it's raw
      const contentHtml = isRaw 
        ? `<pre class="raw-output">${escapeHtml(content)}</pre>`
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
        copyMessageContent(messageElement);
      });
      messageElement.appendChild(copyButton);
      
      // Apply syntax highlighting and add copy buttons to code blocks
      const contentDiv = messageElement.querySelector('.message-content');
      if (contentDiv && !isRaw) {
        MetisMarkdown.initializeHighlighting(contentDiv);
        MetisMarkdown.addCopyButtons(contentDiv);
      }
    }
    
    elements.chatContainer.appendChild(messageElement);
    scrollToBottom();
    
    return messageElement;
  }
  
  /**
   * Adds a message with raw HTML content
   * @param {string} type - The message type ('user' or 'bot')
   * @param {string} html - The HTML content
   * @param {string} id - Optional ID for the message element
   * @returns {HTMLElement} The created message element
   */
  function addRawHtmlMessage(type, html, id = null) {
    if (!elements.chatContainer) return null;
    
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
        copyMessageContent(messageElement);
      });
      messageElement.appendChild(copyButton);
    }
    
    elements.chatContainer.appendChild(messageElement);
    scrollToBottom();
    
    return messageElement;
  }
  
  /**
   * Updates a message with citation sources
   * @param {HTMLElement} messageElement - The message element
   * @param {Array} sources - The sources data
   */
  function updateMessageSources(messageElement, sources) {
    if (!messageElement || !sources || !sources.length) return;
    
    // Check if sources section already exists
    let sourcesSection = messageElement.querySelector('.sources-section');
    
    if (!sourcesSection) {
      // Create sources section
      sourcesSection = document.createElement('div');
      sourcesSection.className = 'sources-section';
      sourcesSection.innerHTML = '<div>Sources:</div>';
      
      // Add after message content
      const messageContent = messageElement.querySelector('.message-content');
      if (messageContent) {
        messageContent.after(sourcesSection);
      } else {
        messageElement.appendChild(sourcesSection);
      }
    }
    
    // Clear existing sources and add new ones
    sourcesSection.innerHTML = '<div>Sources:</div>';
    
    sources.forEach(source => {
      const sourceItem = document.createElement('span');
      sourceItem.className = 'source-item';
      
      // Format the source text based on available metadata
      let sourceName = source.metadata?.filename || source.metadata?.title || 'Source';
      if (source.metadata?.page) {
        sourceName += ` (p.${source.metadata.page})`;
      }
      
      sourceItem.textContent = sourceName;
      sourceItem.title = `Relevance score: ${source.score ? source.score.toFixed(2) : 'N/A'}`;
      
      sourcesSection.appendChild(sourceItem);
    });
    
    // Update sources in conversation memory
    if (window.conversation) {
      // Find the last message (should be the assistant/bot message)
      const lastMessage = window.conversation.messages[window.conversation.messages.length - 1];
      if (lastMessage && lastMessage.role === 'assistant') {
        // Update sources
        lastMessage.sources = sources;
        // Save to localStorage
        saveToLocalStorage();
        console.log("Updated sources in conversation memory");
      }
    }
  }
  
  /**
   * Updates the token usage display
   * @param {Object} usage - The token usage data
   */
  function updateTokenUsage(usage) {
    if (!elements.tokenUsage || !elements.tokenUsageFill || !elements.tokenUsageText) return;
    
    const total = usage.total || 0;
    const max = usage.max || 4096;
    const percentage = Math.min(100, (total / max) * 100);
    
    // Update fill and text
    elements.tokenUsageFill.style.width = `${percentage}%`;
    elements.tokenUsageText.textContent = `${total} / ${max} tokens`;
    
    // Show the token usage indicator
    elements.tokenUsage.style.display = 'block';
    
    // Update color based on usage
    if (percentage > 90) {
      elements.tokenUsageFill.style.backgroundColor = 'var(--error-color)';
    } else if (percentage > 75) {
      elements.tokenUsageFill.style.backgroundColor = 'var(--warning-color)';
    } else {
      elements.tokenUsageFill.style.backgroundColor = 'var(--ginkgo-green)';
    }
  }
  
  /**
   * Copies a message's content to clipboard
   * @param {HTMLElement} messageElement - The message element
   */
  function copyMessageContent(messageElement) {
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
   * Sets the loading state
   * @param {boolean} isLoading - Whether loading is active
   */
  function setLoading(isLoading) {
    if (!elements.loadingIndicator || !elements.sendButton) return;
    
    if (isLoading) {
      elements.loadingIndicator.classList.add('show');
      elements.sendButton.disabled = true;
    } else {
      elements.loadingIndicator.classList.remove('show');
      elements.sendButton.disabled = false;
    }
  }
  
  /**
   * Scrolls the chat container to the bottom
   */
  function scrollToBottom() {
    if (!elements.chatContainer) return;
    
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
  }
  
  /**
   * Clears the chat history
   */
  function clearChat() {
    if (!elements.chatContainer) return;
    
    // Confirm with the user
    if (!confirm('Are you sure you want to clear the chat history?')) {
      return;
    }
    
    // Clear conversation ID
    currentConversationId = null;
    localStorage.removeItem('metis_conversation_id');
    
    // Clear chat UI
    elements.chatContainer.innerHTML = `
      <div class="message bot-message">
        <div class="message-header">Metis:</div>
        <div class="message-content">Hello! I'm your Metis RAG assistant. Ask me anything about your uploaded documents or chat with me directly.</div>
      </div>
    `;
    
    // Reset token usage
    if (elements.tokenUsage) {
      elements.tokenUsage.style.display = 'none';
    }
  }
  
  /**
   * Saves the chat history
   */
  function saveChat() {
    if (!elements.chatContainer) return;
    
    // Get all messages
    const messages = elements.chatContainer.querySelectorAll('.message');
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
  }
  
  /**
   * Helper function to escape HTML in user input
   * @param {string} text - Text to escape
   * @returns {string} Escaped HTML
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
   * Gets the auth token from storage
   * @returns {string} Auth token
   */
  function getAuthToken() {
    return localStorage.getItem('metisToken') || sessionStorage.getItem('metisToken') || '';
  }
  
  // Return public API
  return {
    initialize,
    sendMessage,
    clearChat,
    saveChat
  };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  MetisChat.initialize();
});