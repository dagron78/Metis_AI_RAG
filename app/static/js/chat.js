// File: app/static/js/chat.js

console.log('CHAT.JS LOADED');

// Debug DevOps panel directly
window.addEventListener('load', function() {
    console.log('WINDOW LOADED');
    
    const devopsPanel = document.querySelector('.devops-panel');
    console.log('DevOps Panel (window.load):', devopsPanel);
    
    // Debug checkboxes
    const ragToggle = document.getElementById('rag-toggle');
    const streamToggle = document.getElementById('stream-toggle');
    const rawOutputToggle = document.getElementById('raw-output-toggle');
    const rawLlmOutputToggle = document.getElementById('raw-llm-output-toggle');
    
    console.log('Checkboxes found:', {
        ragToggle,
        streamToggle,
        rawOutputToggle,
        rawLlmOutputToggle
    });
    
    if (devopsPanel) {
        console.log('DevOps Panel style:', window.getComputedStyle(devopsPanel));
        // Force visibility
        devopsPanel.style.display = 'block';
        devopsPanel.style.visibility = 'visible';
        devopsPanel.style.opacity = '1';
        console.log('DevOps Panel style forced visible');
    }
    
    if (devopsPanel) {
        console.log('DevOps Panel style:', window.getComputedStyle(devopsPanel));
        // Force visibility
        devopsPanel.style.display = 'block';
        devopsPanel.style.visibility = 'visible';
        devopsPanel.style.opacity = '1';
        devopsPanel.style.zIndex = '9999';
        
        // Force checkboxes to be visible
        if (ragToggle) ragToggle.style.display = 'inline-block';
        if (streamToggle) streamToggle.style.display = 'inline-block';
        if (rawOutputToggle) rawOutputToggle.style.display = 'inline-block';
        if (rawLlmOutputToggle) rawLlmOutputToggle.style.display = 'inline-block';
        console.log('DevOps Panel style forced visible');
    } else {
        console.error('DevOps Panel not found in DOM!');
    }
});

// Ensure MetisMarkdown is loaded (assuming markdown-parser.js is included before this)
if (typeof window.MetisMarkdown === 'undefined') {
    console.error("Error: markdown-parser.js must be loaded before chat.js");
    // Define dummy functions to prevent errors later if the script failed to load
    window.MetisMarkdown = {
        processResponse: (text) => {
            const el = document.createElement('div');
            el.textContent = text; // Basic fallback
            return el.innerHTML;
        },
        // Add dummy initializeHighlighting and addCopyButtons if needed by addMessage fallback
        initializeHighlighting: () => {},
        addCopyButtons: () => {}
    };
}

