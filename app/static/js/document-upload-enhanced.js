/**
 * Enhanced Document Upload Functionality
 * Implements the Phase 2 improvements for the document upload interface
 */
class EnhancedDocumentUpload {
    constructor() {
        // Initialize properties
        this.fileQueue = [];
        this.selectedFiles = [];
        this.uploadStartTime = null;
        this.fileStartTimes = {};
        this.isUploading = false;
        this.viewMode = 'grid'; // 'grid' or 'list'
        
        // Initialize after DOM is loaded
        document.addEventListener('DOMContentLoaded', () => this.initialize());
    }
    
    /**
     * Initialize the enhanced document upload functionality
     */
    initialize() {
        console.log('Initializing Enhanced Document Upload');
        
        // Add the CSS file
        this.addStylesheet();
        
        // Convert existing sections to collapsible sections
        this.setupCollapsibleSections();
        
        // Setup the enhanced drop zone
        this.setupDropZone();
        
        // Setup batch actions
        this.setupBatchActions();
        
        // Setup modals
        this.setupModals();
    }
    
    /**
     * Add the enhanced CSS stylesheet
     */
    addStylesheet() {
        if (!document.querySelector('link[href*="document-upload-enhanced.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/css/document-upload-enhanced.css';
            document.head.appendChild(link);
        }
    }
    
    /**
     * Convert existing sections to collapsible sections
     */
    setupCollapsibleSections() {
        // Get all sections that should be collapsible
        const uploadForm = document.querySelector('.upload-form');
        const filterSection = document.querySelector('.filter-section');
        const processingOptions = document.querySelector('.processing-options')?.closest('.document-section');
        
        if (uploadForm) {
            this.convertToCollapsibleSection(uploadForm, 'Upload Documents', 'fa-cloud-upload-alt');
        }
        
        if (filterSection) {
            this.convertToCollapsibleSection(filterSection, 'Filter Documents', 'fa-filter');
        }
        
        if (processingOptions) {
            this.convertToCollapsibleSection(processingOptions, 'Document Processing Options', 'fa-cogs');
        }
        
        // Create a new section for selected files
        this.createSelectedFilesSection();
        
        // Create a new section for upload progress
        this.createProgressSection();
    }
    
    /**
     * Convert an element to a collapsible section
     */
    convertToCollapsibleSection(element, title, iconClass) {
        // Create the collapsible section
        const section = document.createElement('div');
        section.className = 'collapsible-section';
        
        // Create the header
        const header = document.createElement('div');
        header.className = 'section-header';
        header.innerHTML = `
            <h3><i class="fas ${iconClass}"></i> ${title}</h3>
            <button class="toggle-btn"><i class="fas fa-chevron-down"></i></button>
        `;
        
        // Create the content container
        const content = document.createElement('div');
        content.className = 'section-content';
        
        // Move the original element's content to the content container
        while (element.firstChild) {
            content.appendChild(element.firstChild);
        }
        
        // Add the header and content to the section
        section.appendChild(header);
        section.appendChild(content);
        
        // Replace the original element with the section
        element.parentNode.replaceChild(section, element);
        
        // Add event listener for toggling
        header.addEventListener('click', () => {
            section.classList.toggle('collapsed');
        });
        
        return section;
    }
    
    /**
     * Create a new section for selected files
     */
    createSelectedFilesSection() {
        // Check if file list already exists
        const existingFileList = document.getElementById('file-list');
        if (!existingFileList) return;
        
        // Create the section
        const section = document.createElement('div');
        section.className = 'collapsible-section';
        section.id = 'selected-files-section';
        
        // Create the header
        const header = document.createElement('div');
        header.className = 'section-header';
        header.innerHTML = `
            <h3><i class="fas fa-file-alt"></i> Selected Files (<span id="file-count">0</span>)</h3>
            <div class="section-actions">
                <button id="view-toggle-grid" class="view-toggle-btn active" title="Grid View">
                    <i class="fas fa-th-large"></i>
                </button>
                <button id="view-toggle-list" class="view-toggle-btn" title="List View">
                    <i class="fas fa-list"></i>
                </button>
                <button class="toggle-btn"><i class="fas fa-chevron-down"></i></button>
            </div>
        `;
        
        // Create the content container
        const content = document.createElement('div');
        content.className = 'section-content';
        
        // Create the file list container
        const fileList = document.createElement('div');
        fileList.id = 'file-list';
        fileList.className = 'file-list grid-view';
        
        // Create the file actions
        const fileActions = document.createElement('div');
        fileActions.className = 'file-actions';
        fileActions.innerHTML = `
            <button id="clear-files-btn" class="btn">Clear All</button>
            <button id="upload-files-btn" class="btn primary">Upload Files</button>
        `;
        
        // Add the file list and actions to the content
        content.appendChild(fileList);
        content.appendChild(fileActions);
        
        // Add the header and content to the section
        section.appendChild(header);
        section.appendChild(content);
        
        // Insert the section after the upload form
        const uploadForm = document.querySelector('.collapsible-section');
        if (uploadForm) {
            uploadForm.parentNode.insertBefore(section, uploadForm.nextSibling);
        }
        
        // Add event listeners
        header.addEventListener('click', (e) => {
            if (!e.target.closest('.view-toggle-btn')) {
                section.classList.toggle('collapsed');
            }
        });
        
        document.getElementById('view-toggle-grid')?.addEventListener('click', () => this.setViewMode('grid'));
        document.getElementById('view-toggle-list')?.addEventListener('click', () => this.setViewMode('list'));
        document.getElementById('clear-files-btn')?.addEventListener('click', () => this.clearFileQueue());
        document.getElementById('upload-files-btn')?.addEventListener('click', () => this.uploadFiles());
    }
    
    /**
     * Create a new section for upload progress
     */
    createProgressSection() {
        // Check if progress container already exists
        const existingProgress = document.querySelector('.progress-container');
        if (!existingProgress) return;
        
        // Create the section
        const section = document.createElement('div');
        section.className = 'collapsible-section';
        section.id = 'progress-section';
        
        // Create the header
        const header = document.createElement('div');
        header.className = 'section-header';
        header.innerHTML = `
            <h3><i class="fas fa-tasks"></i> Upload Progress</h3>
            <button class="toggle-btn"><i class="fas fa-chevron-down"></i></button>
        `;
        
        // Create the content container
        const content = document.createElement('div');
        content.className = 'section-content';
        
        // Create the progress container
        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress-container';
        
        // Create the overall progress
        const overallProgress = document.createElement('div');
        overallProgress.className = 'overall-progress';
        overallProgress.innerHTML = `
            <div class="progress-header">
                <span class="progress-title">Overall Progress</span>
                <span class="progress-stats">
                    <span id="completed-count">0</span>/<span id="total-count">0</span> files
                </span>
            </div>
            <div class="progress-bar" id="overall-progress">
                <div class="progress-bar-fill" id="overall-progress-fill"></div>
            </div>
            <div class="progress-details">
                <span id="overall-percent">0%</span>
                <span id="time-remaining">Estimating time...</span>
            </div>
        `;
        
        // Create the file progress list
        const fileProgressList = document.createElement('div');
        fileProgressList.id = 'file-progress-list';
        fileProgressList.className = 'file-progress-list';
        
        // Add the overall progress and file progress list to the progress container
        progressContainer.appendChild(overallProgress);
        progressContainer.appendChild(fileProgressList);
        
        // Add the progress container to the content
        content.appendChild(progressContainer);
        
        // Add the header and content to the section
        section.appendChild(header);
        section.appendChild(content);
        
        // Insert the section after the selected files section
        const selectedFilesSection = document.getElementById('selected-files-section');
        if (selectedFilesSection) {
            selectedFilesSection.parentNode.insertBefore(section, selectedFilesSection.nextSibling);
        }
        
        // Add event listener for toggling
        header.addEventListener('click', () => {
            section.classList.toggle('collapsed');
        });
        
        // Initially collapse the progress section
        section.classList.add('collapsed');
    }
    
    /**
     * Setup the enhanced drop zone
     */
    setupDropZone() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('document-file');
        
        if (!dropZone || !fileInput) return;
        
        // Add the drop zone icon
        const dropZoneContent = dropZone.innerHTML;
        dropZone.innerHTML = `
            <div class="drop-zone-icon">
                <i class="fas fa-cloud-upload-alt"></i>
            </div>
            ${dropZoneContent}
        `;
        
        // Replace the file input with a button
        const fileInputParent = fileInput.parentNode;
        const selectButton = document.createElement('button');
        selectButton.type = 'button';
        selectButton.className = 'select-files-btn';
        selectButton.textContent = 'Select Files';
        selectButton.addEventListener('click', () => fileInput.click());
        
        // Keep the file input but hide it
        fileInputParent.appendChild(selectButton);
        
        // Add drag and drop event listeners
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            
            if (e.dataTransfer.files.length > 0) {
                this.handleFileSelection(e.dataTransfer.files);
            }
        });
        
        // Add file input change event listener
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelection(e.target.files);
        });
    }
    
    /**
     * Handle file selection
     */
    handleFileSelection(files) {
        if (!files || files.length === 0) return;
        
        // Add files to queue
        Array.from(files).forEach(file => {
            // Check if file is already in queue
            const existingFile = this.fileQueue.find(f => f.name === file.name && f.size === file.size);
            if (!existingFile) {
                // Add unique ID and metadata
                const fileWithId = file;
                fileWithId.id = 'file_' + Math.random().toString(36).substr(2, 9);
                fileWithId.selected = false;
                this.fileQueue.push(fileWithId);
            }
        });
        
        // Update file list display
        this.updateFileList();
        
        // Update file count
        this.updateFileCount();
        
        // Expand the selected files section if collapsed
        const selectedFilesSection = document.getElementById('selected-files-section');
        if (selectedFilesSection && selectedFilesSection.classList.contains('collapsed')) {
            selectedFilesSection.classList.remove('collapsed');
        }
    }
    
    /**
     * Update the file list display
     */
    updateFileList() {
        const fileList = document.getElementById('file-list');
        if (!fileList) return;
        
        // Clear the file list
        fileList.innerHTML = '';
        
        // Add files to the list
        this.fileQueue.forEach(file => {
            const filePreview = this.createFilePreview(file);
            fileList.appendChild(filePreview);
        });
        
        // Show/hide the file list
        if (this.fileQueue.length === 0) {
            fileList.style.display = 'none';
        } else {
            fileList.style.display = 'grid';
        }
    }
    
    /**
     * Create a file preview element
     */
    createFilePreview(file) {
        const preview = document.createElement('div');
        preview.className = 'file-preview';
        preview.dataset.id = file.id;
        preview.dataset.filename = file.name;
        
        // Create thumbnail based on file type
        const thumbnail = document.createElement('div');
        thumbnail.className = 'file-thumbnail';
        
        // Determine the appropriate icon based on file type
        let iconClass = 'fa-file';
        const fileExt = file.name.split('.').pop().toLowerCase() || '';
        
        switch (fileExt) {
            case 'pdf': iconClass = 'fa-file-pdf'; break;
            case 'doc': case 'docx': iconClass = 'fa-file-word'; break;
            case 'xls': case 'xlsx': iconClass = 'fa-file-excel'; break;
            case 'txt': iconClass = 'fa-file-alt'; break;
            case 'csv': iconClass = 'fa-file-csv'; break;
            case 'jpg': case 'jpeg': case 'png': iconClass = 'fa-file-image'; break;
            case 'html': case 'htm': iconClass = 'fa-file-code'; break;
        }
        
        thumbnail.innerHTML = `<i class="fas ${iconClass}"></i>`;
        
        // Add file info
        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';
        fileInfo.innerHTML = `
            <div class="file-name">${file.name}</div>
            <div class="file-meta">
                <span class="file-size">${this.formatFileSize(file.size)}</span>
                <span class="file-type">${fileExt.toUpperCase()}</span>
            </div>
            <div class="file-date">Modified: ${new Date(file.lastModified).toLocaleDateString()}</div>
        `;
        
        // Add checkbox for selection
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'file-select';
        checkbox.checked = file.selected;
        checkbox.addEventListener('change', () => {
            file.selected = checkbox.checked;
            this.updateSelectedFiles();
        });
        
        // Add remove button
        const removeBtn = document.createElement('button');
        removeBtn.className = 'file-remove';
        removeBtn.innerHTML = '&times;';
        removeBtn.addEventListener('click', () => this.removeFileFromQueue(file.id));
        
        // Add elements to preview
        preview.appendChild(checkbox);
        preview.appendChild(thumbnail);
        preview.appendChild(fileInfo);
        preview.appendChild(removeBtn);
        
        return preview;
    }
    
    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * Remove a file from the queue
     */
    removeFileFromQueue(fileId) {
        const index = this.fileQueue.findIndex(file => file.id === fileId);
        if (index !== -1) {
            this.fileQueue.splice(index, 1);
            this.updateFileList();
            this.updateFileCount();
            this.updateSelectedFiles();
        }
    }
    
    /**
     * Clear the file queue
     */
    clearFileQueue() {
        this.fileQueue = [];
        this.updateFileList();
        this.updateFileCount();
        this.updateSelectedFiles();
    }
    
    /**
     * Update the file count display
     */
    updateFileCount() {
        const fileCount = document.getElementById('file-count');
        if (fileCount) {
            fileCount.textContent = this.fileQueue.length;
        }
    }
    
    /**
     * Set the view mode (grid or list)
     */
    setViewMode(mode) {
        this.viewMode = mode;
        
        const fileList = document.getElementById('file-list');
        const gridBtn = document.getElementById('view-toggle-grid');
        const listBtn = document.getElementById('view-toggle-list');
        
        if (fileList) {
            fileList.className = `file-list ${mode}-view`;
        }
        
        if (gridBtn) {
            gridBtn.classList.toggle('active', mode === 'grid');
        }
        
        if (listBtn) {
            listBtn.classList.toggle('active', mode === 'list');
        }
    }
    
    /**
     * Setup batch actions
     */
    setupBatchActions() {
        // Create batch actions toolbar
        this.createBatchActionsToolbar();
    }
    
    /**
     * Create the batch actions toolbar
     */
    createBatchActionsToolbar() {
        // Check if toolbar already exists
        if (document.getElementById('batch-actions-toolbar')) return;
        
        // Create the toolbar
        const toolbar = document.createElement('div');
        toolbar.id = 'batch-actions-toolbar';
        toolbar.className = 'batch-actions-toolbar';
        toolbar.innerHTML = `
            <div class="selection-count">
                <span id="selected-count">0</span> files selected
            </div>
            <div class="batch-actions-buttons">
                <button id="batch-tag-btn" class="batch-btn">
                    <i class="fas fa-tags"></i> Tag
                </button>
                <button id="batch-folder-btn" class="batch-btn">
                    <i class="fas fa-folder"></i> Move
                </button>
                <button id="batch-delete-btn" class="batch-btn danger">
                    <i class="fas fa-trash"></i> Delete
                </button>
                <button id="batch-process-btn" class="batch-btn primary">
                    <i class="fas fa-cogs"></i> Process
                </button>
            </div>
        `;
        
        // Add the toolbar to the body
        document.body.appendChild(toolbar);
        
        // Add event listeners for batch actions
        // These would be implemented in a real application
    }
    
    /**
     * Update the selected files list
     */
    updateSelectedFiles() {
        this.selectedFiles = this.fileQueue.filter(file => file.selected);
        
        // Update the selected count
        const selectedCount = document.getElementById('selected-count');
        if (selectedCount) {
            selectedCount.textContent = this.selectedFiles.length;
        }
        
        // Show/hide the batch actions toolbar
        const toolbar = document.getElementById('batch-actions-toolbar');
        if (toolbar) {
            toolbar.classList.toggle('visible', this.selectedFiles.length > 0);
        }
    }
    
    /**
     * Setup modals for batch operations
     */
    setupModals() {
        // In a real implementation, this would create modals for:
        // - Batch tagging
        // - Batch folder assignment
        // - Batch deletion confirmation
        // - Upload summary
    }
    
    /**
     * Upload files
     */
    uploadFiles() {
        // This would implement the actual file upload functionality
        // with enhanced progress tracking
        console.log('Upload files functionality would be implemented here');
        showNotification('Upload functionality implemented in the full version', 'info');
    }
}

// Initialize the enhanced document upload
const enhancedUpload = new EnhancedDocumentUpload();
