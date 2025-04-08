// Theme switching functionality
document.addEventListener('DOMContentLoaded', function() {



    // Check for saved theme preference or default to 'dark'
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Update theme toggle button
    updateThemeToggle(savedTheme);
    
    // Set up theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
});

// Toggle theme function
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeToggle(newTheme);
}

// Update theme toggle button
function updateThemeToggle(theme) {
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        toggle.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.backgroundColor = type === 'warning' ? '#ff9800' : 'var(--secondary-color)';
    notification.style.color = 'white';
    notification.style.padding = '10px 15px';
    notification.style.borderRadius = '4px';
    notification.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
    notification.style.zIndex = '1000';
    notification.style.maxWidth = '300px';
    notification.textContent = message;
    
    // Add close button
    const closeBtn = document.createElement('span');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.marginLeft = '10px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.fontWeight = 'bold';
    closeBtn.onclick = function() {
        document.body.removeChild(notification);
    };
    notification.appendChild(closeBtn);
    
    // Add to body
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 5000);
}

// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!');
    }).catch(err => {
        console.error('Could not copy text: ', err);
        showNotification('Failed to copy to clipboard', 'warning');
    });
}

// Conversation Management
// Make conversation globally accessible
window.conversation = {
    messages: [],
    metadata: {
        estimatedTokens: 0,
        maxTokens: 4096,
        lastUpdated: new Date().toISOString()
    }
};
// Reference for local use
let conversation = window.conversation;

// Token estimation (rough approximation - 1 token ≈ 4 characters)
function estimateTokens(text) {
    return Math.ceil(text.length / 4);
}

// Add message to conversation
function addMessage(role, content, sources = null) {
    conversation.messages.push({
        role: role,
        content: content,
        sources: sources,
        timestamp: new Date().toISOString()
    });
    
    const tokens = estimateTokens(content);
    conversation.metadata.estimatedTokens += tokens;
    conversation.metadata.lastUpdated = new Date().toISOString();
    
    saveToLocalStorage();
    updateTokenDisplay();
}

// Get formatted conversation history for prompt
function getConversationHistory() {
    let history = '';
    conversation.messages.forEach(msg => {
        const role = msg.role === 'user' ? 'User' : 'Metis';
        history += `${role}: ${msg.content}\n\n`;
    });
    return history;
}

// Get formatted conversation for Ollama
function getFormattedPrompt(newPrompt) {
    // First check if we need to trim the conversation
    trimConversationToFit(conversation.metadata.maxTokens);
    
    // Then format the conversation with the new prompt
    let formattedPrompt = '';
    
    // Add conversation history
    conversation.messages.forEach(msg => {
        const role = msg.role === 'user' ? 'User' : 'Metis';
        formattedPrompt += `${role}: ${msg.content}\n\n`;
    });
    
    // Add the new prompt
    formattedPrompt += `User: ${newPrompt}\n\nMetis:`;
    
    return formattedPrompt;
}

// Clear conversation
function clearConversation() {
    window.conversation = {
        messages: [],
        metadata: {
            estimatedTokens: 0,
            maxTokens: parseInt(document.getElementById('num_ctx')?.value || 4096),
            lastUpdated: new Date().toISOString()
        }
    };
    // Update local reference
    conversation = window.conversation;
    saveToLocalStorage();
    updateTokenDisplay();
}

// Make clearConversation globally accessible
window.clearConversation = clearConversation;

// Save conversation to localStorage
function saveToLocalStorage() {
    localStorage.setItem('metis_conversation', JSON.stringify(conversation));
}

// Load conversation from localStorage
function loadFromLocalStorage() {
    const saved = localStorage.getItem('metis_conversation');
    if (saved) {
        try {
            conversation = JSON.parse(saved);
            // Update max tokens from current form value
            const numCtxElement = document.getElementById('num_ctx');
            if (numCtxElement) {
                conversation.metadata.maxTokens = parseInt(numCtxElement.value) || 4096;
            }
            updateTokenDisplay();
            return true;
        } catch (e) {
            console.error('Error loading conversation:', e);
            return false;
        }
    }
    return false;
}

