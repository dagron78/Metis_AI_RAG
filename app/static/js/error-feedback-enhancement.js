/**
 * Error Feedback Enhancement - Improves error handling and user feedback
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Error feedback enhancement script loaded");
    
    // Enhanced notification function with support for HTML content
    window.showDetailedNotification = function(message, details = null, type = 'info') {
        // Use existing notification function if available
        if (typeof showNotification === 'function') {
            if (details) {
                // Create a more detailed notification
                const notificationContent = document.createElement('div');
                
                // Add main message
                const messageEl = document.createElement('div');
                messageEl.className = 'notification-message';
                messageEl.textContent = message;
                notificationContent.appendChild(messageEl);
                
                // Add details in collapsible section
                const detailsEl = document.createElement('div');
                detailsEl.className = 'notification-details';
                
                if (Array.isArray(details)) {
                    // Handle array of error details (multiple files)
                    const list = document.createElement('ul');
                    list.className = 'error-list';
                    
                    details.forEach(item => {
                        const listItem = document.createElement('li');
                        listItem.textContent = `${item.filename}: ${item.error}`;
                        list.appendChild(listItem);
                    });
                    
                    detailsEl.appendChild(list);
                } else {
                    // Handle string details
                    detailsEl.textContent = details;
                }
                
                notificationContent.appendChild(detailsEl);
                
                // Convert to string for the notification function
                const notificationHTML = notificationContent.outerHTML;
                
                // Create a temporary div to hold the HTML
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = notificationHTML;
                
                // Call the original notification function with the HTML content
                const notificationElement = showNotification(message, type);
                
                // Replace the text content with our HTML
                if (notificationElement) {
                    notificationElement.innerHTML = '';
                    notificationElement.appendChild(tempDiv.firstChild);
                    
                    // Add close button
                    const closeBtn = document.createElement('span');
                    closeBtn.innerHTML = '&times;';
                    closeBtn.style.marginLeft = '10px';
                    closeBtn.style.cursor = 'pointer';
                    closeBtn.style.fontWeight = 'bold';
                    closeBtn.onclick = function() {
                        document.body.removeChild(notificationElement);
                    };
                    notificationElement.appendChild(closeBtn);
                }
                
                return notificationElement;
            } else {
                // Just use the standard notification for simple messages
                return showNotification(message, type);
            }
        } else {
            console.error("Base showNotification function not available");
            alert(`${message} ${details ? '\n\n' + JSON.stringify(details) : ''}`);
        }
    };
    
    // Enhance the DocumentManager to use better error handling
    // Wait for DocumentManager to be fully loaded
    setTimeout(function() {
        if (typeof DocumentManager !== 'undefined') {
            try {
                // Store original methods
                const originalUploadMultipleFiles = DocumentManager.prototype.uploadMultipleFiles;
                const originalUploadNextFile = DocumentManager.prototype.uploadNextFile;
                
                // Enhance uploadMultipleFiles method
                if (originalUploadMultipleFiles) {
                    DocumentManager.prototype.uploadMultipleFiles = function() {
                        // Call original method
                        originalUploadMultipleFiles.apply(this, arguments);
                        
                        // Enhance XHR error handling
                        const xhr = this.xhr;
                        if (xhr) {
                            const originalOnload = xhr.onload;
                            xhr.onload = function() {
                                if (xhr.status === 200) {
                                    const response = JSON.parse(xhr.responseText);
                                    
                                    if (!response.success && response.errors && response.errors.length > 0) {
                                        // Show detailed error notification
                                        showDetailedNotification(
                                            `Error uploading ${response.errors.length} document(s)`,
                                            response.errors,
                                            'warning'
                                        );
                                    }
                                }
                                
                                // Call original handler
                                if (originalOnload) {
                                    originalOnload.apply(this, arguments);
                                }
                            };
                        }
                    };
                    console.log("Enhanced uploadMultipleFiles method");
                }
                
                // Enhance uploadNextFile method
                if (originalUploadNextFile) {
                    DocumentManager.prototype.uploadNextFile = function() {
                        // Call original method
                        originalUploadNextFile.apply(this, arguments);
                        
                        // Enhance XHR error handling
                        const xhr = this.xhr;
                        if (xhr) {
                            const originalOnload = xhr.onload;
                            xhr.onload = function() {
                                if (xhr.status === 200) {
                                    const response = JSON.parse(xhr.responseText);
                                    
                                    if (!response.success && response.message) {
                                        // Show detailed error notification
                                        showDetailedNotification(
                                            `Error uploading document`,
                                            response.message,
                                            'warning'
                                        );
                                    }
                                }
                                
                                // Call original handler
                                if (originalOnload) {
                                    originalOnload.apply(this, arguments);
                                }
                            };
                        }
                    };
                    console.log("Enhanced uploadNextFile method");
                }
            } catch (error) {
                console.error("Error enhancing DocumentManager:", error);
            }
        } else {
            console.error("DocumentManager not defined for error enhancement");
        }
    }, 1000); // Wait 1 second to ensure DocumentManager is fully loaded
    
    // Add CSS for enhanced notifications
    const style = document.createElement('style');
    style.textContent = `
        .notification-message {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .notification-details {
            font-size: 0.9em;
            max-height: 100px;
            overflow-y: auto;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
            padding-top: 5px;
            margin-top: 5px;
        }
        
        .error-list {
            margin: 0;
            padding-left: 20px;
        }
        
        .error-list li {
            margin-bottom: 3px;
        }
    `;
    document.head.appendChild(style);
});