document.addEventListener('DOMContentLoaded', function() {
    // --- Elements ---
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-chat');
    const saveButton = document.getElementById('save-chat'); // Assuming this exists
    const modelSelect = document.getElementById('model');
    const ragToggle = document.getElementById('rag-toggle');
    const streamToggle = document.getElementById('stream-toggle');
    const rawOutputToggle = document.getElementById('raw-output-toggle');
    const rawLlmOutputToggle = document.getElementById('raw-llm-output-toggle');
    const loadingIndicator = document.getElementById('loading');
    const maxResults = document.getElementById('max-results');
    const temperature = document.getElementById('temperature');
    const metadataFilters = document.getElementById('metadata-filters');
    
    // Debug DevOps panel
    const devopsPanel = document.querySelector('.devops-panel');
    console.log('DevOps Panel:', devopsPanel);
    if (devopsPanel) {
        console.log('DevOps Panel style:', window.getComputedStyle(devopsPanel));
        // Force visibility
        devopsPanel.style.display = 'block';
        devopsPanel.style.visibility = 'visible';
        devopsPanel.style.opacity = '1';
        console.log('DevOps Panel style forced visible');
    }

    if (!chatContainer || !userInput || !sendButton || !modelSelect || !ragToggle || !streamToggle || !rawOutputToggle || !rawLlmOutputToggle || !loadingIndicator || !maxResults || !temperature || !metadataFilters) {
        console.error("Chat UI elements not found. Chat functionality may be limited.");
        // return; // Optionally return if core elements are missing
    }

    // --- State ---
    let currentConversationId = null;

    // --- Initialization ---
    loadInitialState();
    setupEventListeners();

    // --- Functions ---

    /**
     * Loads initial state like conversation ID and models.
     */
    function loadInitialState() {
        const storedConversationId = localStorage.getItem('metis_conversation_id');
        if (storedConversationId) {
            currentConversationId = storedConversationId;
            console.log('Retrieved stored conversation ID:', currentConversationId);
        }
        loadModels();
    }

    /**
     * Updates and stores the current conversation ID.
     * @param {string | null} id The new conversation ID.
     */
    function updateConversationId(id) {
        if (!id) return;
        if (id !== currentConversationId) {
            currentConversationId = id;
            localStorage.setItem('metis_conversation_id', id);
            console.log('Conversation ID updated and stored:', id);
        }
    }

    /**
     * Fetches available models and populates the dropdown.
     */
    function loadModels() {
        if (!modelSelect) return;
        console.log('Loading models...');
        authenticatedFetch('/api/system/models')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(models => {
                console.log('Models fetched:', models);
                modelSelect.innerHTML = ''; // Clear existing options

                if (Array.isArray(models) && models.length > 0) {
                    models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.name;
                        option.textContent = model.name;
                        modelSelect.appendChild(option);
                    });
                    // Optionally set a default selection if needed
                    // modelSelect.value = models[0]?.name || 'gemma3:4b';
                } else {
                    console.warn('No models received from API or empty list.');
                    const option = document.createElement('option');
                    option.value = 'gemma3:4b'; // Fallback default
                    option.textContent = 'gemma3:4b (default)';
                    modelSelect.appendChild(option);
                }
            })
            .catch(error => {
                console.error('Error loading models:', error);
                modelSelect.innerHTML = '<option value="">Error loading</option>';
            });
    }

    /**
     * Sets up event listeners for UI elements.
     */
    function setupEventListeners() {
        if (sendButton) sendButton.addEventListener('click', sendMessage);
        if (userInput) userInput.addEventListener('keydown', handleInputKeydown);
        if (clearButton) clearButton.addEventListener('click', handleClearChat);
        // Add event listener for save button if it exists
        if (saveButton) saveButton.addEventListener('click', handleSaveChat);
        if (ragToggle) ragToggle.addEventListener('change', handleRagToggle);
    }

    /**
     * Handles keydown events in the user input textarea.
     * @param {KeyboardEvent} e The keydown event.
     */
    function handleInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    /**
     * Handles the clear chat button click.
     */
    function handleClearChat() {
        if (confirm('Are you sure you want to clear the chat history? This will start a new conversation.')) {
            clearConversationOnServer(); // Call server to clear history if needed
            currentConversationId = null; // Reset local ID
            localStorage.removeItem('metis_conversation_id');
            chatContainer.innerHTML = ''; // Clear UI
            addWelcomeMessage();
            console.log('Chat cleared locally and conversation ID reset.');
        }
    }

     /**
     * Handles the save chat button click (placeholder).
     */
    function handleSaveChat() {
        // Implement save functionality here (e.g., save to local file, send to server)
        showNotification('Save chat functionality not yet implemented.', 'info');
        console.log('Save chat clicked. Conversation ID:', currentConversationId);
    }


    /**
     * Handles the RAG toggle change event.
     */
    function handleRagToggle() {
        const ragParams = document.querySelectorAll('.rag-param');
        ragParams.forEach(param => {
            param.style.display = this.checked ? 'block' : 'none';
        });
    }

    /**
     * Adds the initial welcome message to the chat.
     */
    function addWelcomeMessage() {
         addMessage(
            'assistant',
            "Hello! I'm your Metis RAG assistant. Ask me anything about your uploaded documents or chat with me directly."
         );
    }

    /**
     * Sends the user's message to the backend API.
     */
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        if (!isAuthenticated()) {
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
            return;
        }

        addMessage('user', message); // Add raw user message
        userInput.value = '';
        if (loadingIndicator) loadingIndicator.style.display = 'flex'; // Use flex
