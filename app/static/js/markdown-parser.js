/**
 * Markdown parser utility for Metis RAG
 */

// Configure marked.js options
console.log("CONFIGURING MARKED.JS OPTIONS");

// Log the current breaks setting and its impact
console.log("MARKED.JS BREAKS OPTION EXPLANATION:");
console.log("- When breaks=true: Single newlines (\\n) are converted to <br> tags");
console.log("- When breaks=false: Single newlines are ignored, double newlines (\\n\\n) create new paragraphs");
console.log("- If Ollama uses single newlines for line breaks, breaks=true is better");
console.log("- If Ollama uses double newlines for paragraphs, breaks=false might be better");

// Current setting: breaks=true
const useBreaks = false;
console.log("CURRENT SETTING: breaks=" + useBreaks);

marked.setOptions({
  highlight: function(code, lang) {
    // Use the provided language tag or fallback to plaintext
    // The backend handles language tag fixing, so we just use what's provided
    const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
    console.log("HIGHLIGHTING CODE WITH LANGUAGE:", language);
    
    try {
      // Let highlight.js handle escaping/highlighting
      return hljs.highlight(code, { language, ignoreIllegals: true }).value;
    } catch (e) {
      console.error('Error highlighting code:', e);
      // Fallback: return escaped code without highlighting
      const temp = document.createElement('div');
      temp.textContent = code;
      return temp.innerHTML; // Basic escaping
    }
  },
  breaks: false, // Set to false to only create paragraphs on double newlines (\n\n)
  gfm: true,    // Enable GitHub Flavored Markdown (includes fenced code blocks)
  headerIds: false,
  mangle: false,
  // Add a custom renderer to ensure proper code block formatting
  renderer: {
    ...new marked.Renderer(),
    code: function(code, language) {
      // Ensure proper code block formatting
      const validLanguage = language && hljs.getLanguage(language) ? language : 'plaintext';
      console.log("RENDERING CODE BLOCK WITH LANGUAGE:", validLanguage);
      try {
        const highlighted = hljs.highlight(code, { language: validLanguage, ignoreIllegals: true }).value;
        return `<pre><code class="hljs language-${validLanguage}">${highlighted}</code></pre>`;
      } catch (e) {
        console.error('Error in custom code renderer:', e);
        return `<pre><code class="hljs language-${validLanguage}">${code}</code></pre>`;
      }
    },
    paragraph: function(text) {
      console.log("RENDERING PARAGRAPH:", text.substring(0, 50) + "...");
      return `<p>${text}</p>`;
    }
  }
});

/**
 * Sanitize HTML to prevent XSS attacks
 * This is a more comprehensive sanitization than the basic approach
 * @param {string} html - The HTML to sanitize
 * @return {string} - Sanitized HTML
 */
function sanitizeHTML(html) {
  // Basic sanitization: remove script tags and potentially harmful attributes
  const scriptTagRegex = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
  const eventHandlerRegex = / on\w+="[^"]*"/gi;
  const inlineJSRegex = /javascript:/gi;
  
  let sanitized = html.replace(scriptTagRegex, '')
                      .replace(eventHandlerRegex, '')
                      .replace(inlineJSRegex, 'void:');
  
  return sanitized;
}

/**
 * Parse markdown text and convert to HTML with syntax highlighting
 * @param {string} text - The markdown text to parse
 * @return {string} - HTML with syntax highlighting
 */
