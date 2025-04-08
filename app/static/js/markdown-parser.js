/**
 * Markdown parser utility for Metis RAG
 */

// Check if marked is defined before configuring it
console.log("CONFIGURING MARKED.JS OPTIONS");

// Log the current breaks setting and its impact
console.log("MARKED.JS BREAKS OPTION EXPLANATION:");
console.log("- When breaks=true: Single newlines (\\n) are converted to <br> tags");
console.log("- When breaks=false: Single newlines are ignored, double newlines (\\n\\n) create new paragraphs");
console.log("- If Ollama uses single newlines for line breaks, breaks=true is better");
console.log("- If Ollama uses double newlines for paragraphs, breaks=false might be better");

// Current setting: breaks=false (recommended for proper paragraph structure)
// When breaks=false, only double newlines (\n\n) create new paragraphs
// When breaks=true, single newlines (\n) are converted to <br> tags
const useBreaks = false;
console.log("CURRENT SETTING: breaks=" + useBreaks);
console.log("This means only double newlines (\\n\\n) will create new paragraphs");
console.log("Single newlines (\\n) will be ignored unless they're in code blocks");

// Check if marked is defined
if (typeof marked !== 'undefined' && typeof hljs !== 'undefined') {
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
  breaks: true, // Set to true to convert single newlines (\n) to <br> tags
  gfm: true,     // Enable GitHub Flavored Markdown (includes fenced code blocks)
  headerIds: false,
  sanitize: false, // Disable sanitization to allow HTML tags to be rendered
  mangle: false,
  // Add a custom renderer to ensure proper code block formatting
  renderer: new marked.Renderer(),
});

// Add custom renderer methods after initialization
try {
  if (typeof marked !== 'undefined' && typeof hljs !== 'undefined') {
    // Try to get the renderer - different versions of marked.js have different APIs
    let renderer;
    try {
      // Modern API
      renderer = marked.getRenderer();
    } catch (e) {
      // Fallback to older API or create a new renderer
      console.warn("Could not get renderer with getRenderer(), using fallback:", e);
      renderer = new marked.Renderer();
      // Apply the renderer to marked
      marked.setOptions({ renderer: renderer });
    }
    
    // Custom code renderer
    renderer.code = function(code, language) {
      // Ensure proper code block formatting
      const validLanguage = language && hljs.getLanguage(language) ? language : 'plaintext';
      console.log("RENDERING CODE BLOCK WITH LANGUAGE:", validLanguage);
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
      console.log("RENDERING PARAGRAPH:", text.substring(0, 50) + "...");
      console.log("PARAGRAPH LENGTH:", text.length);
      return `<p class="structured-paragraph">${text}</p>`;
    };
    
    // Custom heading renderer
    renderer.heading = function(text, level) {
      // Only apply our custom styling to h2 (##) headings
      if (level === 2) {
        return `<h${level} class="structured-heading">${text}</h${level}>`;
      }
      return `<h${level}>${text}</h${level}>`;
    };
    
    // Custom list item renderer
    renderer.listitem = function(text) {
      return `<li class="structured-list-item">${text}</li>`;
    };
    
    // Custom blockquote renderer
    renderer.blockquote = function(text) {
      return `<blockquote class="structured-quote">${text}</blockquote>`;
    };
  }
} catch (e) {
  console.error("Error setting up custom renderers:", e);
}
} else {
  console.error("ERROR: marked or hljs is not defined. Make sure to load these libraries before markdown-parser.js");
  
  // Define dummy functions to prevent errors
  window.marked = {
    parse: function(text) {
      return `<pre>${text}</pre>`;
    },
    setOptions: function() {},
    getRenderer: function() { return {}; },
    Renderer: function() { return {}; }
  };
  
  window.hljs = {
    highlight: function(code, options) {
      return { value: code };
    },
    getLanguage: function() { return null; }
  };
}

/**
 * Sanitize HTML to prevent XSS attacks while preserving formatting
 * This is a more comprehensive sanitization than the basic approach
 * @param {string} html - The HTML to sanitize
 * @return {string} - Sanitized HTML
 */