// Get the state of the raw output toggles
const showRawOutput = rawOutputToggle?.checked ?? false;
const showRawLlmOutput = rawLlmOutputToggle?.checked ?? false;

        
        const query = buildQuery(message);
        console.log('Sending query:', query);
        console.log('Raw output mode:', showRawOutput ? 'ENABLED' : 'DISABLED');

        // Create placeholder for assistant response
        const assistantMessageDiv = addMessage('assistant', '', [], true); // Add placeholder
        const contentDiv = assistantMessageDiv.querySelector('.message-content'); // Get the content div

        const controller = new AbortController();
        // Increased timeout to 120 seconds (2 minutes)
        const timeoutId = setTimeout(() => {
            console.warn('Request Aborted due to timeout (120s)');
            controller.abort();
            handleErrorMessage({ name: 'AbortError', message: 'Request timed out after 120 seconds.' }, contentDiv, message, ragToggle, streamToggle, assistantMessageDiv);
        }, 120000);


        authenticatedFetch('/api/chat/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(query),
            signal: controller.signal
        })
        .then(response => {
            clearTimeout(timeoutId); // Clear timeout on successful response header
            if (!response.ok) {
                // Try to read error message from response body
                return response.json().then(errData => {
                    throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
                }).catch(() => {
                    // Fallback if response body is not JSON or empty
                    throw new Error(`HTTP error! status: ${response.status}`);
                });
            }

            if (query.stream && response.body) {
                 processStream(response.body, contentDiv, assistantMessageDiv);
            } else {
                return response.json().then(data => {
                    if (loadingIndicator) loadingIndicator.style.display = 'none';
                    updateConversationId(data.conversation_id);

                    // Process the complete message for Markdown rendering
                    let processedResponse = data.message || '';
                    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s/i;
                    if (processedResponse.match(uuidPattern)) {
                        processedResponse = processedResponse.replace(uuidPattern, '');
                    }
                    
                    // Log text structure before markdown processing
                    console.log("TEXT STRUCTURE BEFORE MARKDOWN:", {
                        paragraphs: (processedResponse.match(/\n\n+/g) || []).length + 1,
                        singleNewlines: (processedResponse.match(/\n/g) || []).length,
                        doubleNewlines: (processedResponse.match(/\n\n+/g) || []).length
                    });
                    if (showRawLlmOutput) {
                        console.log("Displaying RAW LLM output (non-streaming).");
                        // Display raw text, preserving whitespace and line breaks, safely
                        const pre = document.createElement('pre');
                        pre.style.whiteSpace = 'pre-wrap'; // Allow wrapping
                        pre.style.wordBreak = 'break-word'; // Break long words without overflow
                        pre.textContent = processedResponse; // Use textContent for safety
                        contentDiv.innerHTML = ''; // Clear previous content
                        contentDiv.appendChild(pre);
                    } else {
                        // With breaks=true, we need to preserve single newlines
                        // but ensure proper list formatting
                        const preparedText = processedResponse
                            // Ensure list items have proper formatting
                            .replace(/^(\d+\.|\*|-)\s+/gm, '$1 ') // Ensure proper spacing after list markers
                            // Don't convert single newlines to double newlines anymore since breaks=true
                            
                        console.log("PREPARED TEXT PREVIEW:", preparedText.substring(0, 200) + "...");
                        try {
                            // First check if raw output mode is enabled
                            if (showRawOutput) {
                                console.log("Displaying RAW output (non-streaming).");
                                // Display raw text, preserving whitespace and line breaks, safely
                                const pre = document.createElement('pre');
                                pre.style.whiteSpace = 'pre-wrap'; // Allow wrapping
                                pre.style.wordBreak = 'break-word'; // Break long words without overflow
                                pre.textContent = preparedText; // Use textContent for safety
                                contentDiv.innerHTML = ''; // Clear previous content
                                contentDiv.appendChild(pre);
                            } else {
                                contentDiv.innerHTML = window.MetisMarkdown.processResponse(preparedText);
                            }
                        } catch (markdownError) {
                            console.error("Error processing markdown:", markdownError);
                            // Fallback to basic formatting if markdown processing fails
                            contentDiv.innerHTML = `<pre>${preparedText}</pre>`;
                        }
                    }
                    
                    // Add class to indicate markdown processing is complete
                    contentDiv.classList.add('markdown-processed');
                    
                    // Log HTML structure after markdown processing
                    console.log("HTML STRUCTURE AFTER MARKDOWN PROCESSING:", {
                        paragraphTags: (contentDiv.innerHTML.match(/<p>/g) || []).length,
                        brTags: (contentDiv.innerHTML.match(/<br>/g) || []).length
                    });

                    addCitations(assistantMessageDiv, data.citations);
                    scrollToBottom();
                });
            }
        })
        .catch(error => {
            clearTimeout(timeoutId); // Clear timeout on fetch error
            console.error('Fetch Error:', error);
            if (loadingIndicator) loadingIndicator.style.display = 'none';
             handleErrorMessage(error, contentDiv, message, ragToggle, streamToggle, assistantMessageDiv);
        });
    }

    /**
     * Builds the query object for the API request.
     * @param {string} message The user's message.
     * @returns {object} The query object.
     */
    function buildQuery(message) {
        // Get the state of the raw output toggles
        const showRawOutput = rawOutputToggle?.checked ?? false;
        const showRawLlmOutput = rawLlmOutputToggle?.checked ?? false;
        
        const query = {
            message: message,
            model: modelSelect?.value || 'gemma3:4b',
            use_rag: ragToggle?.checked ?? true,
            conversation_id: currentConversationId,
            model_parameters: {},
            stream: streamToggle?.checked ?? false, // Default to false if toggle not found
            debug_raw: showRawOutput // Include raw output in response when toggle is checked
        };

        // Safely access values only if elements exist
        if (temperature) query.model_parameters.temperature = parseFloat(temperature.value);
        if (ragToggle?.checked && maxResults) query.model_parameters.max_results = parseInt(maxResults.value);

        if (ragToggle?.checked && metadataFilters?.value.trim()) {
            try {
                query.metadata_filters = JSON.parse(metadataFilters.value);
            } catch (e) {
                console.error('Invalid metadata filter JSON:', e);
                // Don't send invalid filters, maybe notify user later
            }
        }
        return query;
    }

    /**
     * Processes the streaming response from the API.
     * @param {ReadableStream} body The response body stream.
     * @param {HTMLElement} contentDiv The div where content will be rendered.
     * @param {HTMLElement} messageDiv The main message container div.
     */
    async function processStream(body, contentDiv, messageDiv) {
        console.log("STREAM PROCESSING STARTED");
        const reader = body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';
        let buffer = '';
        let conversationIdReceived = false;
        
        // Track paragraph structure during streaming
        let paragraphCount = 0;
        let newlineCount = 0;
        let doubleNewlineCount = 0;
        
        // Log streaming start time for performance tracking
        const streamStartTime = performance.now();

        try {
            console.log("BEGINNING STREAM READING LOOP");
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log("Stream finished.");
                    break;
                }

                buffer += decoder.decode(value, { stream: true });

                // Process buffer line by line (SSE events end with \n\n)
                let eventBoundary = buffer.indexOf('\n\n');
                while (eventBoundary !== -1) {
                    const eventData = buffer.substring(0, eventBoundary);
                    buffer = buffer.substring(eventBoundary + 2);

                    let currentEventType = null;
                    let dataLines = [];

                    eventData.split('\n').forEach(line => {
                        if (line.startsWith('event:')) {
                            currentEventType = line.substring(6).trim();
                        } else if (line.startsWith('data:')) {
                            dataLines.push(line.substring(5).trim());
                        }
                    });

                    const data = dataLines.join('\n'); // Re-join if data spans multiple lines

                    if (currentEventType === 'conversation_id' && data) {
                         if (!conversationIdReceived) {
                            try {
                                // Remove potential quotes if data is a JSON string
                                const conversationId = data.replace(/^"|"$/g, '');
                                updateConversationId(conversationId);
                                console.log('Conversation ID received in stream:', conversationId);
                                conversationIdReceived = true; // Ensure ID is processed only once
                            } catch (e) {
                                console.error('Error parsing conversation ID from stream:', e, 'Data:', data);
                            }
                         }
                    } else if (data) { // Process regular message data
                        try {
                            // Attempt to parse as JSON (newer format might send {"chunk": "..."})
                            let token = "";
                            try {
                                const jsonData = JSON.parse(data);
                                token = jsonData.chunk || data; // Fallback to raw data if no 'chunk' field
                            } catch (jsonError) {
                                token = data; // Assume older raw text format if JSON parse fails
                            }
                            fullResponse += token;
                            
                            // Update paragraph structure tracking
                            newlineCount = (fullResponse.match(/\n/g) || []).length;
                            doubleNewlineCount = (fullResponse.match(/\n\n/g) || []).length;
                            paragraphCount = doubleNewlineCount + 1;
                            
                            // Log streaming progress periodically (every 500 chars)
                            if (fullResponse.length % 500 === 0) {
                                console.log("STREAMING PROGRESS:", {
                                    length: fullResponse.length,
                                    paragraphs: paragraphCount,
                                    newlines: newlineCount,
                                    doubleNewlines: doubleNewlineCount
                                });
                            }

                            // Update UI with accumulated text during stream
                            let displayResponse = fullResponse;
                            const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s/i;
                            if (displayResponse.match(uuidPattern)) {
                                displayResponse = displayResponse.replace(uuidPattern, '');
                            }
                            
                            // Get the state of the raw output toggles
                            const showRawLlmOutput = rawLlmOutputToggle?.checked ?? false;
                            
                            if (showRawLlmOutput) {
                                // Display raw text during streaming
                                const pre = document.createElement('pre');
                                pre.style.whiteSpace = 'pre-wrap'; // Allow wrapping
                                pre.style.wordBreak = 'break-word'; // Break long words without overflow
                                pre.textContent = displayResponse; // Use textContent for safety
                                contentDiv.innerHTML = ''; // Clear any previous raw text
                                contentDiv.appendChild(pre);
                            } else {
                                // During streaming, we need to handle text differently
                                // Remove markdown-processed class during streaming if it exists
                                contentDiv.classList.remove('markdown-processed');
                                
                                // Improved streaming text formatting
                                // This preserves both paragraphs and list structures
                                let formattedStreamingText = displayResponse;
                                
                                // First handle list items (preserve their structure)
                                formattedStreamingText = formattedStreamingText
                                    // Format numbered lists
                                    .replace(/^(\d+\.)\s+(.+)$/gm, '<li class="numbered-list-item">$1 $2</li>')
                                    // Format bullet lists
                                    .replace(/^(\*|-)\s+(.+)$/gm, '<li class="bullet-list-item">$1 $2</li>');
                                    
                                // Then handle paragraphs
                                formattedStreamingText = formattedStreamingText
                                    .replace(/\n\n+/g, '</p><p>')
                                    .replace(/\n/g, '<br>');
                                
                                // Wrap in paragraph tags
                                contentDiv.innerHTML = '<p>' + formattedStreamingText + '</p>';
                            }
                            
                            // Log streaming text structure
                            if (fullResponse.length % 2000 === 0) {
                                console.log("STREAMING TEXT STRUCTURE:", {
                                    paragraphs: (displayResponse.match(/\n\n+/g) || []).length + 1,
                                    singleNewlines: (displayResponse.match(/\n/g) || []).length,
                                    doubleNewlines: (displayResponse.match(/\n\n+/g) || []).length
                                });
                                
                                // Log HTML structure during streaming
                                console.log("STREAMING HTML STRUCTURE:", {
                                    paragraphTags: (contentDiv.innerHTML.match(/<p>/g) || []).length,
                                    brTags: (contentDiv.innerHTML.match(/<br>/g) || []).length
                                });
                            }
                            
                            scrollToBottom();

                        } catch (e) {
                            console.error('Error processing stream data chunk:', e, 'Data:', data);
                        }
                    }
                    currentEventType = null; // Reset event type for next event
                    eventBoundary = buffer.indexOf('\n\n');
                }
            }

            // --- FINAL PROCESSING after stream ends ---
            const streamEndTime = performance.now();
            const streamDuration = streamEndTime - streamStartTime;
            console.log(`Stream complete in ${streamDuration.toFixed(2)}ms. Processing final response for Markdown.`);
            
            // Log final paragraph structure before markdown processing
            console.log("FINAL STREAM PARAGRAPH STRUCTURE:", {
                paragraphs: paragraphCount,
                newlines: newlineCount,
                doubleNewlines: doubleNewlineCount,
                totalLength: fullResponse.length
            });
            
            let finalProcessedResponse = fullResponse;
            const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s/i;
            if (finalProcessedResponse.match(uuidPattern)) {
                finalProcessedResponse = finalProcessedResponse.replace(uuidPattern, '');
            }
            
            console.log("SWITCHING FROM STREAMING TO FULL MARKDOWN PROCESSING");
            
            // Log the final text structure before markdown processing
            console.log("FINAL TEXT STRUCTURE BEFORE MARKDOWN:", {
                paragraphs: (finalProcessedResponse.match(/\n\n+/g) || []).length + 1,
                singleNewlines: (finalProcessedResponse.match(/\n/g) || []).length,
                doubleNewlines: (finalProcessedResponse.match(/\n\n+/g) || []).length
            });
            
            // Process the complete response for Markdown, highlighting, and copy buttons
            const markdownStartTime = performance.now();
            
            // Get the state of the raw output toggle (in case it changed during streaming)
            const showRawOutput = rawOutputToggle?.checked ?? false;
            
            if (showRawOutput) {
                console.log("Displaying RAW output (streaming final).");
                // Display raw text, preserving whitespace and line breaks, safely
                const pre = document.createElement('pre');
                pre.style.whiteSpace = 'pre-wrap'; // Allow wrapping
                pre.style.wordBreak = 'break-word'; // Break long words without overflow
                pre.textContent = finalProcessedResponse; // Use textContent for safety
                contentDiv.innerHTML = ''; // Clear any previous raw text
                contentDiv.appendChild(pre);
            } else {
                // With breaks=true, we need to preserve single newlines
                // but ensure proper list formatting
                const preparedText = finalProcessedResponse
                    // Ensure list items have proper formatting
                    .replace(/^(\d+\.|\*|-)\s+/gm, '$1 '); // Ensure proper spacing after list markers
                    // Don't convert single newlines to double newlines anymore since breaks=true
                    
                console.log("FINAL PREPARED TEXT PREVIEW:", preparedText.substring(0, 200) + "...");
                try {
                    // First check if raw output mode is enabled
                    if (showRawOutput) {
                        console.log("Displaying RAW output (streaming final).");
                        // Display raw text, preserving whitespace and line breaks, safely
                        const pre = document.createElement('pre');
                        pre.style.whiteSpace = 'pre-wrap'; // Allow wrapping
                        pre.style.wordBreak = 'break-word'; // Break long words without overflow
                        pre.textContent = preparedText; // Use textContent for safety
                        contentDiv.innerHTML = ''; // Clear any previous raw text
                        contentDiv.appendChild(pre);
                    } else {
                        contentDiv.innerHTML = window.MetisMarkdown.processResponse(preparedText);
                    }
                } catch (markdownError) {
                    console.error("Error processing markdown in streaming mode:", markdownError);
                    // Fallback to basic formatting if markdown processing fails
                    contentDiv.innerHTML = `<pre>${preparedText}</pre>`;
                }
                
                // Add class to indicate markdown processing is complete
                contentDiv.classList.add('markdown-processed');
            }
            const markdownEndTime = performance.now();
            
            // Log HTML structure after markdown processing
            console.log("HTML STRUCTURE AFTER MARKDOWN PROCESSING:", {
                paragraphTags: (contentDiv.innerHTML.match(/<p>/g) || []).length,
                brTags: (contentDiv.innerHTML.match(/<br>/g) || []).length
            });
            console.log(`Markdown processing completed in ${(markdownEndTime - markdownStartTime).toFixed(2)}ms`);
            
            scrollToBottom();
            // --- End Final Processing ---

        } catch (error) {
            console.error('Error reading stream:', error);
            // Handle error display in the UI
            if (fullResponse) { // Show partial response if any
                 contentDiv.innerHTML = window.MetisMarkdown.processResponse(fullResponse + "\n\n[Error processing stream]");
            } else {
                 contentDiv.textContent = 'Error processing response stream.';
            }
        } finally {
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            // Release the lock
             try {
                 reader.releaseLock();
             } catch (e) {
                 console.warn("Could not release stream reader lock:", e);
             }
        }
    }


    /**
     * Adds a message (user or assistant) to the chat interface.
     * @param {string} role 'user' or 'assistant'.
     * @param {string} content The message content (raw text).
     * @param {Array | null} citations List of citations for assistant messages.
     * @param {boolean} isPlaceholder If true, creates an empty structure for population later.
     * @returns {HTMLElement} The created message element.
     */
    function addMessage(role, content, citations = null, isPlaceholder = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;

        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        headerDiv.textContent = role === 'user' ? 'You:' : 'Metis:';
        messageDiv.appendChild(headerDiv);

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content preserve-paragraphs'; // Add classes for styling

        if (!isPlaceholder) {
             if (role === 'user') {
                 contentDiv.textContent = content; // User messages as plain text
             } else {
                 // Let the caller handle processing for assistant messages later
                 contentDiv.innerHTML = "Processing..."; // Or leave empty
             }
        }
        // For placeholders, contentDiv remains empty initially

        messageDiv.appendChild(contentDiv);

        // Placeholder for citations if needed later (only for assistant)
        if (role === 'assistant') {
             const citationsContainer = document.createElement('div');
             citationsContainer.className = 'sources-section';
             citationsContainer.style.display = 'none'; // Hide initially
             messageDiv.appendChild(citationsContainer);
        }

        if (chatContainer) {
             chatContainer.appendChild(messageDiv);
             scrollToBottom();
        } else {
            console.error("Chat container not found, cannot add message.");
        }
        return messageDiv; // Return the main message element
    }


    /**
    * Adds citations to an existing assistant message div.
    * @param {HTMLElement} messageDiv The main assistant message element.
    * @param {Array | null} citations List of citation objects.
    */
    function addCitations(messageDiv, citations) {
        if (!citations || citations.length === 0) return;

        const citationsContainer = messageDiv.querySelector('.sources-section');
        if (!citationsContainer) return; // Should exist from addMessage

        citationsContainer.innerHTML = '<strong>Sources:</strong> '; // Clear previous/placeholder content

        citations.forEach((citation, index) => {
            const sourceSpan = document.createElement('span');
            sourceSpan.className = 'source-item';
            // Display filename if available, otherwise document_id
            const displayName = citation.filename || citation.document_id || `Source ${index + 1}`;
            sourceSpan.textContent = `[${index + 1}] ${displayName}`;
            sourceSpan.title = citation.excerpt || 'No excerpt available';
            citationsContainer.appendChild(sourceSpan);
        });

        citationsContainer.style.display = 'block'; // Make visible
    }


    /**
     * Scrolls the chat container to the bottom.
     */
    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    /**
     * Sends a request to the server to clear the conversation history.
     */
    function clearConversationOnServer() {
        authenticatedFetch('/api/chat/clear', { method: 'DELETE' })
            .then(response => response.json())
            .then(data => console.log('Server conversation cleared:', data))
            .catch(error => console.error('Error clearing server conversation:', error));
    }

    /**
     * Handles and displays error messages in the chat.
     * @param {Error} error The error object.
     * @param {HTMLElement} contentDiv The div where the error message should be displayed.
     * @param {string} originalMessage The original user message that caused the error.
     * @param {HTMLInputElement} ragToggle RAG toggle element.
     * @param {HTMLInputElement} streamToggle Streaming toggle element.
     * @param {HTMLElement} messageDiv The main message container div.
     */
    function handleErrorMessage(error, contentDiv, originalMessage, ragToggle, streamToggle, messageDiv) {
        let errorText = 'Sorry, there was an error processing your request. ';
        console.error("Handling error message:", error); // Log the full error

        if (error.name === 'AbortError') {
             errorText = 'The request timed out. The server might be overloaded or the request took too long. ';
             if (streamToggle?.checked) {
                 errorText += 'Try disabling streaming mode.';
                 // No automatic retry here, let user decide.
             } else {
                 errorText += 'Please try again later.';
             }
        } else if (error.message.includes('Failed to fetch')) {
             errorText = 'Could not connect to the server. Please ensure the Metis RAG application is running.';
        } else {
             // Check for specific error patterns from the user query analysis
             const currentYear = new Date().getFullYear();
             const queryLower = originalMessage.toLowerCase();
             const yearMatch = queryLower.match(/\b(20\d\d|19\d\d)\b/);

             if (yearMatch && parseInt(yearMatch[1]) > currentYear) {
                 errorText = `I cannot provide information about events in ${yearMatch[1]} as it's in the future. The current year is ${currentYear}. I can only provide information about past or current events.`;
             } else if (/what will happen|what is going to happen|predict the future|future events|in the future/.test(queryLower)) {
                 errorText = "I cannot predict future events or provide information about what will happen in the future. I can only provide information about past or current events based on available data.";
             } else if (ragToggle?.checked) {
                 errorText += 'This might be because there are no documents available for RAG or an issue occurred during retrieval. Try uploading documents or disabling RAG.';
             } else {
                 errorText += 'Please check your query or try again later.';
             }
        }

        // Display the error in the designated content div
        if (contentDiv) {
             contentDiv.textContent = errorText;
        } else if (messageDiv) {
             // Fallback if contentDiv wasn't found (shouldn't happen ideally)
             messageDiv.innerHTML += `<div class="message-content error">${errorText}</div>`;
        }


        // Optionally add retry button for streaming timeouts if stream toggle exists
        if (error.name === 'AbortError' && streamToggle) {
             const retryButton = document.createElement('button');
             retryButton.textContent = 'Retry without streaming';
             retryButton.className = 'retry-button'; // Add class for styling
             retryButton.onclick = function() {
                 streamToggle.checked = false; // Disable streaming
                 // Resend the original message
                 if(userInput && sendButton) {
                     userInput.value = originalMessage; // Put message back for resend
                     sendButton.click();
                     // Remove the retry button after click
                     if(messageDiv && retryButton.parentNode === messageDiv) {
                         messageDiv.removeChild(retryButton);
                     }
                 }
             };
             // Append button to the messageDiv if it exists
             if (messageDiv) {
                 messageDiv.appendChild(retryButton);
             }
        }
    }

    /**
     * Shows a notification message to the user.
     * @param {string} message The message to display.
     * @param {string} type The type of notification ('info', 'error', 'success').
     */
    function showNotification(message, type = 'info') {
        console.log(`Notification (${type}): ${message}`);
        // Implement UI notification if needed
        // For now, just log to console
    }

}); // End DOMContentLoaded