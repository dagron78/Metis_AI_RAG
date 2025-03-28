/**
 * Document Upload Fix - Ensures multiple file selection works properly
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Document upload fix script loaded");
    
    // Get the file input element
    const fileInput = document.getElementById('document-file');
    
    if (fileInput) {
        console.log("File input found:", fileInput);
        console.log("Multiple attribute:", fileInput.multiple);
        
        // Ensure multiple attribute is set
        fileInput.setAttribute('multiple', 'multiple');
        console.log("Multiple attribute after fix:", fileInput.multiple);
        
        // Add a direct event listener to log file selection
        fileInput.addEventListener('change', function(e) {
            const files = e.target.files;
            console.log(`Files selected: ${files ? files.length : 0}`);
            
            if (files && files.length > 0) {
                console.log("Selected files:");
                for (let i = 0; i < files.length; i++) {
                    console.log(`- ${files[i].name} (${files[i].size} bytes)`);
                }
            }
        });
        
        // Check if the file input is inside a form
        const form = fileInput.closest('form');
        if (form) {
            console.log("Form found:", form);
            
            // Add submit event listener to log form submission
            form.addEventListener('submit', function(e) {
                console.log("Form submitted");
                const files = fileInput.files;
                console.log(`Files in form submission: ${files ? files.length : 0}`);
            });
        }
    } else {
        console.error("File input element not found");
    }
    
    // Check browser compatibility
    const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
    const isFirefox = /Firefox/.test(navigator.userAgent);
    const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
    const isEdge = /Edg/.test(navigator.userAgent);
    
    console.log("Browser detection:", {
        isChrome,
        isFirefox,
        isSafari,
        isEdge
    });
    
    // Check if the browser supports multiple file selection
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    console.log("Browser supports multiple attribute:", input.multiple);
});

// Fix for the DocumentManager class - wait for it to be defined
document.addEventListener('DOMContentLoaded', function() {
    // Wait a short time to ensure DocumentManager is loaded
    setTimeout(function() {
        if (typeof DocumentManager !== 'undefined') {
            try {
                const originalInitialize = DocumentManager.prototype.initialize;
                
                if (originalInitialize) {
                    DocumentManager.prototype.initialize = function() {
                        // Call the original initialize method
                        originalInitialize.apply(this, arguments);
                        
                        // Add our fixes after initialization
                        if (this.documentFile) {
                            console.log("Fixing document file input in DocumentManager");
                            
                            // Ensure multiple attribute is set
                            this.documentFile.setAttribute('multiple', 'multiple');
                            
                            // Replace the event listener to ensure it works
                            this.documentFile.removeEventListener('change', this.handleFileSelection);
                            this.documentFile.addEventListener('change', (e) => {
                                console.log("File selection event triggered");
                                this.handleFileSelection(e);
                            });
                        }
                    };
                    console.log("DocumentManager.initialize successfully patched");
                } else {
                    console.error("DocumentManager.prototype.initialize not found");
                }
            } catch (error) {
                console.error("Error patching DocumentManager:", error);
            }
        } else {
            console.error("DocumentManager not defined");
        }
    }, 500); // Wait 500ms to ensure DocumentManager is loaded
});