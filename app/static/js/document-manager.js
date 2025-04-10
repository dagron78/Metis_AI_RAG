// Document Management Functionality
class DocumentManager {
    constructor() {
        this.documents = [];
        this.selectedDocuments = [];
        this.isExpanded = false;
        this.isUploading = false;
        this.allTags = [];
        this.allFolders = ['/'];
        this.activeFilters = {
            tags: [],
            folder: null
        };
        
        // Initialize elements after DOM is loaded
        document.addEventListener('DOMContentLoaded', () => this.initialize());
    }
    
    initialize() {
        // Get elements
        this.docSection = document.getElementById('document-section');
        this.docList = document.getElementById('document-list');
        this.uploadForm = document.getElementById('upload-form');
        this.documentFile = document.getElementById('document-file');
        this.dropZone = document.getElementById('drop-zone');
        this.fileList = document.getElementById('file-list');
        this.fileProgressList = document.getElementById('file-progress-list');
        this.overallProgress = document.getElementById('overall-progress');
        this.overallProgressFill = document.getElementById('overall-progress-fill');
        this.toggleBtn = document.getElementById('toggle-documents');
        this.processSelectedBtn = document.getElementById('process-selected-btn');
        this.deleteSelectedBtn = document.getElementById('delete-selected-btn');
        this.clearAllBtn = document.getElementById('clear-all-btn');
        
        // Debug log to check if the clear all button is found
        console.log("Clear All Button:", this.clearAllBtn);
        this.documentCount = document.getElementById('document-count');
        this.tagInput = document.getElementById('doc-tags');
        this.folderSelect = document.getElementById('doc-folder');
        this.filterPanel = document.getElementById('filter-panel');
        this.editModal = document.getElementById('document-edit-modal');
        
        // File queue for uploads
        this.fileQueue = [];
        
        // Mobile detection
        this.isMobile = window.innerWidth <= 768;
        
        if (!this.docSection) return;
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load tags and folders
        this.loadTagsAndFolders();
        
        // Load documents
        this.loadDocuments();
        
        // Set up mobile-specific features
        if (this.isMobile) {
            this.setupMobileSupport();
        }
        
        // Listen for window resize to adjust mobile features
        window.addEventListener('resize', () => {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 768;
            
            // If switching between mobile and desktop
            if (wasMobile !== this.isMobile) {
                if (this.isMobile) {
                    this.setupMobileSupport();
                } else {
                    this.removeMobileSupport();
                }
            }
        });
    }
    