// Get total token count for conversation
function getConversationTokenCount() {
    return conversation.metadata.estimatedTokens;
}

// Trim conversation to fit within token limit
function trimConversationToFit(maxTokens) {
    // Reserve tokens for the new prompt and response (rough estimate)
    const reservedTokens = 1000;
    const availableTokens = maxTokens - reservedTokens;
    
    // If we're already under the limit, no need to trim
    if (getConversationTokenCount() <= availableTokens) {
        return;
    }
    
    // Remove oldest messages until we're under the limit
    while (getConversationTokenCount() > availableTokens && conversation.messages.length > 0) {
        const removedMsg = conversation.messages.shift();
        conversation.metadata.estimatedTokens -= estimateTokens(removedMsg.content);
    }
    
    // Update localStorage and UI
    saveToLocalStorage();
    updateTokenDisplay();
    
    // Show a notification that some messages were removed
    showNotification('Some older messages were removed to stay within the token limit.');
}

// Update token display
function updateTokenDisplay() {
    const tokenUsage = document.getElementById('token-usage');
    const tokenUsageFill = document.getElementById('token-usage-fill');
    const tokenUsageText = document.getElementById('token-usage-text');
    
    if (!tokenUsage || !tokenUsageFill || !tokenUsageText) return;
    
    const currentTokens = getConversationTokenCount();
    const maxTokens = conversation.metadata.maxTokens;
    const percentage = Math.min((currentTokens / maxTokens) * 100, 100);
    
    tokenUsageFill.style.width = `${percentage}%`;
    tokenUsageText.textContent = `${currentTokens} / ${maxTokens} tokens`;
    
    // Set color based on usage
    if (percentage > 90) {
        tokenUsageFill.style.backgroundColor = '#d32f2f'; // Red for high usage
    } else if (percentage > 70) {
        tokenUsageFill.style.backgroundColor = '#ff9800'; // Orange for medium usage
    } else {
        tokenUsageFill.style.backgroundColor = 'var(--accent-color)'; // Default color
    }
    
    // Show the token usage indicator if we have messages
    if (conversation.messages.length > 0) {
        tokenUsage.style.display = 'block';
    } else {
        tokenUsage.style.display = 'none';
    }
}

// Initialize conversation
function initConversation() {
    // Try to load from localStorage
    if (!loadFromLocalStorage()) {
        // If no saved conversation, initialize a new one
        clearConversation();
    }
    
    // Render the conversation if there's a chat container
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        renderConversation();
    }
    
    // Update token display
    updateTokenDisplay();
}

