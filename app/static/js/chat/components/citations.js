/**
 * Citations Component
 * Handles the display and management of citation sources
 */

/**
 * Citations class
 * Manages the display and interaction with citation sources
 */
class Citations {
  /**
   * Constructor
   * @param {Object} config - Configuration options
   */
  constructor(config = {}) {
    // Configuration with defaults
    this.config = {
      ...config
    };
  }
  
  /**
   * Updates a message with citation sources
   * @param {HTMLElement} messageElement - The message element
   * @param {Array} sources - The sources data
   */
  updateMessageSources(messageElement, sources) {
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
      
      // Add click handler to show source details
      sourceItem.addEventListener('click', () => {
        this.showSourceDetails(source);
      });
      
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
        this.saveToLocalStorage();
        console.log("Updated sources in conversation memory");
      }
    }
  }
  
  /**
   * Show detailed information about a source
   * @param {Object} source - The source data
   */
  showSourceDetails(source) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('source-details-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'source-details-modal';
      modal.className = 'modal';
      modal.innerHTML = `
        <div class="modal-content">
          <span class="close">&times;</span>
          <h2>Source Details</h2>
          <div class="source-content"></div>
        </div>
      `;
      document.body.appendChild(modal);
      
      // Add close button functionality
      const closeBtn = modal.querySelector('.close');
      closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
      });
      
      // Close when clicking outside the modal
      window.addEventListener('click', (event) => {
        if (event.target === modal) {
          modal.style.display = 'none';
        }
      });
    }
    
    // Update modal content
    const sourceContent = modal.querySelector('.source-content');
    
    // Format source details
    let content = '';
    
    // Document info
    if (source.metadata) {
      content += '<h3>Document Information</h3>';
      content += '<table class="source-details-table">';
      
      if (source.metadata.filename || source.metadata.title) {
        content += `<tr><td>Title:</td><td>${source.metadata.title || source.metadata.filename}</td></tr>`;
      }
      
      if (source.metadata.source) {
        content += `<tr><td>Source:</td><td>${source.metadata.source}</td></tr>`;
      }
      
      if (source.metadata.author) {
        content += `<tr><td>Author:</td><td>${source.metadata.author}</td></tr>`;
      }
      
      if (source.metadata.date) {
        content += `<tr><td>Date:</td><td>${source.metadata.date}</td></tr>`;
      }
      
      if (source.metadata.page) {
        content += `<tr><td>Page:</td><td>${source.metadata.page}</td></tr>`;
      }
      
      content += '</table>';
    }
    
    // Relevance info
    content += '<h3>Relevance Information</h3>';
    content += '<table class="source-details-table">';
    content += `<tr><td>Score:</td><td>${source.score ? source.score.toFixed(4) : 'N/A'}</td></tr>`;
    
    if (source.document_id) {
      content += `<tr><td>Document ID:</td><td>${source.document_id}</td></tr>`;
    }
    
    if (source.chunk_id) {
      content += `<tr><td>Chunk ID:</td><td>${source.chunk_id}</td></tr>`;
    }
    
    content += '</table>';
    
    // Excerpt
    if (source.excerpt) {
      content += '<h3>Excerpt</h3>';
      content += `<div class="source-excerpt">${source.excerpt}</div>`;
    }
    
    sourceContent.innerHTML = content;
    
    // Show the modal
    modal.style.display = 'block';
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

// Export the Citations class
export { Citations };