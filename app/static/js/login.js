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
                // Store token and username in localStorage and sessionStorage
                localStorage.setItem('metisToken', data.access_token);
                sessionStorage.setItem('metisToken', data.access_token);
                localStorage.setItem('token_type', data.token_type);
                localStorage.setItem('username', username);
                
                // Store refresh token if provided
                if (data.refresh_token) {
                    localStorage.setItem('refresh_token', data.refresh_token);
                    sessionStorage.setItem('refresh_token', data.refresh_token);
                }
                
                // Set auth token as a cookie for server-side authentication
                const expirationDate = new Date();
                expirationDate.setDate(expirationDate.getDate() + 7); // 7 days expiration
                document.cookie = `auth_token=${data.access_token}; path=/; expires=${expirationDate.toUTCString()}; SameSite=Strict`;
                
                // Check server status to get server start time
                fetch('/api/health/')
                    .then(response => response.json())
                    .then(healthData => {
                        if (healthData.server_start_time) {
                            sessionStorage.setItem('server_start_time', healthData.server_start_time);
                            console.log('Server start time recorded:', healthData.server_start_time);
                        }
                    })
                    .catch(error => console.error('Failed to get server health info:', error));
                
                // Check for redirect parameter
                const urlParams = new URLSearchParams(window.location.search);
                const redirect = urlParams.get('redirect');
                
                // Redirect to the specified page or home page
                // Add a short delay before redirecting to allow storage to settle
                setTimeout(() => {
                    window.location.href = redirect || '/';
                }, 100); // 100ms delay
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