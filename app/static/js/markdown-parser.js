/**
 * Markdown parser utility for Metis RAG
 * Handles formatting of markdown content, code blocks, and other structured elements
 */

// Define the MetisMarkdown namespace for better organization
window.MetisMarkdown = (function() {
  // Check if external dependencies are loaded
  if (typeof marked === 'undefined' || typeof hljs === 'undefined') {
    console.error("Error: Required libraries (marked.js and highlight.js) must be loaded first");
    // Return a basic implementation to prevent errors
    return {
      processResponse: (text) => {
        const el = document.createElement('div');
        el.textContent = text;
        return el.innerHTML;
      },
      initializeHighlighting: () => {},
      addCopyButtons: () => {}
    };
  }
  
  // Configure marked.js options
  marked.setOptions({
    highlight: function(code, lang) {
      // Use the provided language tag or fallback to plaintext
      const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
      
      try {
        return hljs.highlight(code, { language, ignoreIllegals: true }).value;
      } catch (e) {
        console.error('Error highlighting code:', e);
        // Fallback: return escaped code without highlighting
        const temp = document.createElement('div');
        temp.textContent = code;
        return temp.innerHTML;
      }
    },
    breaks: true, // Convert single newlines to <br> tags
    gfm: true,    // Enable GitHub Flavored Markdown
    headerIds: false,
    sanitize: false, // Allow HTML tags to be rendered
    mangle: false
  });

  // Get the renderer or create a new one
  let renderer;
  try {
    // Modern API
    renderer = marked.getRenderer();
  } catch (e) {
    // Fallback to older API
    renderer = new marked.Renderer();
    marked.setOptions({ renderer: renderer });
  }
  
  // Custom code renderer
  renderer.code = function(code, language) {
    const validLanguage = language && hljs.getLanguage(language) ? language : 'plaintext';
    try {
      const highlighted = hljs.highlight(code, { language: validLanguage, ignoreIllegals: true }).value;
      return `<div class="structured-code-block">
                <div class="code-block-header">${validLanguage}</div>
                <pre><code class="hljs language-${validLanguage}">${highlighted}</code></pre>
              </div>`;
    } catch (e) {
      console.error('Error in custom code renderer:', e);
      return `<div class="structured-code-block">
                <div class="code-block-header">${validLanguage}</div>
                <pre><code class="hljs language-${validLanguage}">${code}</code></pre>
              </div>`;
    }
  };
  
  // Custom paragraph renderer
  renderer.paragraph = function(text) {
    return `<p class="structured-paragraph">${text}</p>`;
  };
  
  // Custom heading renderer
  renderer.heading = function(text, level) {
    return `<h${level} class="structured-heading">${text}</h${level}>`;
  };
  
  // Custom blockquote renderer
  renderer.blockquote = function(quote) {
    return `<blockquote class="structured-quote">${quote}</blockquote>`;
  };
  
  // Custom list renderer
  renderer.list = function(body, ordered, start) {
    const type = ordered ? 'ol' : 'ul';
    const startAttr = (ordered && start !== 1) ? ` start="${start}"` : '';
    return `<${type}${startAttr} class="structured-list">${body}</${type}>`;
  };
  
  // Custom list item renderer
  renderer.listitem = function(text) {
    return `<li class="structured-list-item">${text}</li>`;
  };
  
  /**
   * Adds copy buttons to all code blocks in a container
   * @param {HTMLElement} container - The parent element containing code blocks
   */
  function addCopyButtons(container) {
    if (!container) return;
    
    const codeBlocks = container.querySelectorAll('pre code');
    
    codeBlocks.forEach(codeBlock => {
      // Skip if this code block already has a copy button
      if (codeBlock.parentNode.parentNode.querySelector('.copy-code-button')) {
        return;
      }
      
      const button = document.createElement('button');
      button.className = 'copy-code-button';
      button.innerHTML = '<i class="fas fa-copy"></i> Copy';
      
      // Add click event listener
      button.addEventListener('click', function() {
        const code = codeBlock.textContent;
        navigator.clipboard.writeText(code).then(() => {
          // Temporarily change button text to indicate success
          const originalText = button.innerHTML;
          button.innerHTML = '<i class="fas fa-check"></i> Copied!';
          setTimeout(() => {
            button.innerHTML = originalText;
          }, 2000);
        }).catch(err => {
          console.error('Failed to copy code: ', err);
          button.innerHTML = '<i class="fas fa-times"></i> Error!';
          setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy"></i> Copy';
          }, 2000);
        });
      });
      
      // For code blocks inside structured-code-block divs
      if (codeBlock.parentNode.parentNode.classList.contains('structured-code-block')) {
        codeBlock.parentNode.parentNode.appendChild(button);
      } else {
        // For regular code blocks
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-container';
        
        // Replace the <pre> with our wrapper
        const pre = codeBlock.parentNode;
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);
        wrapper.appendChild(button);
      }
    });
  }
  
  /**
   * Initializes syntax highlighting for all code blocks in a container
   * @param {HTMLElement} container - The parent element containing code blocks
   */
  function initializeHighlighting(container) {
    if (!container) return;
    
    // Only highlight code blocks that haven't been processed by our custom renderer
    const codeBlocks = container.querySelectorAll('pre code:not(.hljs)');
    codeBlocks.forEach(block => {
      hljs.highlightElement(block);
    });
  }
  
  /**
   * Processes a text response with markdown formatting
   * @param {string} text - The text to process
   * @return {string} HTML formatted content
   */
  function processResponse(text) {
    if (!text) return '';
    
    try {
      // Process the markdown
      const html = marked.parse(text); // Use marked.parse() for v4+
      
      // Add class for styling
      return `<div class="markdown-processed">${html}</div>`;
    } catch (error) {
      console.error('Error processing markdown:', error);
      // Fallback: return escaped HTML
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
  }
  
  /**
   * Formats raw text by preserving whitespace and line breaks
   * @param {string} text - The raw text to format
   * @return {string} HTML with preserved formatting
   */
  function formatRawText(text) {
    if (!text) return '';
    
    // Escape HTML and preserve whitespace
    const div = document.createElement('div');
    div.textContent = text;
    return `<pre class="raw-output">${div.innerHTML}</pre>`;
  }
  
  // Public API
  return {
    processResponse,
    formatRawText,
    initializeHighlighting,
    addCopyButtons
  };
})();