function parseMarkdown(text) {
  console.log("PARSE MARKDOWN CALLED WITH TEXT LENGTH:", text ? text.length : 0);
  console.log("TEXT PREVIEW:", text ? text.substring(0, 200) + "..." : "null");
  
  // Log paragraph structure
  const paragraphCount = (text.match(/\n\n/g) || []).length + 1;
  const singleNewlineCount = (text.match(/\n/g) || []).length;
  const doubleNewlineCount = (text.match(/\n\n/g) || []).length;
  console.log("PARAGRAPH STRUCTURE:", {
    paragraphs: paragraphCount,
    singleNewlines: singleNewlineCount,
    doubleNewlines: doubleNewlineCount
  });
  
  // Pre-process code blocks to ensure proper formatting
  console.log("CALLING PREPROCESS CODE BLOCKS");
  text = preprocessCodeBlocks(text);
  
  // Check for code blocks after preprocessing
  const codeBlockPattern = /```(\w+)[\s\S]*?```/g;
  const codeBlocks = text.match(codeBlockPattern);
  console.log("CODE BLOCKS AFTER PREPROCESSING:", codeBlocks);
  
  // Log paragraph structure after preprocessing
  const paragraphCountAfter = (text.match(/\n\n/g) || []).length + 1;
  console.log("PARAGRAPH COUNT AFTER PREPROCESSING:", paragraphCountAfter);
  if (paragraphCount !== paragraphCountAfter) {
    console.warn("PARAGRAPH COUNT CHANGED DURING PREPROCESSING:",
      paragraphCount, "->", paragraphCountAfter);
  }
  
  // Let marked.js handle everything, including code blocks via the 'highlight' option
  console.log("CALLING MARKED.PARSE");
  try {
    const rawHtml = marked.parse(text);
    console.log("MARKED.PARSE RETURNED HTML LENGTH:", rawHtml ? rawHtml.length : 0);
    
    // Apply sanitization to the final HTML output
    console.log("SANITIZING HTML");
    const sanitizedHtml = sanitizeHTML(rawHtml);
    console.log("SANITIZED HTML LENGTH:", sanitizedHtml ? sanitizedHtml.length : 0);
    
    return sanitizedHtml;
  } catch (error) {
    console.error("ERROR IN MARKED.PARSE:", error);
    // Return a fallback HTML with the error message
    return `<div class="error">Error parsing markdown: ${error.message}</div>
            <pre>${text}</pre>`;
  }
}

/**
 * Pre-process code blocks to ensure proper formatting
 * @param {string} text - The text containing code blocks
 * @return {string} - Text with properly formatted code blocks
 */
function preprocessCodeBlocks(text) {
  if (!text) return text;
  
  console.log("BEFORE PREPROCESSING:", JSON.stringify(text));
  
  // Fix duplicate language tags at the beginning (e.g., ```python python)
  let step1 = text.replace(/```(\w+)\s+\1/g, '```$1');
  console.log("AFTER FIXING DUPLICATE TAGS:", JSON.stringify(step1));
  
  // Fix code blocks with incorrect closing tags
  // This regex matches code blocks with language tags and ensures proper closing
  let step2 = step1.replace(/```(\w+)([\s\S]*?)```(\w+)?/g, function(match, lang, code, closingLang) {
    console.log("FOUND CODE BLOCK:", {
      lang: lang,
      codePreview: code.substring(0, 50) + "...",
      closingLang: closingLang
    });
    
    // If there's a closing language tag, remove it
    if (closingLang) {
      console.log("REMOVING CLOSING LANGUAGE TAG:", closingLang);
      return '```' + lang + code + '```';
    }
    return match;
  });
  
  console.log("AFTER FIXING CLOSING TAGS:", JSON.stringify(step2));
  
  // Additional fix for cases where language tag is repeated after newline
  // Example: ```python\npython\ndef...
  let step3 = step2.replace(/```(\w+)\n\1\b/g, function(match, lang) {
    console.log("FIXING NEWLINE LANGUAGE REPETITION:", lang);
    return '```' + lang + '\n';
  });
  
  // Fix for the specific pattern in the user's example
  // This handles cases where there's a newline between the language tag and the code
  let step4 = step3.replace(/```(\w+)(\s*\n\s*)/g, function(match, lang, spacing) {
    console.log("FIXING NEWLINE AFTER LANGUAGE TAG:", lang);
    return '```' + lang + '\n';
  });
  
  console.log("FINAL PREPROCESSED TEXT:", JSON.stringify(step4));
  
  return step4;
}

/**
 * Process a response for display in the chat interface
 * @param {string} response - The response text to process
 * @return {string} - Processed HTML ready for display
 */
