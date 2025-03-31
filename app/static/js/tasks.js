/**
 * Background Tasks Management JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const statusFilter = document.getElementById('status-filter');
    const typeFilter = document.getElementById('type-filter');
    const applyFiltersBtn = document.getElementById('apply-filters');
    const clearFiltersBtn = document.getElementById('clear-filters');
    const createTaskBtn = document.getElementById('create-task-btn');
    const submitTaskBtn = document.getElementById('submit-task');
    const autoRefreshToggle = document.getElementById('auto-refresh');
    const refreshIntervalSelect = document.getElementById('refresh-interval');
    
    // State
    let currentStatus = '';
    let currentType = '';
    let currentPage = 1;
    let pageSize = 10;
    let totalTasks = 0;
    let refreshInterval = 5000;
    let refreshTimer = null;
    
    // Initialize
    loadTasks();
    loadStats();
    
    // Set up auto-refresh
    autoRefreshToggle.addEventListener('change', function() {
        if (this.checked) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });
    
    refreshIntervalSelect.addEventListener('change', function() {
        refreshInterval = parseInt(this.value);
        if (autoRefreshToggle.checked) {
            stopAutoRefresh();
            startAutoRefresh();
        }
    });
    
    // Start auto-refresh by default
    startAutoRefresh();
    
    // Set up filters
    applyFiltersBtn.addEventListener('click', function() {
        currentStatus = statusFilter.value;
        currentType = typeFilter.value;
        currentPage = 1;
        loadTasks();
    });
    
    clearFiltersBtn.addEventListener('click', function() {
        statusFilter.value = '';
        typeFilter.value = '';
        currentStatus = '';
        currentType = '';
        currentPage = 1;
        loadTasks();
    });
    
    // Set up task creation
    submitTaskBtn.addEventListener('click', function() {
        createTask();
    });
    
    /**
     * Start auto-refresh timer
     */
    function startAutoRefresh() {
        stopAutoRefresh();
        refreshTimer = setInterval(function() {
            loadTasks(false);
            loadStats();
        }, refreshInterval);
    }
    
    /**
     * Stop auto-refresh timer
     */
    function stopAutoRefresh() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }
    
    /**
     * Load tasks from API
     * @param {boolean} resetPage - Whether to reset to page 1
     */
    function loadTasks(resetPage = true) {
        if (resetPage) {
            currentPage = 1;
        }
        
        // Build query parameters
        const params = new URLSearchParams();
        if (currentStatus) {
            params.append('status', currentStatus);
        }
        if (currentType) {
            params.append('task_type', currentType);
        }
        params.append('limit', pageSize);
        params.append('offset', (currentPage - 1) * pageSize);
        
        // Show loading state
        document.getElementById('task-list').innerHTML = '<tr><td colspan="8" class="text-center">Loading tasks...</td></tr>';
        
        // Fetch tasks
        fetch(`/api/v1/tasks?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                renderTasks(data);
            })
            .catch(error => {
                console.error('Error loading tasks:', error);
                document.getElementById('task-list').innerHTML = 
                    '<tr><td colspan="8" class="text-center text-danger">Error loading tasks. Please try again.</td></tr>';
            });
    }
    
    /**
     * Render tasks in the table
     * @param {Object} data - Task data from API
     */
    function renderTasks(data) {
        const taskList = document.getElementById('task-list');
        
        // Update total tasks count
        totalTasks = data.total;
        
        // Check if there are tasks
        if (!data.tasks || data.tasks.length === 0) {
            taskList.innerHTML = '<tr><td colspan="8" class="text-center">No tasks found</td></tr>';
            document.getElementById('pagination').innerHTML = '';
            return;
        }
        
        // Render tasks
        let html = '';
        data.tasks.forEach(task => {
            // Format dates
            const createdDate = new Date(task.created_at);
            
            // Determine status class
            let statusClass = '';
            switch (task.status) {
                case 'pending':
                    statusClass = 'bg-light text-dark';
                    break;
                case 'scheduled':
                    statusClass = 'bg-info text-white';
                    break;
                case 'running':
                    statusClass = 'bg-primary text-white';
                    break;
                case 'completed':
                    statusClass = 'bg-success text-white';
                    break;
                case 'failed':
                    statusClass = 'bg-danger text-white';
                    break;
                case 'cancelled':
                    statusClass = 'bg-secondary text-white';
                    break;
                case 'waiting':
                    statusClass = 'bg-warning text-dark';
                    break;
            }
            
            // Determine priority class
            let priorityClass = '';
            switch (task.priority) {
                case 'low':
                    priorityClass = 'text-muted';
                    break;
                case 'normal':
                    priorityClass = '';
                    break;
                case 'high':
                    priorityClass = 'text-primary fw-bold';
                    break;
                case 'critical':
                    priorityClass = 'text-danger fw-bold';
                    break;
            }
            
            html += `
                <tr>
                    <td><small>${task.id.substring(0, 8)}...</small></td>
                    <td>${task.name}</td>
                    <td>${task.task_type}</td>
                    <td><span class="badge ${statusClass}">${task.status}</span></td>
                    <td><span class="${priorityClass}">${task.priority}</span></td>
                    <td>
                        <div class="progress">
                            <div class="progress-bar" role="progressbar" style="width: ${task.progress}%;" 
                                aria-valuenow="${task.progress}" aria-valuemin="0" aria-valuemax="100">
                                ${Math.round(task.progress)}%
                            </div>
                        </div>
                    </td>
                    <td><small>${createdDate.toLocaleString()}</small></td>
                    <td>
                        <button type="button" class="btn btn-sm btn-outline-primary view-task" data-task-id="${task.id}">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${task.status === 'pending' || task.status === 'scheduled' || task.status === 'running' ? 
                            `<button type="button" class="btn btn-sm btn-outline-danger cancel-task" data-task-id="${task.id}">
                                <i class="fas fa-times"></i>
                            </button>` : ''}
                    </td>
                </tr>
            `;
        });
        
        taskList.innerHTML = html;
        
        // Update pagination
        renderPagination();
        
        // Set up task detail view
        document.querySelectorAll('.view-task').forEach(button => {
            button.addEventListener('click', function() {
                const taskId = this.getAttribute('data-task-id');
                showTaskDetails(taskId);
            });
        });
        
        // Set up task cancellation
        document.querySelectorAll('.cancel-task').forEach(button => {
            button.addEventListener('click', function() {
                const taskId = this.getAttribute('data-task-id');
                cancelTask(taskId);
            });
        });
    }
    
    /**
     * Render pagination controls
     */
    function renderPagination() {
        const pagination = document.getElementById('pagination');
        const totalPages = Math.ceil(totalTasks / pageSize);
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = '';
        
        // Previous button
        html += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage - 1}">Previous</a>
            </li>
        `;
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            html += `
                <li class="page-item ${currentPage === i ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
        
        // Next button
        html += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage + 1}">Next</a>
            </li>
        `;
        
        pagination.innerHTML = html;
        
        // Set up pagination click handlers
        document.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = parseInt(this.getAttribute('data-page'));
                if (page >= 1 && page <= totalPages) {
                    currentPage = page;
                    loadTasks(false);
                }
            });
        });
    }
    
    /**
     * Load system statistics
     */
    function loadStats() {
        fetch('/api/v1/tasks/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Update task counts
                document.getElementById('pending-count').textContent = data.pending_tasks;
                document.getElementById('running-count').textContent = data.running_tasks;
                document.getElementById('completed-count').textContent = data.completed_tasks;
                document.getElementById('failed-count').textContent = data.failed_tasks;
                
                // Update system load
                const loadPercent = Math.round(data.system_load * 100);
                const systemLoadBar = document.getElementById('system-load-bar');
                systemLoadBar.style.width = loadPercent + '%';
                systemLoadBar.setAttribute('aria-valuenow', loadPercent);
                systemLoadBar.textContent = loadPercent + '%';
                
                // Set color based on load
                systemLoadBar.className = 'progress-bar';
                if (loadPercent < 50) {
                    systemLoadBar.classList.add('bg-success');
                } else if (loadPercent < 80) {
                    systemLoadBar.classList.add('bg-warning');
                } else {
                    systemLoadBar.classList.add('bg-danger');
                }
                
                // Update resource alerts
                const alertsList = document.getElementById('alerts-list');
                if (data.resource_alerts && data.resource_alerts.length > 0) {
                    let alertsHtml = '';
                    data.resource_alerts.forEach(alert => {
                        const date = new Date(alert.timestamp * 1000);
                        alertsHtml += `
                            <tr>
                                <td>${date.toLocaleString()}</td>
                                <td>${alert.resource_type}</td>
                                <td>${alert.current_value.toFixed(1)}%</td>
                                <td>${alert.threshold.toFixed(1)}%</td>
                                <td>${alert.message}</td>
                            </tr>
                        `;
                    });
                    alertsList.innerHTML = alertsHtml;
                } else {
                    alertsList.innerHTML = '<tr><td colspan="5" class="text-center">No alerts</td></tr>';
                }
            })
            .catch(error => {
                console.error('Error loading stats:', error);
            });
    }
    
    /**
     * Show task details
     * @param {string} taskId - Task ID
     */
    function showTaskDetails(taskId) {
        fetch(`/api/v1/tasks/${taskId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(task => {
                // Basic details
                document.getElementById('detail-id').textContent = task.id;
                document.getElementById('detail-name').textContent = task.name;
                document.getElementById('detail-type').textContent = task.task_type;
                
                // Status with badge
                let statusClass = '';
                switch (task.status) {
                    case 'pending':
                        statusClass = 'bg-light text-dark';
                        break;
                    case 'scheduled':
                        statusClass = 'bg-info text-white';
                        break;
                    case 'running':
                        statusClass = 'bg-primary text-white';
                        break;
                    case 'completed':
                        statusClass = 'bg-success text-white';
                        break;
                    case 'failed':
                        statusClass = 'bg-danger text-white';
                        break;
                    case 'cancelled':
                        statusClass = 'bg-secondary text-white';
                        break;
                    case 'waiting':
                        statusClass = 'bg-warning text-dark';
                        break;
                }
                document.getElementById('detail-status').innerHTML = `<span class="badge ${statusClass}">${task.status}</span>`;
                
                // Priority
                document.getElementById('detail-priority').textContent = task.priority;
                
                // Dates
                document.getElementById('detail-created').textContent = task.created_at ? new Date(task.created_at).toLocaleString() : 'N/A';
                document.getElementById('detail-started').textContent = task.started_at ? new Date(task.started_at).toLocaleString() : 'N/A';
                document.getElementById('detail-completed').textContent = task.completed_at ? new Date(task.completed_at).toLocaleString() : 'N/A';
                
                // Execution time
                document.getElementById('detail-execution-time').textContent = task.execution_time_ms ? `${(task.execution_time_ms / 1000).toFixed(2)}s` : 'N/A';
                
                // Retries
                document.getElementById('detail-retries').textContent = `${task.retry_count} / ${task.max_retries}`;
                
                // Progress bar
                const progressBar = document.getElementById('detail-progress-bar');
                progressBar.style.width = task.progress + '%';
                progressBar.setAttribute('aria-valuenow', task.progress);
                progressBar.textContent = Math.round(task.progress) + '%';
                
                // Parameters
                document.getElementById('detail-params').textContent = JSON.stringify(task.params, null, 2);
                
                // Result
                if (task.result) {
                    document.getElementById('detail-result').textContent = JSON.stringify(task.result, null, 2);
                } else {
                    document.getElementById('detail-result').textContent = 'No result yet';
                }
                
                // Error
                const errorContainer = document.getElementById('detail-error-container');
                if (task.error) {
                    document.getElementById('detail-error').textContent = task.error;
                    errorContainer.style.display = 'block';
                } else {
                    errorContainer.style.display = 'none';
                }
                
                // Cancel button
                const cancelBtn = document.getElementById('cancel-task');
                if (task.status === 'pending' || task.status === 'scheduled' || task.status === 'running') {
                    cancelBtn.style.display = 'block';
                    cancelBtn.setAttribute('data-task-id', task.id);
                    
                    // Set up cancel button event handler
                    cancelBtn.onclick = function() {
                        const taskId = this.getAttribute('data-task-id');
                        cancelTask(taskId);
                    };
                } else {
                    cancelBtn.style.display = 'none';
                }
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('taskDetailsModal'));
                modal.show();
            })
            .catch(error => {
                console.error('Error loading task details:', error);
                alert('Error loading task details. Please try again.');
            });
    }
    
    /**
     * Create a new task
     */
    function createTask() {
        // Get form values
        const name = document.getElementById('task-name').value;
        const taskType = document.getElementById('task-type').value;
        const priority = document.getElementById('task-priority').value;
        let params = {};
        
        // Validate form
        if (!name || !taskType) {
            alert('Please fill in all required fields');
            return;
        }
        
        // Parse parameters
        try {
            const paramsText = document.getElementById('task-params').value;
            if (paramsText) {
                params = JSON.parse(paramsText);
            }
        } catch (e) {
            alert('Invalid JSON in parameters field');
            return;
        }
        
        // Create task data
        const taskData = {
            name: name,
            task_type: taskType,
            priority: priority,
            params: params
        };
        
        // Submit task
        fetch('/api/v1/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.detail || 'Error creating task');
                });
            }
            return response.json();
        })
        .then(data => {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('createTaskModal'));
            modal.hide();
            
            // Reset form
            document.getElementById('create-task-form').reset();
            
            // Refresh tasks
            loadTasks();
            loadStats();
            
            // Show success message
            alert('Task created successfully');
        })
        .catch(error => {
            console.error('Error creating task:', error);
            alert('Error creating task: ' + error.message);
        });
    }
    
    /**
     * Cancel a task
     * @param {string} taskId - Task ID
     */
    function cancelTask(taskId) {
        if (confirm('Are you sure you want to cancel this task?')) {
            fetch(`/api/v1/tasks/${taskId}/cancel`, {
                method: 'POST'
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.detail || 'Error cancelling task');
                    });
                }
                return response.json();
            })
            .then(data => {
                // Close details modal if open
                const detailsModal = bootstrap.Modal.getInstance(document.getElementById('taskDetailsModal'));
                if (detailsModal) {
                    detailsModal.hide();
                }
                
                // Refresh tasks
                loadTasks();
                loadStats();
                
                // Show success message
                alert('Task cancelled successfully');
            })
            .catch(error => {
                console.error('Error cancelling task:', error);
                alert('Error cancelling task: ' + error.message);
            });
        }
    }
});