function sanitizeHTML(html) {
  // Only remove potentially harmful elements while preserving formatting
  const scriptTagRegex = /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi;
  const eventHandlerRegex = / on\w+="[^"]*"/gi;
  const inlineJSRegex = /javascript:/gi;
  
  // Preserve HTML tags that are safe for formatting
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
    doubleNewlines: doubleNewlineCount,
    singleToDoubleRatio: singleNewlineCount > 0 ? (singleNewlineCount / (doubleNewlineCount || 1)).toFixed(2) : 0
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
    // Log the first few paragraphs with double newlines to confirm proper structure
    const paragraphsWithDoubleNewlines = text.split(/\n\n+/);
    console.log("PARAGRAPHS WITH DOUBLE NEWLINES:", paragraphsWithDoubleNewlines.length);
    paragraphsWithDoubleNewlines.slice(0, 3).forEach((p, i) => {
      console.log(`PARAGRAPH ${i+1} WITH DOUBLE NEWLINE:`, p.substring(0, 50) + (p.length > 50 ? "..." : ""));
    });
    
    // Check if marked is defined and use the correct API
    let rawHtml;
    if (typeof marked !== 'undefined') {
      try {
        // Check if the error is the specific "t.text is not a function" issue
        // This is a known issue with some versions of marked.js
        const hasTextFunctionIssue = (function() {
          try {
            // Try a minimal test to see if we hit the error
            const testText = "Test paragraph\n\nAnother paragraph";
            if (typeof marked.parse === 'function') {
              marked.parse(testText);
            } else if (typeof marked === 'function') {
              marked(testText);
            }
            return false; // No error occurred
          } catch (e) {
            return e.message.includes("t.text is not a function");
          }
        })();

        if (hasTextFunctionIssue) {
          console.warn("Detected 't.text is not a function' issue, using custom parser");
          // Use our own simple markdown parser to avoid the issue
          rawHtml = customMarkdownParser(text);
        } else {
          // Try using the modern API first
          if (typeof marked.parse === 'function') {
            rawHtml = marked.parse(text);
          } else if (typeof marked === 'function') {
            // Some versions expose marked as a function directly
            rawHtml = marked(text);
          } else if (typeof marked.Parser === 'function' && typeof marked.Lexer === 'function') {
            // Fallback to older API if needed
            const tokens = marked.Lexer.lex(text);
            rawHtml = marked.Parser.parse(tokens);
          } else {
            // Last resort fallback
            rawHtml = customMarkdownParser(text);
            console.warn("Could not parse markdown with any available method, using custom parser");
          }
        }
      } catch (parseError) {
        console.warn("Error parsing markdown, using custom parser:", parseError);
        rawHtml = customMarkdownParser(text);
      }
    } else {
      rawHtml = `<pre>${text}</pre>`;
    }

    // Our custom markdown parser function as a fallback
    function customMarkdownParser(mdText) {
      if (!mdText) return '<p></p>';
      
      // Process code blocks first to avoid interference with other formatting
      let processedText = mdText.replace(/```(\w*)([\s\S]*?)```/g, function(match, lang, code) {
        return `<div class="structured-code-block">
                  <div class="code-block-header">${lang || 'code'}</div>
                  <pre><code class="language-${lang || 'plaintext'}">${code.trim()}</code></pre>
                </div>`;
      });
      
      // Process inline code
      processedText = processedText.replace(/`([^`]+)`/g, '<code>$1</code>');
      
      // Process headers
      processedText = processedText.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
      processedText = processedText.replace(/^## (.*?)$/gm, '<h2 class="structured-heading">$1</h2>');
      processedText = processedText.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
      
      // Process lists
      processedText = processedText.replace(/^\s*[\*\-]\s+(.*?)$/gm, '<li class="structured-list-item">$1</li>');
      processedText = processedText.replace(/^\s*(\d+)\.\s+(.*?)$/gm, '<li class="numbered-list-item">$1. $2</li>');
      
      // Process paragraphs (must be done after lists)
      const paragraphs = processedText.split(/\n\n+/);
      processedText = paragraphs.map(p => {
        // Skip if already wrapped in HTML tag
        if (p.trim().startsWith('<') && !p.trim().startsWith('<li')) {
          return p;
        }
        // Convert single newlines to <br> tags
        p = p.replace(/\n/g, '<br>');
        // Wrap in paragraph tag if not a list item
        if (p.includes('<li')) {
          return `<ul>${p}</ul>`;
        }
        return `<p class="structured-paragraph">${p}</p>`;
      }).join('\n\n');
      
      // Process bold and italic
      processedText = processedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      processedText = processedText.replace(/\*(.*?)\*/g, '<em>$1</em>');
      
      // Process links
      processedText = processedText.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');
      
      return processedText;
    }
    console.log("MARKED.PARSE RETURNED HTML LENGTH:", rawHtml ? rawHtml.length : 0);
    
    // Log the raw HTML to see what marked.js is generating
    console.log("RAW HTML PREVIEW:", rawHtml ? rawHtml.substring(0, 200) + "..." : "null");
    
    // Count paragraph tags in raw HTML
    const paragraphTagsInRawHtml = (rawHtml.match(/<p>/g) || []).length;
    console.log("PARAGRAPH TAGS IN RAW HTML:", paragraphTagsInRawHtml);
    
    // Compare with paragraphs with double newlines
    console.log("PARAGRAPH CONVERSION RATE:",
      paragraphsWithDoubleNewlines.length > 0 ?
      ((paragraphTagsInRawHtml / paragraphsWithDoubleNewlines.length) * 100).toFixed(2) + "%" : "0%");
    
    // Apply minimal sanitization to the final HTML output
    console.log("SANITIZING HTML (PRESERVING FORMATTING)");
    const sanitizedHtml = sanitizeHTML(rawHtml);
    console.log("SANITIZED HTML LENGTH:", sanitizedHtml ? sanitizedHtml.length : 0);
    
    // Log HTML structure after sanitization
    console.log("HTML STRUCTURE AFTER SANITIZATION:", {
      paragraphTags: (sanitizedHtml.match(/<p>/g) || []).length,
      brTags: (sanitizedHtml.match(/<br>/g) || []).length,
      listItems: (sanitizedHtml.match(/<li>/g) || []).length
    });
    
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
  
  // Check if the response is a JSON string (structured output)
  if (response.trim().startsWith('{') && response.trim().endsWith('}')) {
      try {
          console.log("DETECTED POTENTIAL JSON RESPONSE, ATTEMPTING TO PARSE");
          const jsonData = JSON.parse(response);
          
          // Check if this is our structured output format
          if (jsonData.text && (jsonData.code_blocks || jsonData.text_blocks || jsonData.tables || jsonData.images || jsonData.math_blocks)) {
              console.log("DETECTED STRUCTURED OUTPUT FORMAT");
              
              let processedText = jsonData.text;
              
              // Process text blocks if available
              if (jsonData.text_blocks && jsonData.text_blocks.length > 0) {
                  console.log(`PROCESSING ${jsonData.text_blocks.length} TEXT BLOCKS`);
                  
                  // Combine text blocks into a single text with proper paragraph structure
                  const textParts = jsonData.text_blocks.map(block => {
                      if (block.format_type === "paragraph") {
                          return block.content;
                      } else if (block.format_type === "heading") {
                          return `## ${block.content}`;
                      } else if (block.format_type === "list_item") {
                          return `- ${block.content}`;
                      } else if (block.format_type === "quote") {
                          return `> ${block.content}`;
                      } else {
                          return block.content;
                      }
                  });
                  
                  // Join with double newlines to preserve paragraph structure
                  processedText = textParts.join("\n\n");
              }
              
              // Process code blocks
              if (jsonData.code_blocks && jsonData.code_blocks.length > 0) {
                  console.log(`PROCESSING ${jsonData.code_blocks.length} CODE BLOCKS`);
                  
                  // Replace code block placeholders with properly formatted code blocks
                  jsonData.code_blocks.forEach((codeBlock, index) => {
                      const placeholder = `{CODE_BLOCK_${index}}`;
                      const formattedBlock = `\`\`\`${codeBlock.language}\n${codeBlock.code}\n\`\`\``;
                      processedText = processedText.replace(placeholder, formattedBlock);
                  });
              }
              
              // Process tables
              if (jsonData.tables && jsonData.tables.length > 0) {
                  console.log(`PROCESSING ${jsonData.tables.length} TABLES`);
                  
                  // Replace table placeholders with markdown tables
                  jsonData.tables.forEach((table, index) => {
                      const placeholder = `{TABLE_${index}}`;
                      let tableMarkdown = "";
                      
                      // Add caption if available
                      if (table.caption) {
                          tableMarkdown += `**${table.caption}**\n\n`;
                      }
                      
                      // Process rows
                      table.rows.forEach((row, rowIndex) => {
                          // Create row content
                          const rowCells = row.cells.map(cell => {
                              let content = cell.content.trim();
                              if (cell.align === "center") {
                                  content = ` ${content} `;
                              } else if (cell.align === "right") {
                                  content = ` ${content}`;
                              } else { // left alignment (default)
                                  content = `${content} `;
                              }
                              return content;
                          });
                          
                          tableMarkdown += `| ${rowCells.join(' | ')} |\n`;
                          
                          // Add header separator after first row if it's a header row
                          if (rowIndex === 0 && (row.is_header_row || row.cells.some(cell => cell.is_header))) {
                              const separators = row.cells.map(cell => {
                                  if (cell.align === "center") {
                                      return ":---:";
                                  } else if (cell.align === "right") {
                                      return "---:";
                                  } else { // left alignment (default)
                                      return "---";
                                  }
                              });
                              
                              tableMarkdown += `| ${separators.join(' | ')} |\n`;
                          }
                      });
                      
                      processedText = processedText.replace(placeholder, tableMarkdown);
                  });
              }
              
              // Process images
              if (jsonData.images && jsonData.images.length > 0) {
                  console.log(`PROCESSING ${jsonData.images.length} IMAGES`);
                  
                  // Replace image placeholders with markdown images
                  jsonData.images.forEach((image, index) => {
                      const placeholder = `{IMAGE_${index}}`;
                      let imageMarkdown = `![${image.alt_text}](${image.url})`;
                      
                      // Add caption if available
                      if (image.caption) {
                          imageMarkdown += `\n*${image.caption}*`;
                      }
                      
                      processedText = processedText.replace(placeholder, imageMarkdown);
                  });
              }
              
              // Process math blocks
              if (jsonData.math_blocks && jsonData.math_blocks.length > 0) {
                  console.log(`PROCESSING ${jsonData.math_blocks.length} MATH BLOCKS`);
                  
                  // Replace math block placeholders with LaTeX
                  jsonData.math_blocks.forEach((mathBlock, index) => {
                      const placeholder = `{MATH_${index}}`;
                      let mathMarkdown = "";
                      
                      if (mathBlock.display_mode) {
                          // Display mode (block)
                          mathMarkdown = `$$\n${mathBlock.latex}\n$$`;
                      } else {
                          // Inline mode
                          mathMarkdown = `$${mathBlock.latex}$`;
                      }
                      
                      processedText = processedText.replace(placeholder, mathMarkdown);
                  });
              }
              
              console.log("STRUCTURED OUTPUT PROCESSED SUCCESSFULLY");
              response = processedText;
          }
    } catch (e) {
      console.warn("FAILED TO PARSE JSON RESPONSE:", e);
      // Continue with normal processing
    }
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
  const preBlocks = (html.match(/<pre>/g) || []).length;
  
  // Extract and log the first few paragraph tags to see their content
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;
  const pElements = tempDiv.querySelectorAll('p');
  console.log("FIRST FEW PARAGRAPH ELEMENTS:");
  Array.from(pElements).slice(0, 3).forEach((p, i) => {
    console.log(`P ELEMENT ${i+1} (${p.textContent.length} chars):`, p.textContent.substring(0, 50) + (p.textContent.length > 50 ? "..." : ""));
    console.log(`P ELEMENT ${i+1} BR TAGS:`, (p.innerHTML.match(/<br>/g) || []).length);
  });
  
  console.log("HTML STRUCTURE:", {
    paragraphTags: paragraphTags,
    brTags: brTags,
    preBlocks: preBlocks,
    brToParaRatio: paragraphTags > 0 ? (brTags / paragraphTags).toFixed(2) : 0,
    averageCharsPerParagraph: pElements.length > 0 ?
      (Array.from(pElements).reduce((sum, p) => sum + p.textContent.length, 0) / pElements.length).toFixed(2) : 0
  });
  
  // Check if paragraph count matches
  if (paragraphCount !== paragraphTags) {
    console.warn("PARAGRAPH COUNT MISMATCH:", {
      originalParagraphs: paragraphCount,
      htmlParagraphs: paragraphTags,
      difference: paragraphCount - paragraphTags
    });
  }
  
  // Log the impact of breaks=true setting
  console.log("BREAKS=TRUE IMPACT:", {
    singleNewlines: singleNewlineCount,
    brTags: brTags,
    conversionRate: singleNewlineCount > 0 ? (brTags / singleNewlineCount).toFixed(2) : 0,
    effectivenessRating: singleNewlineCount > 0 && brTags > 0 ?
      ((brTags / singleNewlineCount) * 100).toFixed(2) + "%" : "0%"
  });
  
  // Log overall formatting assessment
  console.log("FORMATTING ASSESSMENT:", {
    paragraphPreservation: paragraphCount === paragraphTags ? "Good" : "Needs improvement",
    lineBreakPreservation: singleNewlineCount > 0 && brTags > 0 ?
      ((brTags / singleNewlineCount) * 100).toFixed(2) + "%" : "0%",
    overallQuality: paragraphCount === paragraphTags && brTags > 0 ? "Good" : "Needs improvement"
  });
  
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
// Define the MetisMarkdown object with fallbacks
window.MetisMarkdown = {
  processResponse: function(response) {
    try {
      return processResponse(response);
    } catch (e) {
      console.error("Error in processResponse:", e);
      return `<pre>${response}</pre>`;
    }
  },
  initializeHighlighting: function() {
    try {
      if (typeof initializeCodeHighlighting === 'function') {
        initializeCodeHighlighting();
      }
    } catch (e) {
      console.error("Error in initializeCodeHighlighting:", e);
    }
  },
  addCopyButtons: function() {
    try {
      if (typeof addCopyButtons === 'function') {
        addCopyButtons();
      }
    } catch (e) {
      console.error("Error in addCopyButtons:", e);
    }
  }
};

// Log that the MetisMarkdown object is ready
console.log("MetisMarkdown object initialized and ready for use");

// Add Font Awesome if not already included
if (!document.querySelector('link[href*="font-awesome"]')) {
  const faLink = document.createElement('link');
  faLink.rel = 'stylesheet';
  faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
  document.head.appendChild(faLink);
}