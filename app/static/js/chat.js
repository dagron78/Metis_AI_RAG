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
        fetch('/api/system/models')
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(models => {
                console.log('Models fetched:', models);
                console.log('Number of models:', models.length);
                
                // Clear the dropdown
                modelSelect.innerHTML = '';
                
                // Add models to dropdown
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = model.name;
                    modelSelect.appendChild(option);
                    console.log('Added model to dropdown:', model.name);
                });
            })
            .catch(error => {
                console.error('Error loading models:', error);
            });
    }
    
    // Send message
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
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
            model: modelSelect.value,
            use_rag: ragToggle.checked,
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
        
        // Send to API
        fetch('/api/chat/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(query)
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
                
                // Function to process the stream
                function processStream() {
                    return reader.read().then(({ done, value }) => {
                        if (done) {
                            // Hide loading indicator when done
                            loadingIndicator.style.display = 'none';
                            return;
                        }
                        
                        // Decode the chunk and append to the response
                        const chunk = decoder.decode(value, { stream: true });
                        
                        // Process the chunk (which may contain multiple SSE events)
                        const lines = chunk.split('\n');
                        for (const line of lines) {
                            if (line.startsWith('data:')) {
                                const data = line.substring(5).trim();
                                if (data) {
                                    try {
                                        // Try to parse as JSON (for newer format)
                                        try {
                                            const jsonData = JSON.parse(data);
                                            if (jsonData.chunk) {
                                                fullResponse += jsonData.chunk;
                                            } else {
                                                fullResponse += data;
                                            }
                                        } catch (e) {
                                            // If not JSON, just append the data (older format)
                                            // Check if we need to add a space before the new token
                                            const needsSpace = fullResponse.length > 0 &&
                                                              !fullResponse.endsWith(' ') &&
                                                              !fullResponse.endsWith('\n') &&
                                                              !fullResponse.endsWith('.') &&
                                                              !fullResponse.endsWith(',') &&
                                                              !fullResponse.endsWith('!') &&
                                                              !fullResponse.endsWith('?') &&
                                                              !fullResponse.endsWith(':') &&
                                                              !fullResponse.endsWith(';') &&
                                                              !fullResponse.endsWith('(') &&
                                                              !data.startsWith(' ') &&
                                                              !data.startsWith('\n') &&
                                                              !data.startsWith('.') &&
                                                              !data.startsWith(',') &&
                                                              !data.startsWith('!') &&
                                                              !data.startsWith('?') &&
                                                              !data.startsWith(':') &&
                                                              !data.startsWith(';') &&
                                                              !data.startsWith(')');
                                            
                                            if (needsSpace) {
                                                fullResponse += ' ';
                                            }
                                            
                                            fullResponse += data;
                                        }
                                    } catch (e) {
                                        console.error('Error processing chunk:', e);
                                    }
                                }
                            }
                        }
                        
                        // Update the content div with the current response
                        contentDiv.textContent = fullResponse;
                        
                        // Scroll to bottom
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                        
                        // Continue reading
                        return processStream();
                    }).catch(error => {
                        console.error('Error reading stream:', error);
                        loadingIndicator.style.display = 'none';
                    });
                }
                
                // Start processing the stream
                return processStream();
            } else {
                // Handle non-streaming response
                return response.json().then(data => {
                    // Hide loading indicator
                    loadingIndicator.style.display = 'none';
                    
                    // Display the response
                    contentDiv.textContent = data.message;
                    
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
            }
            else {
                contentDiv.textContent += 'Please try again later or with different parameters.';
            }
            
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
        });
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
        // Clear conversation from local storage or API
        fetch('/api/chat/clear', {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Conversation cleared:', data);
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