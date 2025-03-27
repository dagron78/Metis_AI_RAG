// Enable debug mode for troubleshooting
const debugMode = true;

function debugLog(message) {
    if (debugMode) {
        const debugInfo = document.getElementById('debug-info');
        if (debugInfo) {
            debugInfo.style.display = 'block';
            debugInfo.innerHTML += message + '<br>';
        }
        console.log(message);
    }
}

// Check for credentials in URL and clean them up
function checkAndCleanCredentialsInUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const hasUsername = urlParams.has('username');
    const hasPassword = urlParams.has('password');
    
    if (hasUsername || hasPassword) {
        // Show warning
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.textContent = 'WARNING: Credentials should never be included in URLs as this is a security risk. The URL has been cleaned.';
            errorMessage.style.display = 'block';
        }
        
        // Save redirect parameter if present
        const redirect = urlParams.get('redirect');
        
        // Clean the URL (keep only redirect parameter if it exists)
        const cleanUrl = redirect
            ? `/login?redirect=${encodeURIComponent(redirect)}`
            : '/login';
        
        // Replace current URL without reloading
        window.history.replaceState({}, document.title, cleanUrl);
        
        debugLog('Credentials detected in URL and cleaned');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    debugLog('Page loaded');
    
    // Check for credentials in URL
    checkAndCleanCredentialsInUrl();
    
    const urlParams = new URLSearchParams(window.location.search);
    
    // Check if there's a registered parameter
    const registered = urlParams.get('registered');
    if (registered === 'true') {
        const successMessage = document.getElementById('success-message');
        if (successMessage) {
            successMessage.textContent = 'Registration successful! Please log in.';
            successMessage.style.display = 'block';
        }
        
        // Clean up the URL
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }
    
    // Check if there's a security warning
    const securityWarning = urlParams.get('security_warning');
    if (securityWarning === 'credentials_in_url') {
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.textContent = 'WARNING: Credentials should never be included in URLs as this is a security risk.';
            errorMessage.style.display = 'block';
        }
        
        // Clean up the URL
        const redirect = urlParams.get('redirect');
        const cleanUrl = redirect
            ? `/login?redirect=${encodeURIComponent(redirect)}`
            : '/login';
        window.history.replaceState({}, document.title, cleanUrl);
    }
    
    // Set up login form submission handler
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // Prevent the default form submission
            debugLog('Form submitted');
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                debugLog('Sending login request');
                // Always use the API endpoint directly
                const response = await fetch('/api/auth/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
                });
                
                debugLog(`Response status: ${response.status}`);
                const data = await response.json();
                debugLog(`Response data: ${JSON.stringify(data)}`);
                
                if (response.ok) {
                    // Store token and username in localStorage
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('token_type', data.token_type);
                    localStorage.setItem('username', username);
                    
                    // Show success message
                    const successMessage = document.getElementById('success-message');
                    if (successMessage) {
                        successMessage.textContent = 'Login successful! Redirecting...';
                        successMessage.style.display = 'block';
                    }
                    
                    const errorMessage = document.getElementById('error-message');
                    if (errorMessage) {
                        errorMessage.textContent = '';
                    }
                    
                    // Check for redirect parameter
                    const urlParams = new URLSearchParams(window.location.search);
                    const redirect = urlParams.get('redirect');
                    
                    // Log the redirect
                    debugLog(`Redirecting to: ${redirect || '/'}`);
                    
                    // Redirect to the specified page or home page after a short delay
                    setTimeout(() => {
                        window.location.href = redirect || '/';
                    }, 1000);
                } else {
                    // Display error message
                    const errorMessage = document.getElementById('error-message');
                    if (errorMessage) {
                        errorMessage.textContent = data.detail || 'Login failed';
                        errorMessage.style.display = 'block';
                    }
                    
                    const successMessage = document.getElementById('success-message');
                    if (successMessage) {
                        successMessage.style.display = 'none';
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                debugLog(`Error: ${error.message}`);
                
                const errorMessage = document.getElementById('error-message');
                if (errorMessage) {
                    errorMessage.textContent = 'An error occurred during login';
                    errorMessage.style.display = 'block';
                }
                
                const successMessage = document.getElementById('success-message');
                if (successMessage) {
                    successMessage.style.display = 'none';
                }
            }
        });
    }
});