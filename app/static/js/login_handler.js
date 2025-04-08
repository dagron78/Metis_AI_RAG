// Debug mode should be disabled in production
const debugMode = false;

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
        // Login form submission is handled by login.js
    }
});