document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('login-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('/api/auth/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Store token and username in localStorage
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('token_type', data.token_type);
                localStorage.setItem('username', username);
                
                // Set auth token as a cookie for server-side authentication
                const expirationDate = new Date();
                expirationDate.setDate(expirationDate.getDate() + 7); // 7 days expiration
                document.cookie = `auth_token=${data.access_token}; path=/; expires=${expirationDate.toUTCString()}; SameSite=Strict`;
                
                // Check for redirect parameter
                const urlParams = new URLSearchParams(window.location.search);
                const redirect = urlParams.get('redirect');
                
                // Redirect to the specified page or home page
                window.location.href = redirect || '/';
            } else {
                // Display error message
                document.getElementById('error-message').textContent = data.detail || 'Login failed';
            }
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('error-message').textContent = 'An error occurred during login';
        }
    });
});