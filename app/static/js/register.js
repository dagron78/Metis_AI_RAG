document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('register-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const fullName = document.getElementById('full_name').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        
        // Validate passwords match
        if (password !== confirmPassword) {
            document.getElementById('error-message').textContent = 'Passwords do not match';
            return;
        }
        
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    full_name: fullName,
                    password: password,
                    is_active: true,
                    is_admin: false
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Redirect to login page
                window.location.href = '/login?registered=true';
            } else {
                // Display error message
                document.getElementById('error-message').textContent = data.detail || 'Registration failed';
            }
        } catch (error) {
            console.error('Error:', error);
            document.getElementById('error-message').textContent = 'An error occurred during registration';
        }
    });
});