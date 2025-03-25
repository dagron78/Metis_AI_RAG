// Chat functionality
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-chat');
    const saveButton = document.getElementById('save-chat');
    const modelSelect = document.getElementById('model');
    const ragToggle = document.getElementById('rag-toggle');
    const streamToggle = document.getElementById('stream-toggle');
    const loadingIndicator = document.getElementById('loading');
    const maxResults = document.getElementById('max-results');
    const temperature = document.getElementById('temperature');
    const metadataFilters = document.getElementById('metadata-filters');
    
    // Store conversation ID for maintaining context between messages
    let currentConversationId = null;
    
    // Toggle RAG parameters visibility
    if (ragToggle) {
        ragToggle.addEventListener('change', function() {
            const ragParams = document.querySelectorAll('.rag-param');
            ragParams.forEach(param => {
                param.style.display = this.checked ? 'block' : 'none';
            });
        });
    }
    
    // Load available models
    if (modelSelect) {
        console.log('Loading models...');
        authenticatedFetch('/api/system/models')
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(models => {
                console.log('Models fetched:', models);
                console.log('Number of models:', models.length);
                
                // Clear the dropdown
                modelSelect.innerHTML = '';
                
                if (models && models.length > 0) {
                    // Add models to dropdown
                    models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model.name;
                        option.textContent = model.name;
                        modelSelect.appendChild(option);
                        console.log('Added model to dropdown:', model.name);
                    });
                } else {
                    // Add a default option if no models are available
                    const option = document.createElement('option');
                    option.value = 'gemma3:4b';
                    option.textContent = 'gemma3:4b (default)';
                    modelSelect.appendChild(option);
                    console.log('No models available, added default model');
                }
            })
            .catch(error => {
                console.error('Error loading models:', error);
            });
    }
    
    // Send message
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Check if user is authenticated
        if (!isAuthenticated()) {
            // Redirect to login page
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
            return;
        }
        
        // Log the selected model
        console.log('Selected model for this message:', modelSelect.value);
        
        // Add user message to conversation
        addMessage('user', message);
        
        // Clear input
        userInput.value = '';
        
        // Show loading indicator
        loadingIndicator.style.display = 'block';
        
        // Prepare query
        const query = {
            message: message,
            model: modelSelect.value || 'gemma3:4b', // Use default model if none selected
            use_rag: ragToggle.checked,
            conversation_id: currentConversationId, // Include conversation ID if available
            model_parameters: {
                temperature: parseFloat(temperature.value),
                max_results: ragToggle.checked ? parseInt(maxResults.value) : 0
            }
        };
        
        // Log the query being sent
        console.log('Sending query with model:', query.model);
        
        // Parse metadata filters if provided
        if (ragToggle.checked && metadataFilters.value.trim()) {
            try {
                query.metadata_filters = JSON.parse(metadataFilters.value);
            } catch (e) {
                console.error('Invalid metadata filter JSON:', e);
                addMessage('assistant', 'Error: Invalid metadata filter format. Please use valid JSON.');
                loadingIndicator.style.display = 'none';
                return;
            }
        }
        // Use streaming based on the toggle
        query.stream = streamToggle.checked;
        
        // Create message element for assistant response
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        
        // Add header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        headerDiv.textContent = 'Metis:';
        messageDiv.appendChild(headerDiv);
        
        // Add content div for streaming response
        const contentDiv = document.createElement('div');
        contentDiv.id = 'streaming-response';
        messageDiv.appendChild(contentDiv);
        
        // Add to chat container
        chatContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Send to API with a timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
        
        authenticatedFetch('/api/chat/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(query),
            signal: controller.signal
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            if (query.stream) {
                // Handle streaming response
                // Create a new reader for the response
                const reader = response.body.getReader();
                let decoder = new TextDecoder();
                let fullResponse = '';
                
                // Variable to track if the previous line was a conversation_id event
                let previousLineWasConversationIdEvent = false;
                
                // Function to process the stream with improved error handling
                function processStream() {
                    let streamTimeout;
                    let lastActivityTime = Date.now();
                    
                    // Set a timeout for the stream reading
                    const setStreamTimeout = () => {
                        clearTimeout(streamTimeout);
                        streamTimeout = setTimeout(() => {
                            // Check if we've had activity in the last 10 seconds
                            const inactiveTime = Date.now() - lastActivityTime;
                            if (inactiveTime > 10000) {
                                console.warn(`Stream reading timeout after ${inactiveTime}ms of inactivity - aborting`);
                                reader.cancel('Timeout');
                                
                                // Try again without streaming
                                if (streamToggle.checked) {
                                    // Update UI to show we're retrying
                                    contentDiv.textContent = 'The streaming response timed out. Retrying without streaming...';
                                    
                                    // Disable streaming and retry
                                    streamToggle.checked = false;
                                    sendButton.click();
                                }
                            } else {
                                // Reset the timeout
                                setStreamTimeout();
                            }
                        }, 5000); // Check every 5 seconds
                    };
                    
                    // Start the timeout
                    setStreamTimeout();
                    
                    return reader.read().then(({ done, value }) => {
                        // Update the last activity time
                        lastActivityTime = Date.now();
                        
                        if (done) {
                            // Clear the timeout when done
                            clearTimeout(streamTimeout);
                            
                            // Hide loading indicator when done
                            loadingIndicator.style.display = 'none';
                            return;
                        }
                        
                        // Decode the chunk and append to the response
                        const chunk = decoder.decode(value, { stream: true });
                        
                        // Process the chunk (which may contain multiple SSE events)
                        const lines = chunk.split('\n');
                        for (const line of lines) {
                            // Check for event type
                            if (line.startsWith('event:')) {
                                const eventType = line.substring(6).trim();
                                // Handle conversation_id event
                                if (eventType === 'conversation_id') {
                                    // The next line should be the data
                                    previousLineWasConversationIdEvent = true;
                                    continue;
                                }
                            }
                            else if (line.startsWith('data:')) {
                                const data = line.substring(5).trim();
                                if (data) {
                                    try {
                                        // Try to parse as JSON (for newer format)
                                        try {
                                            const jsonData = JSON.parse(data);
                                            
                                            // Check if this is conversation ID data
                                            if (previousLineWasConversationIdEvent) {
                                                try {
                                                    // The data should be the conversation ID
                                                    // Remove any quotes if present (in case it's a JSON string)
                                                    currentConversationId = data.replace(/^"|"$/g, '');
                                                    console.log('Conversation ID received in stream:', currentConversationId);
                                                } catch (e) {
                                                    console.error('Error parsing conversation ID:', e);
                                                }
                                                previousLineWasConversationIdEvent = false;
                                                continue; // Skip adding this to the response
                                            }
                                            
                                            if (jsonData.chunk) {
                                                fullResponse += jsonData.chunk;
                                            } else {
                                                fullResponse += data;
                                            }
                                        } catch (e) {
                                            // Skip if this is the conversation ID data that wasn't properly caught earlier
                                            if (previousLineWasConversationIdEvent) {
                                                // The data should be the conversation ID
                                                currentConversationId = data.replace(/^"|"$/g, '');
                                                console.log('Conversation ID received in stream (fallback):', currentConversationId);
                                                previousLineWasConversationIdEvent = false;
                                            } else {
                                                // If not JSON and not conversation ID, append the data (older format)
                                                // With streaming tokens from Ollama, we should not add spaces
                                                // as the model already handles proper spacing
                                                fullResponse += data;
                                            }
                                        }
                                    } catch (e) {
                                        console.error('Error processing chunk:', e);
                                    }
                                }
                            }
                        }
                        
                        // Update the content div with the current response
                        // Check if the response starts with a UUID pattern (conversation ID)
                        const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s/i;
                        if (fullResponse.match(uuidPattern)) {
                            // Remove the UUID from the beginning of the response
                            contentDiv.textContent = fullResponse.replace(uuidPattern, '');
                        } else {
                            contentDiv.textContent = fullResponse;
                        }
                        
                        // Scroll to bottom
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                        
                        // Continue reading
                        return processStream();
                    }).catch(error => {
                        // Clear the timeout
                        clearTimeout(streamTimeout);
                        
                        console.error('Error reading stream:', error);
                        
                        // If we already have some response, show it
                        if (fullResponse.length > 0) {
                            contentDiv.textContent = fullResponse + "\n\n[Response was cut off due to a connection issue]";
                            
                            // Add a note about the error
                            const noteDiv = document.createElement('div');
                            noteDiv.className = 'streaming-note';
                            noteDiv.textContent = '(Note: The response was cut off due to a connection issue)';
                            noteDiv.style.fontSize = '0.8em';
                            noteDiv.style.fontStyle = 'italic';
                            noteDiv.style.marginTop = '10px';
                            noteDiv.style.color = 'var(--muted-color)';
                            messageDiv.appendChild(noteDiv);
                        } else {
                            // Update the content div with an error message
                            contentDiv.textContent = 'There was an error processing your request. ' +
                                'This might be due to a connection issue with the language model. ' +
                                'Try disabling streaming mode or check if the Ollama server is running properly.';
                        }
                        
                        // Hide loading indicator
                        loadingIndicator.style.display = 'none';
                        
                        // Add a retry button
                        const retryButton = document.createElement('button');
                        retryButton.textContent = 'Retry without streaming';
                        retryButton.className = 'retry-button';
                        retryButton.onclick = function() {
                            // Disable streaming and retry
                            if (streamToggle && streamToggle.checked) {
                                streamToggle.checked = false;
                                sendButton.click();
                            }
                        };
                        messageDiv.appendChild(retryButton);
                    });
                }
                
                // Start processing the stream
                return processStream();
            } else {
                // Handle non-streaming response
                return response.json().then(data => {
                    // Hide loading indicator
                    loadingIndicator.style.display = 'none';
                    
                    // Store conversation ID for future messages
                    if (data.conversation_id) {
                        currentConversationId = data.conversation_id;
                        console.log('Conversation ID updated:', currentConversationId);
                    }
                    
                    // Display the response
                    // Check if the response starts with a UUID pattern (conversation ID)
                    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s/i;
                    if (data.message && data.message.match(uuidPattern)) {
                        // Remove the UUID from the beginning of the response
                        contentDiv.textContent = data.message.replace(uuidPattern, '');
                    } else {
                        contentDiv.textContent = data.message;
                    }
                    
                    // Scroll to bottom
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                    
                    // Add citations if available
                    if (data.citations && data.citations.length > 0) {
                        const citationsDiv = document.createElement('div');
                        citationsDiv.className = 'sources-section';
                        citationsDiv.innerHTML = '<strong>Sources:</strong> ';
                        
                        data.citations.forEach(citation => {
                            const sourceSpan = document.createElement('span');
                            sourceSpan.className = 'source-item';
                            sourceSpan.textContent = citation.document_id;
                            sourceSpan.title = citation.excerpt;
                            citationsDiv.appendChild(sourceSpan);
                        });
                        
                        messageDiv.appendChild(citationsDiv);
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Check if it's an abort error (timeout)
            if (error.name === 'AbortError') {
                console.log('Request timed out, trying again without streaming');
                
                // If streaming was enabled, try again without streaming
                if (streamToggle.checked) {
                    // Update UI to show we're retrying
                    contentDiv.textContent = 'The streaming request timed out. Retrying without streaming...';
                    
                    // Disable streaming and retry
                    query.stream = false;
                    
                    // Clear the previous timeout
                    clearTimeout(timeoutId);
                    
                    // Send the request again without streaming
                    authenticatedFetch('/api/chat/query', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(query)
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Hide loading indicator
                        loadingIndicator.style.display = 'none';
                        
                        // Store conversation ID for future messages
                        if (data.conversation_id) {
                            currentConversationId = data.conversation_id;
                            console.log('Conversation ID updated:', currentConversationId);
                        }
                        
                        // Display the response
                        contentDiv.textContent = data.message;
                        
                        // Add a note that streaming was disabled
                        const noteDiv = document.createElement('div');
                        noteDiv.className = 'streaming-note';
                        noteDiv.textContent = '(Note: Streaming was disabled due to timeout)';
                        noteDiv.style.fontSize = '0.8em';
                        noteDiv.style.fontStyle = 'italic';
                        noteDiv.style.marginTop = '10px';
                        noteDiv.style.color = 'var(--muted-color)';
                        messageDiv.appendChild(noteDiv);
                        
                        // Uncheck streaming toggle for future requests
                        streamToggle.checked = false;
                    })
                    .catch(fallbackError => {
                        console.error('Error in fallback request:', fallbackError);
                        handleErrorMessage(fallbackError, contentDiv, message, ragToggle, streamToggle);
                        loadingIndicator.style.display = 'none';
                    });
                } else {
                    // If streaming was already disabled, show a regular error
                    handleErrorMessage(error, contentDiv, message, ragToggle, streamToggle);
                    loadingIndicator.style.display = 'none';
                }
            } else {
                // For other types of errors
                handleErrorMessage(error, contentDiv, message, ragToggle, streamToggle);
                loadingIndicator.style.display = 'none';
            }
        });
        
        // Helper function to handle error messages
        function handleErrorMessage(error, contentDiv, message, ragToggle, streamToggle) {
            // Add error message with more details
            contentDiv.textContent = 'Sorry, there was an error processing your request. ';
            
            // Check if the query is about future events
            const currentYear = new Date().getFullYear();
            const queryLower = message.toLowerCase();
            const yearMatch = queryLower.match(/\b(20\d\d|19\d\d)\b/);
            
            if (yearMatch && parseInt(yearMatch[1]) > currentYear) {
                contentDiv.textContent = `I cannot provide information about events in ${yearMatch[1]} as it's in the future. ` +
                    `The current year is ${currentYear}. I can only provide information about past or current events.`;
            }
            // Check if the query is about speculative future events
            else if (/what will happen|what is going to happen|predict the future|future events|in the future/.test(queryLower)) {
                contentDiv.textContent = "I cannot predict future events or provide information about what will happen in the future. " +
                    "I can only provide information about past or current events based on available data.";
            }
            // Add suggestion based on RAG status
            else if (ragToggle.checked) {
                contentDiv.textContent += 'This might be because there are no documents available for RAG. ' +
                    'Try uploading some documents or disabling the RAG feature.';
            }
            // Add suggestion based on streaming status
            else if (streamToggle.checked) {
                contentDiv.textContent += 'You might try disabling streaming mode for better error handling. ';
                
                // Add a retry button
                const retryButton = document.createElement('button');
                retryButton.textContent = 'Retry without streaming';
                retryButton.className = 'retry-button';
                retryButton.onclick = function() {
                    // Disable streaming and retry
                    streamToggle.checked = false;
                    sendButton.click();
                };
                messageDiv.appendChild(retryButton);
            }
            else {
                contentDiv.textContent += 'Please try again later or with different parameters.';
            }
        }
    }
    
    // Clear chat
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear the chat history?')) {
                clearConversation();
                chatContainer.innerHTML = '';
                
                // Add welcome message
                const welcomeMessage = document.createElement('div');
                welcomeMessage.className = 'message bot-message';
                welcomeMessage.innerHTML = `
                    <div class="message-header">Metis:</div>
                    Hello! I'm your Metis RAG assistant. Ask me anything about your uploaded documents or chat with me directly.
                `;
                chatContainer.appendChild(welcomeMessage);
            }
        });
    }
    
    // Add message to chat
    function addMessage(role, content, citations = null) {
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        // Add header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        headerDiv.textContent = role === 'user' ? 'You:' : 'Metis:';
        messageDiv.appendChild(headerDiv);
        
        // Add content
        const contentDiv = document.createElement('div');
        contentDiv.textContent = content;
        messageDiv.appendChild(contentDiv);
        
        // Add citations if available
        if (citations && citations.length > 0) {
            const citationsDiv = document.createElement('div');
            citationsDiv.className = 'sources-section';
            citationsDiv.innerHTML = '<strong>Sources:</strong> ';
            
            citations.forEach(citation => {
                const sourceSpan = document.createElement('span');
                sourceSpan.className = 'source-item';
                sourceSpan.textContent = citation.document_id;
                sourceSpan.title = citation.excerpt;
                citationsDiv.appendChild(sourceSpan);
            });
            
            messageDiv.appendChild(citationsDiv);
        }
        
        // Add to chat container
        chatContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Clear conversation
    function clearConversation() {
        // Reset conversation ID
        currentConversationId = null;
        console.log('Conversation ID reset');
        
        // Clear conversation from local storage or API
        authenticatedFetch('/api/chat/clear', {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Conversation cleared:', data);
            // Use the globally exposed clearConversation function from main.js
            // This ensures proper clearing of localStorage and updating the UI
            if (window.clearConversation) {
                window.clearConversation();
            } else {
                // Fallback if the global function isn't available
                localStorage.removeItem('metis_conversation');
                console.warn('window.clearConversation not found, using fallback clear method');
            }
        })
        .catch(error => {
            console.error('Error clearing conversation:', error);
        });
    }
    
    // Event listeners
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    if (userInput) {
        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});