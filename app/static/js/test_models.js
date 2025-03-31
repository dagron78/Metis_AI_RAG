// This script will be loaded by the browser and will log any errors
console.log('Test script loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing test script');
    
    // Get elements
    const modelSelect = document.getElementById('test-model-select');
    const modelList = document.getElementById('model-list');
    
    if (modelSelect) {
        console.log('Found model select element');
    } else {
        console.error('Model select element not found');
    }
    
    if (modelList) {
        console.log('Found model list element');
    } else {
        console.error('Model list element not found');
    }
    
    // Try to fetch models
    authenticatedFetch('/api/system/models')
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(models => {
            console.log('Models fetched:', models);
            console.log('Number of models:', models.length);
            
            // Log each model
            models.forEach(model => {
                console.log('Model:', model.name);
            });
            
            // Update UI if elements exist
            if (modelSelect) {
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
            }
            
            if (modelList) {
                // Clear the list
                modelList.innerHTML = '';
                
                // Add models to list
                models.forEach(model => {
                    const modelItem = document.createElement('div');
                    modelItem.className = 'model-item';
                    modelItem.textContent = model.name;
                    modelList.appendChild(modelItem);
                    console.log('Added model to list:', model.name);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching models:', error);
            
            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">Error loading models</option>';
            }
            
            if (modelList) {
                modelList.innerHTML = '<div>Error loading models: ' + error.message + '</div>';
            }
        });
});