    setupEventListeners() {
        // Toggle document section
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggleDocumentSection());
        }
        
        // Upload form
        if (this.uploadForm) {
            this.uploadForm.addEventListener('submit', (e) => this.handleUpload(e));
        }
        
        // File input change
        if (this.documentFile) {
            this.documentFile.addEventListener('change', (e) => this.handleFileSelection(e));
        }
        
        // Drag and drop functionality
        if (this.dropZone) {
            this.dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.add('active');
            });
            
            this.dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.remove('active');
            });
            
            this.dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.remove('active');
                
                if (e.dataTransfer.files.length > 0) {
                    this.handleFileSelection({ target: { files: e.dataTransfer.files } });
                }
            });
        }
        
        // Process selected documents
        if (this.processSelectedBtn) {
            this.processSelectedBtn.addEventListener('click', () => this.processSelected());
        }
        
        // Delete selected documents
        if (this.deleteSelectedBtn) {
            this.deleteSelectedBtn.addEventListener('click', () => this.deleteSelected());
        }
        
        // Clear all documents (admin only)
        if (this.clearAllBtn) {
            this.clearAllBtn.addEventListener('click', () => this.clearAllDocuments());
        }
        
        // Filter toggle
        const filterToggle = document.getElementById('filter-toggle');
        if (filterToggle) {
            filterToggle.addEventListener('click', () => {
                const filterContent = document.getElementById('filter-content');
                filterContent.classList.toggle('show');
                const icon = filterToggle.querySelector('i');
                if (icon) {
                    icon.className = filterContent.classList.contains('show') ?
                        'fas fa-chevron-up' : 'fas fa-chevron-down';
                }
            });
        }
        
        // Apply filters button
        const applyFiltersBtn = document.getElementById('apply-filters');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        }
        
        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }
        
        // Modal close button
        const modalClose = document.querySelector('.modal-close');
        if (modalClose) {
            modalClose.addEventListener('click', () => {
                if (this.editModal) {
                    this.editModal.style.display = 'none';
                }
            });
        }
        
        // Save changes button in modal
        const saveChangesBtn = document.getElementById('save-changes');
        if (saveChangesBtn) {
            saveChangesBtn.addEventListener('click', () => this.saveDocumentChanges());
        }
        
        // Tag input for suggestions
        if (this.tagInput) {
            this.tagInput.addEventListener('input', () => this.showTagSuggestions());
            this.tagInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && this.tagInput.value.trim()) {
                    e.preventDefault();
                    this.addTag(this.tagInput.value.trim());
                    this.tagInput.value = '';
                }
            });
        }
    }
    
    loadTagsAndFolders() {
        // Load all tags
        authenticatedFetch('/api/documents/tags')
            .then(response => response.json())
            .then(data => {
                this.allTags = data.tags || [];
                this.renderTagFilters();
            })
            .catch(error => {
                console.error('Error loading tags:', error);
            });
        
        // Load all folders
        authenticatedFetch('/api/documents/folders')
            .then(response => response.json())
            .then(data => {
                this.allFolders = data.folders || ['/'];
                this.renderFolderFilters();
                this.populateFolderSelect();
            })
            .catch(error => {
                console.error('Error loading folders:', error);
            });
    }
    
    renderTagFilters() {
        const filterTagsContainer = document.getElementById('filter-tags');
        if (!filterTagsContainer || !this.allTags.length) return;
        
        filterTagsContainer.innerHTML = '';
        
        this.allTags.forEach(tag => {
            const tagEl = document.createElement('div');
            tagEl.className = 'filter-tag';
            tagEl.textContent = tag;
            tagEl.dataset.tag = tag;
            
            if (this.activeFilters.tags.includes(tag)) {
                tagEl.classList.add('active');
            }
            
            tagEl.addEventListener('click', () => {
                tagEl.classList.toggle('active');
            });
            
            filterTagsContainer.appendChild(tagEl);
        });
    }
    
    renderFolderFilters() {
        const filterFoldersContainer = document.getElementById('filter-folders');
        if (!filterFoldersContainer || !this.allFolders.length) return;
        
        filterFoldersContainer.innerHTML = '';
        
        this.allFolders.forEach(folder => {
            const folderEl = document.createElement('div');
            folderEl.className = 'filter-folder';
            folderEl.textContent = folder === '/' ? 'Root' : folder.replace('/', '');
            folderEl.dataset.folder = folder;
            
            if (this.activeFilters.folder === folder) {
                folderEl.classList.add('active');
            }
            
            folderEl.addEventListener('click', () => {
                // Deactivate all folders
                document.querySelectorAll('.filter-folder').forEach(el => {
                    el.classList.remove('active');
                });
                
                // Activate this folder
                folderEl.classList.add('active');
            });
            
            filterFoldersContainer.appendChild(folderEl);
        });
    }
    
    populateFolderSelect() {
        if (!this.folderSelect || !this.allFolders.length) return;
        
        this.folderSelect.innerHTML = '';
        
        this.allFolders.forEach(folder => {
            const option = document.createElement('option');
            option.value = folder;
            option.textContent = folder === '/' ? 'Root' : folder.replace('/', '');
            this.folderSelect.appendChild(option);
        });
    }
    
    applyFilters() {
        // Get selected tags
        const selectedTags = Array.from(document.querySelectorAll('.filter-tag.active'))
            .map(el => el.dataset.tag);
        
        // Get selected folder
        const selectedFolder = document.querySelector('.filter-folder.active')?.dataset.folder;
        
        this.activeFilters = {
            tags: selectedTags,
            folder: selectedFolder
        };
        
        // Load filtered documents
        this.loadFilteredDocuments();
        
        // Close filter panel
        const filterContent = document.getElementById('filter-content');
        if (filterContent) {
            filterContent.classList.remove('show');
        }
        
        const filterToggle = document.getElementById('filter-toggle');
        if (filterToggle) {
            const icon = filterToggle.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-chevron-down';
            }
        }
    }
    
    clearFilters() {
        // Clear active filters
        document.querySelectorAll('.filter-tag.active, .filter-folder.active').forEach(el => {
            el.classList.remove('active');
        });
        
        this.activeFilters = {
            tags: [],
            folder: null
        };
        
        // Load all documents
        this.loadDocuments();
    }
    
    loadFilteredDocuments() {
        if (!this.docList) return;
        
        // Show loading indicator
        this.docList.innerHTML = '<div class="document-loading">Loading documents...</div>';
        
        // Prepare filter request
        const filterRequest = {
            tags: this.activeFilters.tags.length > 0 ? this.activeFilters.tags : null,
            folder: this.activeFilters.folder
        };
        
        authenticatedFetch('/api/documents/filter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filterRequest)
        })
            .then(response => response.json())
            .then(documents => {
                this.documents = documents;
                this.renderDocuments();
            })
            .catch(error => {
                console.error('Error loading filtered documents:', error);
                this.docList.innerHTML = '<div class="document-error">Error loading documents</div>';
            });
    }
    
    toggleDocumentSection() {
        if (!this.docSection) return;
        
        this.isExpanded = !this.isExpanded;
        this.docSection.classList.toggle('expanded', this.isExpanded);
        
        // Update toggle button icon and text
        if (this.toggleBtn) {
            const icon = this.toggleBtn.querySelector('i');
            if (icon) {
                icon.className = this.isExpanded ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
            }
        }
        
        // Load documents if expanding and not already loaded
        if (this.isExpanded && this.documents.length === 0) {
            this.loadDocuments();
        }
    }
    
    loadDocuments() {
        if (!this.docList) return Promise.resolve();
        
        // Show loading indicator
        this.docList.innerHTML = '<div class="document-loading">Loading documents...</div>';
        
        // Return the promise for chaining
        return authenticatedFetch('/api/documents/list')
            .then(response => response.json())
            .then(documents => {
                this.documents = documents;
                this.renderDocuments();
                return documents;
            })
            .catch(error => {
                console.error('Error loading documents:', error);
                this.docList.innerHTML = '<div class="document-error">Error loading documents</div>';
                return [];
            });
    }
    
    renderDocuments() {
        if (!this.docList) return;
        
        this.docList.innerHTML = '';
        
        if (this.documents.length === 0) {
            this.docList.innerHTML = '<div class="document-empty">No documents found</div>';
            this.updateDocumentCount(0);
            return;
        }
        
        this.documents.forEach(doc => {
            const docEl = this.createDocumentElement(doc);
            this.docList.appendChild(docEl);
        });
        
        this.updateDocumentCount(this.documents.length);
        this.updateBatchButtons();
    }
    
    createDocumentElement(doc) {
        const docEl = document.createElement('div');
        docEl.className = 'sidebar-document-item';
        docEl.dataset.id = doc.id;
        
        const date = new Date(doc.uploaded);
        const formattedDate = date.toLocaleDateString();
        
        // Create tags HTML
        const tagsHtml = doc.tags && doc.tags.length > 0
            ? `<div class="doc-tags">${doc.tags.map(tag => `<span class="doc-tag">${tag}</span>`).join('')}</div>`
            : '';
        
        // Create folder HTML
        const folderHtml = doc.folder
            ? `<div class="doc-folder"><i class="fas fa-folder"></i> ${doc.folder === '/' ? 'Root' : doc.folder.replace('/', '')}</div>`
            : '';
        
        docEl.innerHTML = `
            <div class="doc-header">
                <label class="doc-select-label">
                    <input type="checkbox" class="doc-select" data-id="${doc.id}">
                    <span class="doc-title" title="${doc.filename}">${this.truncateFilename(doc.filename)}</span>
                </label>
            </div>
            ${tagsHtml}
            ${folderHtml}
            <div class="doc-meta">
                <span class="doc-chunks">${doc.chunk_count} chunks</span>
                <span class="doc-date">${formattedDate}</span>
            </div>
            <div class="doc-actions">
                <button class="doc-action edit-btn" data-id="${doc.id}" title="Edit Document">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="doc-action process-btn" data-id="${doc.id}" title="Process Document">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button class="doc-action delete-btn" data-id="${doc.id}" title="Delete Document">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            ${this.isMobile ? `
            <div class="swipe-actions">
                <button class="swipe-action delete-action" title="Delete Document">
                    <i class="fas fa-trash"></i>
                </button>
            </div>` : ''}
        `;
        
        // Add event listeners
        const checkbox = docEl.querySelector('.doc-select');
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                this.selectedDocuments.push(doc.id);
            } else {
                const index = this.selectedDocuments.indexOf(doc.id);
                if (index !== -1) {
                    this.selectedDocuments.splice(index, 1);
                }
            }
            this.updateBatchButtons();
        });
        
        const editBtn = docEl.querySelector('.edit-btn');
        editBtn.addEventListener('click', () => {
            this.openEditModal(doc);
        });
        
        const processBtn = docEl.querySelector('.process-btn');
        processBtn.addEventListener('click', () => {
            this.processDocuments([doc.id]);
        });
        
        const deleteBtn = docEl.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', () => {
            this.deleteDocument(doc.id);
        });
        
        return docEl;
    }
    
    openEditModal(doc) {
        if (!this.editModal) return;
        
        // Set document ID
        this.editModal.dataset.documentId = doc.id;
        
        // Set document title
        const modalTitle = this.editModal.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = `Edit: ${this.truncateFilename(doc.filename)}`;
        }
        
        // Clear existing tags
        const tagList = document.getElementById('edit-tag-list');
        if (tagList) {
            tagList.innerHTML = '';
            
            // Add current tags
            if (doc.tags && doc.tags.length > 0) {
                doc.tags.forEach(tag => {
                    const tagEl = document.createElement('div');
                    tagEl.className = 'tag-item';
                    tagEl.innerHTML = `
                        ${tag}
                        <span class="tag-remove" data-tag="${tag}">&times;</span>
                    `;
                    
                    const removeBtn = tagEl.querySelector('.tag-remove');
                    removeBtn.addEventListener('click', () => {
                        tagEl.remove();
                    });
                    
                    tagList.appendChild(tagEl);
                });
            }
        }
        
        // Set folder
        const folderSelect = document.getElementById('edit-folder');
        if (folderSelect) {
            // Populate folder options
            folderSelect.innerHTML = '';
            this.allFolders.forEach(folder => {
                const option = document.createElement('option');
                option.value = folder;
                option.textContent = folder === '/' ? 'Root' : folder.replace('/', '');
                option.selected = folder === doc.folder;
                folderSelect.appendChild(option);
            });
        }
        
        // Show modal
        this.editModal.style.display = 'flex';
        
        // Set up tag input
        const tagInput = document.getElementById('edit-tag-input');
        if (tagInput) {
            tagInput.value = '';
            tagInput.focus();
            
            // Remove existing event listeners
            const newTagInput = tagInput.cloneNode(true);
            tagInput.parentNode.replaceChild(newTagInput, tagInput);
            
            // Add event listeners
            newTagInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && newTagInput.value.trim()) {
                    e.preventDefault();
                    this.addTagToModal(newTagInput.value.trim());
                    newTagInput.value = '';
                }
            });
            
            // Tag suggestions
            newTagInput.addEventListener('input', () => {
                this.showTagSuggestionsInModal(newTagInput.value);
            });
        }
    }
    
    addTagToModal(tag) {
        const tagList = document.getElementById('edit-tag-list');
        if (!tagList) return;
        
        // Check if tag already exists
        const existingTags = Array.from(tagList.querySelectorAll('.tag-item'))
            .map(el => el.textContent.trim().replace('×', ''));
        
        if (existingTags.includes(tag)) return;
        
        // Add tag
        const tagEl = document.createElement('div');
        tagEl.className = 'tag-item';
        tagEl.innerHTML = `
            ${tag}
            <span class="tag-remove" data-tag="${tag}">&times;</span>
        `;
        
        const removeBtn = tagEl.querySelector('.tag-remove');
        removeBtn.addEventListener('click', () => {
            tagEl.remove();
        });
        
        tagList.appendChild(tagEl);
    }
    
    showTagSuggestionsInModal(input) {
        const suggestionsContainer = document.getElementById('tag-suggestions');
        if (!suggestionsContainer || !input) {
            if (suggestionsContainer) {
                suggestionsContainer.style.display = 'none';
            }
            return;
        }
        
        // Filter tags
        const matchingTags = this.allTags.filter(tag =>
            tag.toLowerCase().includes(input.toLowerCase()) &&
            !Array.from(document.getElementById('edit-tag-list').querySelectorAll('.tag-item'))
                .map(el => el.textContent.trim().replace('×', ''))
                .includes(tag)
        );
        
        if (matchingTags.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        // Render suggestions
        suggestionsContainer.innerHTML = '';
        matchingTags.forEach(tag => {
            const suggestionEl = document.createElement('div');
            suggestionEl.className = 'tag-suggestion-item';
            suggestionEl.textContent = tag;
            suggestionEl.addEventListener('click', () => {
                this.addTagToModal(tag);
                document.getElementById('edit-tag-input').value = '';
                suggestionsContainer.style.display = 'none';
            });
            
            suggestionsContainer.appendChild(suggestionEl);
        });
        
        suggestionsContainer.style.display = 'block';
    }
    
    saveDocumentChanges() {
        const documentId = this.editModal.dataset.documentId;
        if (!documentId) return;
        
        // Get tags
        const tags = Array.from(document.getElementById('edit-tag-list').querySelectorAll('.tag-item'))
            .map(el => el.textContent.trim().replace('×', ''));
        
        // Get folder
        const folder = document.getElementById('edit-folder').value;
        
        // Update tags
        this.updateDocumentTags(documentId, tags);
        
        // Update folder
        this.updateDocumentFolder(documentId, folder);
        
        // Close modal
        this.editModal.style.display = 'none';
    }
    
    updateDocumentTags(documentId, tags) {
        authenticatedFetch(`/api/documents/${documentId}/tags`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tags })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Tags updated successfully');
                this.loadDocuments();
                this.loadTagsAndFolders();
            } else {
                showNotification('Error updating tags: ' + data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error updating tags:', error);
            showNotification('Error updating tags', 'warning');
        });
    }
    
    updateDocumentFolder(documentId, folder) {
        authenticatedFetch(`/api/documents/${documentId}/folder`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ folder })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Folder updated successfully');
                this.loadDocuments();
                this.loadTagsAndFolders();
            } else {
                showNotification('Error updating folder: ' + data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error updating folder:', error);
            showNotification('Error updating folder', 'warning');
        });
    }
    
    truncateFilename(filename) {
        if (filename.length > 20) {
            return filename.substring(0, 17) + '...';
        }
        return filename;
    }
    
    handleFileSelection(e) {
        const files = Array.from(e.target.files || []);
        
        if (files.length === 0) return;
        
        // Add files to queue
        files.forEach(file => {
            // Check if file is already in queue
            const existingFile = this.fileQueue.find(f => f.name === file.name && f.size === file.size);
            if (!existingFile) {
                this.fileQueue.push(file);
            }
        });
        
        // Update file list display
        this.updateFileList();
    }
    
    updateFileList() {
        if (!this.fileList) return;
        
        this.fileList.innerHTML = '';
        
        if (this.fileQueue.length === 0) {
            this.fileList.style.display = 'none';
            return;
        }
        
        this.fileList.style.display = 'block';
        
        this.fileQueue.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileSize = this.formatFileSize(file.size);
            
            fileItem.innerHTML = `
                <div class="file-item-name">${file.name}</div>
                <div class="file-item-size">${fileSize}</div>
                <div class="file-item-remove" data-index="${index}">×</div>
            `;
            
            const removeBtn = fileItem.querySelector('.file-item-remove');
            removeBtn.addEventListener('click', () => {
                this.fileQueue.splice(index, 1);
                this.updateFileList();
            });
            
            this.fileList.appendChild(fileItem);
        });
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    createProgressElement(file) {
        const progressItem = document.createElement('div');
        progressItem.className = 'file-progress-item';
        progressItem.dataset.filename = file.name;
        
        progressItem.innerHTML = `
            <div class="file-progress-name">${this.truncateFilename(file.name)}</div>
            <div class="file-progress-bar">
                <div class="file-progress-fill" style="width: 0%"></div>
            </div>
        `;
        
        return progressItem;
    }
    
    updateFileProgress(filename, percent) {
        const progressItem = this.fileProgressList.querySelector(`.file-progress-item[data-filename="${filename}"]`);
        if (progressItem) {
            const progressFill = progressItem.querySelector('.file-progress-fill');
            if (progressFill) {
                progressFill.style.width = `${percent}%`;
            }
        }
    }
    
    updateOverallProgress(percent) {
        if (this.overallProgressFill) {
            this.overallProgressFill.style.width = `${percent}%`;
        }
    }
    
    handleUpload(e) {
        e.preventDefault();
        
        if (this.isUploading) return;
        
        if (this.fileQueue.length === 0) {
            showNotification('Please select files to upload', 'warning');
            return;
        }
        
        // Clear previous progress elements
        if (this.fileProgressList) {
            this.fileProgressList.innerHTML = '';
        }
        
        // Reset overall progress
        this.updateOverallProgress(0);
        
        // Create progress elements for each file
        this.fileQueue.forEach(file => {
            const progressElement = this.createProgressElement(file);
            this.fileProgressList.appendChild(progressElement);
        });
        
        this.isUploading = true;
        
        // Check if we should use the batch upload or individual uploads
        if (this.fileQueue.length > 1 && this.supportsMultipleFileUpload()) {
            this.uploadMultipleFiles();
        } else {
            this.uploadedCount = 0;
            this.successfulUploads = [];
            // Start uploading files one by one
            this.uploadNextFile();
        }
    }
    
    supportsMultipleFileUpload() {
        // Feature detection for multiple file upload support
        // This can be expanded to check for browser compatibility or server capabilities
        return true;
    }
    
    uploadMultipleFiles() {
        const formData = new FormData();
        
        // Add all files to FormData
        this.fileQueue.forEach(file => {
            formData.append('files', file);
        });
        
        // Add tags if provided
        if (this.tagInput && this.tagInput.value.trim()) {
            formData.append('tags', this.tagInput.value.trim());
        }
        
        // Add folder if provided
        if (this.folderSelect && this.folderSelect.value) {
            formData.append('folder', this.folderSelect.value);
        }
        
        // Upload files
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/documents/upload-multiple', true);
        
        // Add authorization header if authenticated
        if (isAuthenticated()) {
            xhr.setRequestHeader('Authorization', `Bearer ${getToken()}`);
        }
        
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                this.updateOverallProgress(percentComplete);
                
                // Update individual file progress based on overall progress
                // This is an approximation since we can't track individual files in a batch upload
                this.fileQueue.forEach(file => {
                    this.updateFileProgress(file.name, percentComplete);
                });
            }
        };
        
        xhr.onload = () => {
            this.isUploading = false;
            
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                
                if (response.success) {
                    // Update progress for successful uploads
                    if (response.documents && response.documents.length > 0) {
                        response.documents.forEach(doc => {
                            const file = this.fileQueue.find(f => f.name === doc.filename);
                            if (file) {
                                this.updateFileProgress(file.name, 100);
                            }
                        });
                        
                        // Process the documents
                        const documentIds = response.documents.map(doc => doc.document_id);
                        this.processDocuments(documentIds);
                    }
                    
                    // Show completion notification
                    const message = response.documents.length === 1
                        ? 'Document uploaded successfully!'
                        : `${response.documents.length} documents uploaded successfully!`;
                    showNotification(message);
                    
                    // Clear file queue and input
                    this.fileQueue = [];
                    if (this.documentFile) {
                        this.documentFile.value = '';
                    }
                    if (this.tagInput) {
                        this.tagInput.value = '';
                    }
                    this.updateFileList();
                    
                    // Reload documents and tags/folders
                    this.loadDocuments();
                    this.loadTagsAndFolders();
                } else {
                    showNotification('Error uploading documents: ' + response.message, 'warning');
                    
                    // Update progress for failed uploads
                    if (response.errors && response.errors.length > 0) {
                        response.errors.forEach(error => {
                            const file = this.fileQueue.find(f => f.name === error.filename);
                            if (file) {
                                this.updateFileProgress(file.name, 0);
                            }
                        });
                    }
                }
            } else {
                showNotification('Error uploading documents', 'warning');
                
                // Mark all as failed
                this.fileQueue.forEach(file => {
                    this.updateFileProgress(file.name, 0);
                });
            }
            
            // Hide progress after delay
            setTimeout(() => {
                if (this.fileProgressList) {
                    this.fileProgressList.innerHTML = '';
                }
                this.updateOverallProgress(0);
            }, 3000);
        };
        
        xhr.onerror = () => {
            this.isUploading = false;
            showNotification('Error uploading documents', 'warning');
            
            // Mark all as failed
            this.fileQueue.forEach(file => {
                this.updateFileProgress(file.name, 0);
            });
            
            // Hide progress after delay
            setTimeout(() => {
                if (this.fileProgressList) {
                    this.fileProgressList.innerHTML = '';
                }
                this.updateOverallProgress(0);
            }, 3000);
        };
        
        xhr.send(formData);
    }
    
    uploadNextFile() {
        if (this.uploadedCount >= this.fileQueue.length) {
            // All files uploaded
            this.handleUploadCompletion();
            return;
        }
        
        const file = this.fileQueue[this.uploadedCount];
        const formData = new FormData();
        formData.append('file', file);
        
        // Add tags if provided
        if (this.tagInput && this.tagInput.value.trim()) {
            formData.append('tags', this.tagInput.value.trim());
        }
        
        // Add folder if provided
        if (this.folderSelect && this.folderSelect.value) {
            formData.append('folder', this.folderSelect.value);
        }
        
        // Upload file
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/documents/upload', true);
        
        // Add authorization header if authenticated
        if (isAuthenticated()) {
            xhr.setRequestHeader('Authorization', `Bearer ${getToken()}`);
        }
        
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                this.updateFileProgress(file.name, percentComplete);
                
                // Update overall progress
                const overallPercent = ((this.uploadedCount + (e.loaded / e.total)) / this.fileQueue.length) * 100;
                this.updateOverallProgress(overallPercent);
            }
        };
        
        xhr.onload = () => {
            this.uploadedCount++;
            
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.success) {
                    this.updateFileProgress(file.name, 100);
                    this.successfulUploads.push(response.document_id);
                } else {
                    this.updateFileProgress(file.name, 0);
                    showNotification(`Error uploading ${file.name}: ${response.message}`, 'warning');
                }
            } else {
                this.updateFileProgress(file.name, 0);
                showNotification(`Error uploading ${file.name}`, 'warning');
            }
            
            // Upload next file
            this.uploadNextFile();
        };
        
        xhr.onerror = () => {
            this.uploadedCount++;
            this.updateFileProgress(file.name, 0);
            showNotification(`Error uploading ${file.name}`, 'warning');
            
            // Upload next file
            this.uploadNextFile();
        };
        
        xhr.send(formData);
    }
    
    handleUploadCompletion() {
        this.isUploading = false;
        
        // Show completion notification
        if (this.successfulUploads.length > 0) {
            const message = this.successfulUploads.length === 1
                ? 'Document uploaded successfully!'
                : `${this.successfulUploads.length} documents uploaded successfully!`;
            showNotification(message);
            
            // Process the documents
            this.processDocuments(this.successfulUploads);
            
            // Clear file queue and input
            this.fileQueue = [];
            if (this.documentFile) {
                this.documentFile.value = '';
            }
            if (this.tagInput) {
                this.tagInput.value = '';
            }
            this.updateFileList();
            
            // Reload documents and tags/folders
            this.loadDocuments();
            this.loadTagsAndFolders();
        } else {
            showNotification('No documents were uploaded successfully', 'warning');
        }
        
        // Update overall progress to complete
        this.updateOverallProgress(100);
        
        // Hide progress after delay
        setTimeout(() => {
            if (this.fileProgressList) {
                this.fileProgressList.innerHTML = '';
            }
            this.updateOverallProgress(0);
        }, 3000);
    }
    
    processDocuments(documentIds) {
        // Get chunking strategy options if available
        const chunkingStrategy = document.getElementById('chunking-strategy')?.value || 'recursive';
        const chunkSize = document.getElementById('chunk-size')?.value || null;
        const chunkOverlap = document.getElementById('chunk-overlap')?.value || null;
        
        const request = {
            document_ids: documentIds,
            force_reprocess: false,
            chunking_strategy: chunkingStrategy,
            chunk_size: chunkSize ? parseInt(chunkSize) : null,
            chunk_overlap: chunkOverlap ? parseInt(chunkOverlap) : null
        };
        
        // Log the processing request
        console.log('Processing documents with options:', request);
        
        authenticatedFetch('/api/documents/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`Processing started for ${documentIds.length} document(s) with ${chunkingStrategy} chunking strategy`);
            } else {
                showNotification('Error processing documents: ' + data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error processing documents:', error);
            showNotification('Error processing documents', 'warning');
        });
    }
    
    deleteDocument(documentId) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }
        
        authenticatedFetch(`/api/documents/${documentId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Document deleted successfully');
                
                // Remove from selected documents
                const index = this.selectedDocuments.indexOf(documentId);
                if (index !== -1) {
                    this.selectedDocuments.splice(index, 1);
                }
                
                this.loadDocuments();
                this.loadTagsAndFolders();
            } else {
                showNotification('Error deleting document: ' + data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error deleting document:', error);
            showNotification('Error deleting document', 'warning');
        });
    }
    
    processSelected() {
        if (this.selectedDocuments.length === 0) return;
        this.processDocuments([...this.selectedDocuments]);
    }
    
    deleteSelected() {
        if (this.selectedDocuments.length === 0) return;
        
        if (!confirm('Are you sure you want to delete ' + this.selectedDocuments.length + ' document(s)?')) {
            return;
        }
        
        const promises = this.selectedDocuments.map(id => {
            return authenticatedFetch(`/api/documents/${id}`, {
                method: 'DELETE'
            }).then(response => response.json());
        });
        
        Promise.all(promises)
            .then(() => {
                showNotification('Documents deleted successfully');
                this.selectedDocuments = [];
                this.loadDocuments();
                this.loadTagsAndFolders();
            })
            .catch(error => {
                console.error('Error deleting documents:', error);
                showNotification('Error deleting documents', 'warning');
            });
    }
    
    
    clearAllDocuments() {
        if (!confirm('WARNING: This will permanently delete ALL documents from the system. This action cannot be undone. Are you sure you want to continue?')) {
            return;
        }
        
        // Double confirmation for destructive action
        if (!confirm('FINAL WARNING: All documents will be permanently deleted. Proceed?')) {
            return;
        }
        
        // Show loading state
        this.docList.innerHTML = '<div class="document-loading">Clearing all documents...</div>';
        
        // Call the API endpoint
        authenticatedFetch('/api/documents/actions/clear-all', {
            method: 'DELETE'
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to clear documents');
                }
                return response.json();
            })
            .then(data => {
                // Show success message
                this.docList.innerHTML = '<div class="document-empty">All documents have been cleared</div>';
                this.documents = [];
                this.selectedDocuments = [];
                this.updateDocumentCount(0);
                this.updateBatchButtons();
                
                // Reload tags and folders
                this.loadTagsAndFolders();
                
                // Show notification
                showNotification('success', 'Documents Cleared', `Successfully cleared ${data.document_count} documents from the system.`);
            })
            .catch(error => {
                console.error('Error clearing documents:', error);
                this.docList.innerHTML = '<div class="document-error">Error clearing documents</div>';
                
                // Show error notification
                showNotification('error', 'Error', 'Failed to clear documents. You may not have admin privileges.');
                
                // Reload documents to restore the view
                this.loadDocuments();
            });
    }
    
    updateBatchButtons() {
        const hasSelected = this.selectedDocuments.length > 0;
        
        if (this.processSelectedBtn) {
            this.processSelectedBtn.disabled = !hasSelected;
        }
        
        if (this.deleteSelectedBtn) {
            this.deleteSelectedBtn.disabled = !hasSelected;
        }
    }
    
    updateDocumentCount(count) {
        if (this.documentCount) {
            this.documentCount.textContent = count;
            
            // If there are documents and the section is not expanded, add a visual indicator
            if (count > 0 && !this.isExpanded) {
                this.documentCount.classList.add('has-documents');
            } else {
                this.documentCount.classList.remove('has-documents');
            }
        }
    }
    
    setupMobileSupport() {
        // Add pull-to-refresh functionality
        this.setupPullToRefresh();
        
        // Add swipe gestures for document items
        this.setupSwipeGestures();
    }
    
    removeMobileSupport() {
        // Remove mobile-specific event listeners
        if (this.docList) {
            this.docList.removeEventListener('touchstart', this.touchStartHandler);
            this.docList.removeEventListener('touchmove', this.touchMoveHandler);
            this.docList.removeEventListener('touchend', this.touchEndHandler);
        }
        
        // Remove pull-to-refresh indicator if it exists
        const refreshIndicator = document.querySelector('.pull-to-refresh');
        if (refreshIndicator) {
            refreshIndicator.parentNode.removeChild(refreshIndicator);
        }
    }
    
    setupPullToRefresh() {
        if (!this.docList) return;
        
        // Create pull-to-refresh indicator
        const refreshIndicator = document.createElement('div');
        refreshIndicator.className = 'pull-to-refresh';
        refreshIndicator.style.display = 'none';
        refreshIndicator.innerHTML = '<span class="spinner"></span> Pull to refresh';
        
        // Insert before document list
        this.docList.parentNode.insertBefore(refreshIndicator, this.docList);
        
        // Touch event variables
        let touchStartY = 0;
        let touchEndY = 0;
        
        // Touch event handlers
        this.touchStartHandler = (e) => {
            touchStartY = e.touches[0].clientY;
        };
        
        this.touchMoveHandler = (e) => {
            touchEndY = e.touches[0].clientY;
            
            // If scrolled to top and pulling down
            if (this.docList.scrollTop === 0 && touchEndY > touchStartY) {
                refreshIndicator.style.display = 'flex';
                e.preventDefault(); // Prevent default scroll
            }
        };
        
        this.touchEndHandler = () => {
            if (refreshIndicator.style.display === 'flex') {
                refreshIndicator.innerHTML = '<span class="spinner"></span> Refreshing...';
                
                // Reload documents
                this.loadDocuments().then(() => {
                    refreshIndicator.style.display = 'none';
                });
            }
        };
        
        // Add touch event listeners
        this.docList.addEventListener('touchstart', this.touchStartHandler);
        this.docList.addEventListener('touchmove', this.touchMoveHandler);
        this.docList.addEventListener('touchend', this.touchEndHandler);
    }
    
    setupSwipeGestures() {
        // Set up swipe gestures for document items
        document.querySelectorAll('.sidebar-document-item').forEach(item => {
            // Add delete action event listener to existing swipe actions
            const deleteAction = item.querySelector('.swipe-action.delete-action');
            if (deleteAction) {
                deleteAction.addEventListener('click', () => {
                    const docId = item.dataset.id;
                    if (docId) {
                        this.deleteDocument(docId);
                    }
                });
            }
            
            // Touch variables
            let touchStartX = 0;
            let touchEndX = 0;
            
            // Touch event handlers
            item.addEventListener('touchstart', (e) => {
                touchStartX = e.touches[0].clientX;
            });
            
            item.addEventListener('touchend', (e) => {
                touchEndX = e.changedTouches[0].clientX;
                
                // Swipe left to show delete button
                if (touchStartX - touchEndX > 50) {
                    item.classList.add('show-actions');
                }
                
                // Swipe right to hide actions
                if (touchEndX - touchStartX > 50) {
                    item.classList.remove('show-actions');
                }
            });
        });
    }
}

// Initialize document manager
const documentManager = new DocumentManager();