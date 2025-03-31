// Schema Viewer JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const connectionSelect = document.getElementById('connection-select');
    const schemaSelect = document.getElementById('schema-select');
    const tableSelect = document.getElementById('table-select');
    const refreshConnectionsBtn = document.getElementById('refresh-connections');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const explainButton = document.getElementById('explain-button');
    const queryInput = document.getElementById('query-input');
    const loadingOverlay = document.getElementById('loading-overlay');
    const errorModal = document.getElementById('error-modal');
    const errorMessage = document.getElementById('error-message');
    const closeModalBtn = document.querySelector('.close');

    // Initialize
    loadConnections();

    // Event listeners
    refreshConnectionsBtn.addEventListener('click', loadConnections);
    connectionSelect.addEventListener('change', handleConnectionChange);
    schemaSelect.addEventListener('change', handleSchemaChange);
    tableSelect.addEventListener('change', handleTableChange);
    explainButton.addEventListener('click', explainQuery);
    closeModalBtn.addEventListener('click', () => errorModal.classList.add('hidden'));

    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Functions
    async function loadConnections() {
        showLoading();
        try {
            const response = await fetch('/api/schema/connections');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            // Clear existing options
            connectionSelect.innerHTML = '<option value="">Select a connection...</option>';
            
            // Add new options
            data.connections.forEach(conn => {
                const option = document.createElement('option');
                option.value = conn.id;
                option.textContent = conn.connection_string;
                connectionSelect.appendChild(option);
            });
            
            // Reset dependent selects
            schemaSelect.innerHTML = '<option value="">Select a schema...</option>';
            schemaSelect.disabled = true;
            tableSelect.innerHTML = '<option value="">Select a table...</option>';
            tableSelect.disabled = true;
            
            // Clear content areas
            clearContentAreas();
            
        } catch (error) {
            showError(`Failed to load connections: ${error.message}`);
        } finally {
            hideLoading();
        }
    }

    async function handleConnectionChange() {
        const connectionId = connectionSelect.value;
        
        if (!connectionId) {
            schemaSelect.innerHTML = '<option value="">Select a schema...</option>';
            schemaSelect.disabled = true;
            tableSelect.innerHTML = '<option value="">Select a table...</option>';
            tableSelect.disabled = true;
            clearContentAreas();
            return;
        }
        
        showLoading();
        try {
            const response = await fetch(`/api/schema/schemas?connection_id=${connectionId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            // Clear existing options
            schemaSelect.innerHTML = '<option value="">Select a schema...</option>';
            
            // Add new options
            data.schemas.forEach(schema => {
                const option = document.createElement('option');
                option.value = schema.schema_name;
                option.textContent = schema.schema_name;
                schemaSelect.appendChild(option);
            });
            
            // Enable schema select
            schemaSelect.disabled = false;
            
            // Reset table select
            tableSelect.innerHTML = '<option value="">Select a table...</option>';
            tableSelect.disabled = true;
            
            // Clear content areas
            clearContentAreas();
            
        } catch (error) {
            showError(`Failed to load schemas: ${error.message}`);
        } finally {
            hideLoading();
        }
    }

    async function handleSchemaChange() {
        const connectionId = connectionSelect.value;
        const schema = schemaSelect.value;
        
        if (!connectionId || !schema) {
            tableSelect.innerHTML = '<option value="">Select a table...</option>';
            tableSelect.disabled = true;
            clearContentAreas();
            return;
        }
        
        showLoading();
        try {
            const response = await fetch(`/api/schema/tables?connection_id=${connectionId}&schema=${schema}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            // Clear existing options
            tableSelect.innerHTML = '<option value="">Select a table...</option>';
            
            // Add new options
            data.tables.forEach(table => {
                const option = document.createElement('option');
                option.value = table.table_name;
                option.textContent = `${table.table_name} (${table.type})`;
                tableSelect.appendChild(option);
            });
            
            // Enable table select
            tableSelect.disabled = false;
            
            // Clear content areas
            clearContentAreas();
            
        } catch (error) {
            showError(`Failed to load tables: ${error.message}`);
        } finally {
            hideLoading();
        }
    }

    async function handleTableChange() {
        const connectionId = connectionSelect.value;
        const schema = schemaSelect.value;
        const table = tableSelect.value;
        
        if (!connectionId || !schema || !table) {
            clearContentAreas();
            return;
        }
        
        showLoading();
        try {
            // Load table structure
            const response = await fetch(`/api/schema/table-structure?connection_id=${connectionId}&table_name=${table}&schema=${schema}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            const tableStructure = data.table_structure;
            
            // Update table info
            document.getElementById('table-name').textContent = tableStructure.table_name;
            document.getElementById('table-description').textContent = tableStructure.description || 'No description available';
            document.getElementById('table-owner').textContent = tableStructure.owner || 'Unknown';
            document.getElementById('table-row-count').textContent = tableStructure.exact_row_count !== null ? 
                tableStructure.exact_row_count : `~${tableStructure.row_estimate} (estimate)`;
            document.getElementById('table-size').textContent = tableStructure.total_size || 'Unknown';
            
            // Update structure content
            const structureContent = document.getElementById('structure-content');
            structureContent.innerHTML = `
                <h3>Table Overview</h3>
                <p>This table has ${tableStructure.columns.length} columns, 
                   ${tableStructure.indexes.length} indexes, and 
                   ${tableStructure.constraints.length} constraints.</p>
            `;
            
            // Update columns content
            const columnsContent = document.getElementById('columns-content');
            columnsContent.innerHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Column Name</th>
                            <th>Data Type</th>
                            <th>Nullable</th>
                            <th>Default</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableStructure.columns.map(column => `
                            <tr>
                                <td>${column.column_name}</td>
                                <td>${column.data_type}</td>
                                <td>${column.is_nullable}</td>
                                <td>${column.default_value || ''}</td>
                                <td>${column.description || ''}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            
            // Update indexes content
            const indexesContent = document.getElementById('indexes-content');
            if (tableStructure.indexes.length > 0) {
                indexesContent.innerHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Index Name</th>
                                <th>Type</th>
                                <th>Definition</th>
                                <th>Unique</th>
                                <th>Primary</th>
                                <th>Size</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableStructure.indexes.map(index => `
                                <tr>
                                    <td>${index.index_name}</td>
                                    <td>${index.index_type}</td>
                                    <td>${index.index_definition}</td>
                                    <td>${index.is_unique}</td>
                                    <td>${index.is_primary}</td>
                                    <td>${index.index_size || ''}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                indexesContent.innerHTML = '<p>No indexes found for this table.</p>';
            }
            
            // Update constraints content
            const constraintsContent = document.getElementById('constraints-content');
            if (tableStructure.constraints.length > 0) {
                constraintsContent.innerHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Constraint Name</th>
                                <th>Type</th>
                                <th>Definition</th>
                                <th>Deferrable</th>
                                <th>Deferred</th>
                                <th>Validated</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableStructure.constraints.map(constraint => `
                                <tr>
                                    <td>${constraint.constraint_name}</td>
                                    <td>${constraint.constraint_type}</td>
                                    <td>${constraint.definition}</td>
                                    <td>${constraint.is_deferrable ? 'YES' : 'NO'}</td>
                                    <td>${constraint.is_deferred ? 'YES' : 'NO'}</td>
                                    <td>${constraint.is_validated ? 'YES' : 'NO'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                constraintsContent.innerHTML = '<p>No constraints found for this table.</p>';
            }
            
            // Update foreign keys content
            const foreignKeysContent = document.getElementById('foreign-keys-content');
            if (tableStructure.foreign_keys.length > 0) {
                foreignKeysContent.innerHTML = `
                    <table>
                        <thead>
                            <tr>
                                <th>Constraint Name</th>
                                <th>Referenced Schema</th>
                                <th>Referenced Table</th>
                                <th>Columns</th>
                                <th>Referenced Columns</th>
                                <th>Update Rule</th>
                                <th>Delete Rule</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableStructure.foreign_keys.map(fk => `
                                <tr>
                                    <td>${fk.constraint_name}</td>
                                    <td>${fk.referenced_schema}</td>
                                    <td>${fk.referenced_table}</td>
                                    <td>${Array.isArray(fk.column_names) ? fk.column_names.join(', ') : fk.column_names}</td>
                                    <td>${Array.isArray(fk.referenced_columns) ? fk.referenced_columns.join(', ') : fk.referenced_columns}</td>
                                    <td>${fk.update_rule}</td>
                                    <td>${fk.delete_rule}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                foreignKeysContent.innerHTML = '<p>No foreign keys found for this table.</p>';
            }
            
        } catch (error) {
            showError(`Failed to load table structure: ${error.message}`);
        } finally {
            hideLoading();
        }
    }

    async function explainQuery() {
        const connectionId = connectionSelect.value;
        const query = queryInput.value.trim();
        const explainType = document.querySelector('input[name="explain-type"]:checked').value;
        
        if (!connectionId) {
            showError('Please select a database connection first.');
            return;
        }
        
        if (!query) {
            showError('Please enter a SQL query to explain.');
            return;
        }
        
        showLoading();
        try {
            const response = await fetch('/api/schema/explain-query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    connection_id: connectionId,
                    query: query,
                    explain_type: explainType
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const explainContent = document.getElementById('explain-content');
            
            if (explainType === 'json' || explainType === 'analyze_json') {
                // Format JSON for display
                explainContent.innerHTML = `<pre>${JSON.stringify(data.plan, null, 2)}</pre>`;
            } else {
                // Display text plan
                explainContent.innerHTML = `<pre>${data.plan_text}</pre>`;
            }
            
        } catch (error) {
            showError(`Failed to explain query: ${error.message}`);
        } finally {
            hideLoading();
        }
    }

    function clearContentAreas() {
        document.getElementById('table-name').textContent = '';
        document.getElementById('table-description').textContent = '';
        document.getElementById('table-owner').textContent = '';
        document.getElementById('table-row-count').textContent = '';
        document.getElementById('table-size').textContent = '';
        
        document.getElementById('structure-content').innerHTML = '';
        document.getElementById('columns-content').innerHTML = '';
        document.getElementById('indexes-content').innerHTML = '';
        document.getElementById('constraints-content').innerHTML = '';
        document.getElementById('foreign-keys-content').innerHTML = '';
        document.getElementById('explain-content').innerHTML = '';
    }

    function showLoading() {
        loadingOverlay.classList.remove('hidden');
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorModal.classList.remove('hidden');
    }
});