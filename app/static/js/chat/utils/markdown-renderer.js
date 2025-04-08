/**
 * Markdown rendering utilities for the chat interface
 * Handles formatting, syntax highlighting, and code block management
 */

/**
 * MetisMarkdown - Utility for processing and rendering markdown content
 */
const MetisMarkdown = {
  /**
   * Process a response string with markdown formatting
   * @param {string} text - The text to process
   * @returns {string} Processed HTML
   */
  processResponse(text) {
    if (!text) return '';
    
    // Process code blocks first (to avoid interference with other formatting)
    text = this.processCodeBlocks(text);
    
    // Process other markdown elements
    text = this.processLists(text);
    text = this.processTables(text);
    text = this.processInlineFormatting(text);
    
    // Process line breaks and paragraphs
    text = this.processLineBreaks(text);
    
    return text;
  },
  
  /**
   * Process code blocks with syntax highlighting
   * @param {string} text - The text to process
   * @returns {string} Processed HTML
   */
  processCodeBlocks(text) {
    // Replace ```language\ncode\n``` blocks with highlighted code
    return text.replace(/```(\w*)\n([\s\S]*?)\n```/g, (match, language, code) => {
      language = language.trim() || 'plaintext';
      
      return `<pre class="code-block"><code class="language-${language}">${this.escapeHtml(code)}</code></pre>`;
    });
  },
  
  /**
   * Process unordered and ordered lists
   * @param {string} text - The text to process
   * @returns {string} Processed HTML
   */
  processLists(text) {
    // Process unordered lists
    text = text.replace(/(?:^|\n)((?:[ \t]*[-*+][ \t]+.+\n?)+)/g, (match, list) => {
      const items = list.split(/\n[ \t]*[-*+][ \t]+/).filter(Boolean);
      return `<ul>${items.map(item => `<li>${item.trim()}</li>`).join('')}</ul>`;
    });
    
    // Process ordered lists
    text = text.replace(/(?:^|\n)((?:[ \t]*\d+\.[ \t]+.+\n?)+)/g, (match, list) => {
      const items = list.split(/\n[ \t]*\d+\.[ \t]+/).filter(Boolean);
      return `<ol>${items.map(item => `<li>${item.trim()}</li>`).join('')}</ol>`;
    });
    
    return text;
  },
  
  /**
   * Process markdown tables
   * @param {string} text - The text to process
   * @returns {string} Processed HTML
   */
  processTables(text) {
    // Find table blocks
    return text.replace(/(?:^|\n)([|].*[|]\n[|][-:| ]+[|](?:\n[|].*[|])*)/g, (match, table) => {
      const rows = table.trim().split('\n');
      
      // Extract header row
      const headerRow = rows[0];
      const headerCells = headerRow.split('|').slice(1, -1).map(cell => cell.trim());
      
      // Skip separator row
      
      // Extract data rows
      const dataRows = rows.slice(2);
      const dataRowsHtml = dataRows.map(row => {
        const cells = row.split('|').slice(1, -1).map(cell => cell.trim());
        return `<tr>${cells.map(cell => `<td>${cell}</td>`).join('')}</tr>`;
      }).join('');
      
      // Build table HTML
      return `
        <table class="markdown-table">
          <thead>
            <tr>${headerCells.map(cell => `<th>${cell}</th>`).join('')}</tr>
          </thead>
          <tbody>
            ${dataRowsHtml}
          </tbody>
        </table>
      `;
    });
  },
  
  /**
   * Process inline formatting (bold, italic, links)
   * @param {string} text - The text to process
   * @returns {string} Processed HTML
   */
  processInlineFormatting(text) {
    // Bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Links
    text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    return text;
  },
  
  /**
   * Process line breaks and paragraphs
   * @param {string} text - The text to process
   * @returns {string} Processed HTML
   */
  processLineBreaks(text) {
    // Split by double newlines for paragraphs
    const paragraphs = text.split(/\n\n+/);
    
    // Process each paragraph
    return paragraphs.map(p => {
      // Skip if it's already an HTML element
      if (p.trim().startsWith('<') && p.trim().endsWith('>')) {
        return p;
      }
      
      // Replace single newlines with <br>
      p = p.replace(/\n/g, '<br>');
      
      // Wrap in paragraph tags if not empty
      return p.trim() ? `<p>${p}</p>` : '';
    }).join('');
  },
  
  /**
   * Format raw text for display
   * @param {string} text - The raw text to format
   * @returns {string} Formatted HTML
   */
  formatRawText(text) {
    return `<pre class="raw-output">${this.escapeHtml(text)}</pre>`;
  },
  
  /**
   * Initialize syntax highlighting for code blocks
   * @param {HTMLElement} container - The container with code blocks
   */
  initializeHighlighting(container) {
    // Find all code blocks
    const codeBlocks = container.querySelectorAll('pre code');
    
    // Apply highlighting if available
    if (window.hljs) {
      codeBlocks.forEach(block => {
        window.hljs.highlightElement(block);
      });
    }
  },
  
  /**
   * Add copy buttons to code blocks
   * @param {HTMLElement} container - The container with code blocks
   */
  addCopyButtons(container) {
    // Find all code blocks
    const codeBlocks = container.querySelectorAll('pre.code-block');
    
    codeBlocks.forEach(block => {
      // Check if button already exists
      if (block.querySelector('.code-copy-button')) return;
      
      // Create copy button
      const copyButton = document.createElement('button');
      copyButton.className = 'code-copy-button';
      copyButton.innerHTML = '<i class="fas fa-copy"></i>';
      copyButton.title = 'Copy code';
      
      // Add click handler
      copyButton.addEventListener('click', () => {
        const code = block.querySelector('code');
        if (!code) return;
        
        // Copy text to clipboard
        navigator.clipboard.writeText(code.textContent)
          .then(() => {
            // Show success feedback
            copyButton.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
              copyButton.innerHTML = '<i class="fas fa-copy"></i>';
            }, 2000);
          })
          .catch(err => {
            console.error('Failed to copy code: ', err);
          });
      });
      
      // Add button to block
      block.appendChild(copyButton);
    });
  },
  
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
};

// Export the utilities
export { MetisMarkdown };