// Render conversation in UI
function renderConversation() {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;
    
    chatContainer.innerHTML = '';
    
    conversation.messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.role === 'user' ? 'user-message' : 'bot-message'}`;
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        headerDiv.textContent = msg.role === 'user' ? 'You:' : 'Metis:';
        messageDiv.appendChild(headerDiv);
        
        const contentText = document.createTextNode(msg.content);
        messageDiv.appendChild(contentText);
        
        if (msg.role === 'assistant') {
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.innerHTML = '<i class="fas fa-copy"></i> Copy';
            copyButton.onclick = function() {
                copyToClipboard(msg.content);
            };
            messageDiv.appendChild(copyButton);
            
            // Add sources if available
            if (msg.sources && msg.sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources-section';
                sourcesDiv.innerHTML = '<strong>Sources:</strong> ';
                
                msg.sources.forEach(source => {
                    const sourceSpan = document.createElement('span');
                    sourceSpan.className = 'source-item';
                    sourceSpan.textContent = source.filename || source;
                    sourcesDiv.appendChild(sourceSpan);
                });
                
                messageDiv.appendChild(sourcesDiv);
            }
        }
        
        chatContainer.appendChild(messageDiv);
    });
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Authentication functions
function isAuthenticated() {
    return localStorage.getItem('metisToken') !== null;
}

function getToken() {
    // Try localStorage first, then sessionStorage as fallback
    return localStorage.getItem('metisToken') || sessionStorage.getItem('metisToken') || '';
}

// Check if token is expired or about to expire
function isTokenExpired() {
    const token = getToken();
    if (!token) return true;
    
    try {
        // Parse the JWT payload
        const payload = JSON.parse(atob(token.split('.')[1]));
        
        // Get expiration time in milliseconds
        const expirationTime = payload.exp * 1000;
        
        // Get current time
        const currentTime = Date.now();
        
        // Check if token is expired or will expire in the next 5 minutes
        return expirationTime < (currentTime + 5 * 60 * 1000);
    } catch (e) {
        console.error('Error checking token expiration:', e);
        return true; // Assume expired if we can't parse the token
    }
}

// Refresh the token
async function refreshToken() {
    console.log('Attempting to refresh token...');
    
    // Get the refresh token
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        console.error('No refresh token available');
        return false;
    }
    
    try {
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                refresh_token: refreshToken
            })
        });
        
        if (!response.ok) {
            console.error('Token refresh failed:', response.status);
            return false;
        }
        
        const data = await response.json();
        
        // Store the new tokens in both localStorage and sessionStorage
        localStorage.setItem('metisToken', data.access_token);
        sessionStorage.setItem('metisToken', data.access_token);
        
        if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token);
            sessionStorage.setItem('refresh_token', data.refresh_token);
        }
        
        // Also update the cookie for server-side authentication
        const expirationDate = new Date();
        expirationDate.setDate(expirationDate.getDate() + 7); // 7 days expiration
        document.cookie = `auth_token=${data.access_token}; path=/; expires=${expirationDate.toUTCString()}; SameSite=Strict`;
        
        console.log('Token refreshed successfully');
        return true;
    } catch (e) {
        console.error('Error refreshing token:', e);
        return false;
    }
}

// Authenticated fetch function with token refresh
async function authenticatedFetch(url, options = {}) {
    // Clone the options to avoid modifying the original
    const fetchOptions = { ...options };
    
    // Add headers if not present
    if (!fetchOptions.headers) {
        fetchOptions.headers = {};
    }
    
    // Check if token is expired and refresh if needed
    if (isAuthenticated() && isTokenExpired()) {
        console.log('Token is expired or about to expire, refreshing...');
        const refreshed = await refreshToken();
        if (!refreshed) {
            // If refresh failed, redirect to login
            console.warn('Token refresh failed, redirecting to login');
            logout();
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
            throw new Error('Authentication expired');
        }
    }
    
    // Add authorization header if authenticated
    if (isAuthenticated()) {
        fetchOptions.headers['Authorization'] = `Bearer ${getToken()}`;
    }
    
    // Make the request
    const response = await fetch(url, fetchOptions);
    
    // Handle 401 Unauthorized errors
    if (response.status === 401) {
        console.log('Received 401 Unauthorized, attempting token refresh');
        
        // Try to refresh the token
        const refreshed = await refreshToken();
        if (refreshed) {
            // If refresh succeeded, retry the request with the new token
            console.log('Token refreshed, retrying request');
            fetchOptions.headers['Authorization'] = `Bearer ${getToken()}`;
            return fetch(url, fetchOptions);
        } else {
            // If refresh failed, redirect to login
            console.warn('Token refresh failed after 401, redirecting to login');
            logout();
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
            throw new Error('Authentication expired');
        }
    }
    
    return response;
}

// Make authentication functions globally available
window.isAuthenticated = isAuthenticated;
window.getToken = getToken;
window.authenticatedFetch = authenticatedFetch;
console.log('Auth functions made global');

function logout() {
    // Clear localStorage
    localStorage.removeItem('metisToken');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('username');
    
    // Clear sessionStorage
    sessionStorage.removeItem('metisToken');
    sessionStorage.removeItem('refresh_token');
    
    // Clear auth cookie
    document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict';
    updateAuthUI();
    
    // Redirect to login page if on a protected page
    const protectedPages = ['/documents', '/chat', '/analytics', '/system'];
    const currentPath = window.location.pathname;
    if (protectedPages.includes(currentPath)) {
        window.location.href = '/login';
    } else {
        showNotification('Logged out successfully');
    }
}

function getCurrentUser() {
    if (!isAuthenticated()) {
        return null;
    }
    
    return fetch('/api/auth/me', {
        headers: {
            'Authorization': `Bearer ${getToken()}`
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Failed to get user info');
    })
    .catch(error => {
        console.error('Error getting current user:', error);
        // If we can't get the user info, the token might be invalid
        logout();
        return null;
    });
}

function updateAuthUI() {
    const loginButton = document.getElementById('login-button');
    const logoutButton = document.getElementById('logout-button');
    const usernameDisplay = document.getElementById('username-display');
    
    if (!loginButton || !logoutButton || !usernameDisplay) {
        return;
    }
    
    if (isAuthenticated()) {
        loginButton.style.display = 'none';
        logoutButton.style.display = 'inline-block';
        
        // Display username if available
        const username = localStorage.getItem('username');
        if (username) {
            usernameDisplay.textContent = username;
        } else {
            // Try to get username from API
            getCurrentUser().then(user => {
                if (user) {
                    localStorage.setItem('username', user.username);
                    usernameDisplay.textContent = user.username;
                }
            });
        }
    } else {
        loginButton.style.display = 'inline-block';
        logoutButton.style.display = 'none';
        usernameDisplay.textContent = '';
    }
}

function setupAuthListeners() {
    const loginButton = document.getElementById('login-button');
    const logoutButton = document.getElementById('logout-button');
    
    if (loginButton) {
        loginButton.addEventListener('click', () => {
            window.location.href = '/login';
        });
    }
    
    if (logoutButton) {
        logoutButton.addEventListener('click', logout);
    }
}

// Check token expiration periodically
function setupTokenRefreshCheck() {
    // Check token every 5 minutes
    setInterval(() => {
        if (isAuthenticated() && isTokenExpired()) {
            console.log('Periodic token check: Token is expired or about to expire');
            refreshToken().then(refreshed => {
                if (!refreshed) {
                    console.warn('Periodic token refresh failed');
                    showNotification('Your session is about to expire. Please log in again.', 'warning');
                } else {
                    console.log('Periodic token refresh succeeded');
                }
            });
        }
        
        // Also check for server restarts
        checkServerStatus();
    }, 5 * 60 * 1000); // Check every 5 minutes
    
    // Immediate server status check on page load
    checkServerStatus();
}

/**
 * Check if the server has restarted and handle auth token synchronization
 */
function checkServerStatus() {
    // Store a random session ID for server restart detection
    if (!sessionStorage.getItem('server_session_id')) {
        sessionStorage.setItem('server_session_id', Math.random().toString(36).substring(2));
    }
    
    const sessionId = sessionStorage.getItem('server_session_id');
    
    // Simple health check
    fetch('/api/health/', {
        headers: {
            'X-Client-Session': sessionId
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Health check failed');
    })
    .then(data => {
        // If server reports different session than what we've seen before
        if (data.server_start_time && sessionStorage.getItem('server_start_time') &&
            sessionStorage.getItem('server_start_time') !== data.server_start_time) {
            console.log('Server restart detected, synchronizing tokens');
            
            // Server has restarted, attempt to refresh token or force re-login
            if (isAuthenticated()) {
                refreshToken()
                    .then(success => {
                        if (success) {
                            console.log('Token refreshed after server restart');
                            // Also sync cookie to ensure consistency
                            const token = localStorage.getItem('metisToken');
                            if (token) {
                                const expirationDate = new Date();
                                expirationDate.setDate(expirationDate.getDate() + 7); // 7 days expiration
                                document.cookie = `auth_token=${token}; path=/; expires=${expirationDate.toUTCString()}; SameSite=Strict`;
                            }
                        } else {
                            // Force logout if refresh fails
                            logout();
                            showNotification('Your session expired due to server restart. Please log in again.', 'warning');
                            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}&reason=server_restart`;
                        }
                    })
                    .catch(() => {
                        // Force logout if refresh fails with error
                        logout();
                        showNotification('Your session expired due to server restart. Please log in again.', 'warning');
                        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}&reason=server_restart`;
                    });
            }
        }
        
        // Store server start time for future comparisons
        if (data.server_start_time) {
            sessionStorage.setItem('server_start_time', data.server_start_time);
        }
    })
    .catch(error => {
        console.error('Server status check failed:', error);
    });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize conversation
    initConversation();
    
    // Set up authentication UI
    updateAuthUI();
    setupAuthListeners();
    
    // Set up token refresh check
    setupTokenRefreshCheck();
    
    // DevOps panel is now directly included in chat.html
    const currentPath = window.location.pathname;
    
    // Check if we need to redirect to login
    const protectedPages = ['/documents', '/chat', '/analytics', '/system'];
    if (protectedPages.includes(currentPath) && !isAuthenticated()) {
        window.location.href = '/login?redirect=' + encodeURIComponent(currentPath);
    }
    
    // Set up advanced options toggle if it exists
    const advancedToggle = document.getElementById('advanced-toggle');
    const advancedContent = document.getElementById('advanced-content');
    const advancedIcon = document.getElementById('advanced-icon');
    
    if (advancedToggle && advancedContent && advancedIcon) {
        // Show advanced options if they were previously shown
        if (localStorage.getItem('advancedOptions') === 'shown') {
            advancedContent.classList.add('show');
            advancedIcon.classList.replace('fa-chevron-down', 'fa-chevron-up');
        }
        
        advancedToggle.addEventListener('click', function() {
            advancedContent.classList.toggle('show');
            if (advancedContent.classList.contains('show')) {
                advancedIcon.classList.replace('fa-chevron-down', 'fa-chevron-up');
                localStorage.setItem('advancedOptions', 'shown');
            } else {
                advancedIcon.classList.replace('fa-chevron-up', 'fa-chevron-down');
                localStorage.setItem('advancedOptions', 'hidden');
            }
        });
    }
    
    // Set up DevOps panel toggle
    const devopsHeader = document.querySelector('.devops-header');
    const devopsContent = document.querySelector('.devops-content');
    
    if (devopsHeader && devopsContent) {
        // Add toggle indicator
        const toggleIcon = document.createElement('i');
        toggleIcon.className = 'fas fa-chevron-down toggle-icon';
        toggleIcon.style.marginLeft = '8px';
        toggleIcon.style.cursor = 'pointer';
        devopsHeader.querySelector('h3').appendChild(toggleIcon);
        
        // Set initial state based on preference
        const devopsPanelOpen = localStorage.getItem('metis_devops_panel_open') !== 'false';
        if (!devopsPanelOpen) {
            devopsContent.style.display = 'none';
            toggleIcon.className = 'fas fa-chevron-right toggle-icon';
        }
        
        // Add click handler
        devopsHeader.addEventListener('click', function() {
            const isVisible = devopsContent.style.display !== 'none';
            devopsContent.style.display = isVisible ? 'none' : 'flex';
            toggleIcon.className = isVisible 
                ? 'fas fa-chevron-right toggle-icon' 
                : 'fas fa-chevron-down toggle-icon';
            
            // Store preference
            localStorage.setItem('metis_devops_panel_open', isVisible ? 'false' : 'true');
        });
    }
    
    // Set up context window size change listener if it exists
    const numCtxElement = document.getElementById('num_ctx');
    if (numCtxElement) {
        numCtxElement.addEventListener('change', function() {
            conversation.metadata.maxTokens = parseInt(this.value) || 4096;
            updateTokenDisplay();
            saveToLocalStorage();
        });
    }
});