function processResponse(response) {
  console.log("PROCESSING RESPONSE:", {
    responseLength: response ? response.length : 0,
    responsePreview: response ? response.substring(0, 100) + "..." : "null"
  });
  
  // Log paragraph structure in the response
  const paragraphCount = (response.match(/\n\n/g) || []).length + 1;
  const singleNewlineCount = (response.match(/\n/g) || []).length;
  const doubleNewlineCount = (response.match(/\n\n/g) || []).length;
  console.log("RESPONSE PARAGRAPH STRUCTURE:", {
    paragraphs: paragraphCount,
    singleNewlines: singleNewlineCount,
    doubleNewlines: doubleNewlineCount
  });
  
  // Check if the response starts with a UUID pattern (conversation ID)
  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s/i;
  if (response.match(uuidPattern)) {
    // Remove the UUID from the beginning of the response
    console.log("UUID PATTERN FOUND, REMOVING");
    response = response.replace(uuidPattern, '');
  }
  
  // Check for code blocks before preprocessing
  const codeBlockPattern = /```(\w+)[\s\S]*?```/g;
  const codeBlocks = response.match(codeBlockPattern);
  console.log("CODE BLOCKS FOUND BEFORE PREPROCESSING:", codeBlocks);
  
  // Log the first few paragraphs to see their structure
  const paragraphs = response.split(/\n\n+/);
  console.log("FIRST FEW PARAGRAPHS:");
  paragraphs.slice(0, 3).forEach((p, i) => {
    console.log(`PARAGRAPH ${i+1}:`, p.substring(0, 100) + (p.length > 100 ? "..." : ""));
  });
  
  // Parse markdown and return the HTML
  console.log("CALLING PARSE MARKDOWN");
  const html = parseMarkdown(response);
  console.log("PARSE MARKDOWN RETURNED HTML LENGTH:", html ? html.length : 0);
  
  // Log HTML structure
  const paragraphTags = (html.match(/<p>/g) || []).length;
  const brTags = (html.match(/<br>/g) || []).length;
  console.log("HTML STRUCTURE:", {
    paragraphTags: paragraphTags,
    brTags: brTags
  });
  
  // Check if paragraph count matches
  if (paragraphCount !== paragraphTags) {
    console.warn("PARAGRAPH COUNT MISMATCH:", {
      originalParagraphs: paragraphCount,
      htmlParagraphs: paragraphTags
    });
  }
  
  // Use requestAnimationFrame to ensure DOM is ready for button addition/highlighting
  requestAnimationFrame(() => {
    console.log("ADDING COPY BUTTONS AND HIGHLIGHTING");
    addCopyButtons();
    initializeCodeHighlighting();
  });
  
  return html;
}

/**
 * Add copy buttons to code blocks
 */
function addCopyButtons() {
  document.querySelectorAll('pre code').forEach((codeBlock) => {
    // Check if the container already exists
    let container = codeBlock.closest('.code-block-container');
    if (!container) {
      // Create container if it doesn't exist
      container = document.createElement('div');
      container.className = 'code-block-container';
      const preElement = codeBlock.parentNode; // Should be <pre>
      preElement.parentNode.replaceChild(container, preElement);
      container.appendChild(preElement);
    }
    
    // Check if button already exists
    if (container.querySelector('.copy-code-button')) {
      return;
    }
    
    // Create copy button
    const copyButton = document.createElement('button');
    copyButton.className = 'copy-code-button';
    copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy';
    
    // Add click event to copy the code
    copyButton.addEventListener('click', () => {
      const code = codeBlock.textContent;
      navigator.clipboard.writeText(code).then(() => {
        // Change button text to indicate success
        copyButton.innerHTML = '<i class="fas fa-check"></i> Copied!';
        setTimeout(() => {
          copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy';
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy code:', err);
        copyButton.textContent = 'Failed';
        setTimeout(() => {
          copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy';
        }, 2000);
      });
    });
    
    container.appendChild(copyButton);
  });
}

/**
 * Initialize syntax highlighting for all code blocks
 */
function initializeCodeHighlighting() {
  document.querySelectorAll('pre code').forEach((block) => {
    // Check if already highlighted
    if (!block.classList.contains('hljs')) {
      hljs.highlightElement(block);
    }
  });
}

// Export the functions for use in other scripts
window.MetisMarkdown = {
  processResponse: processResponse,
  initializeHighlighting: initializeCodeHighlighting,
  addCopyButtons: addCopyButtons
};

// Add Font Awesome if not already included
if (!document.querySelector('link[href*="font-awesome"]')) {
  const faLink = document.createElement('link');
  faLink.rel = 'stylesheet';
  faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
  document.head.appendChild(faLink);
}