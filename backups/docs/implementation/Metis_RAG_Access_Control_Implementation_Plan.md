# Metis RAG Access Control Implementation Plan

## Overview

This document outlines the implementation plan for enhancing Metis RAG's access control, user roles, and permission management capabilities. The goal is to create a secure, flexible, and collaborative system that respects data boundaries while enabling appropriate sharing of knowledge across teams and organizations.

## Current State Analysis

Based on the analysis of the codebase, the following observations were made:

1. **Authentication System**: The system has JWT-based authentication with basic user/admin roles.
2. **Resource Ownership**: Documents and conversations are linked to users via a `user_id` field.
3. **Data Access Gaps**:
   - Vector Store queries don't consistently filter by user ownership
   - No mechanism for document sharing between users
   - Limited role granularity (only user/admin)
   - Tools lack user-specific access controls
   - No team or organization structure for group permissions

## Implementation Plan

### 1. Data Model Enhancements

#### 1.1 Document Sharing Structure

Create new database tables to support document sharing:

```sql
CREATE TABLE document_sharing (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    shared_with_user_id UUID REFERENCES users(id) NULL,
    shared_with_team_id UUID REFERENCES teams(id) NULL,
    shared_with_organization_id UUID REFERENCES organizations(id) NULL,
    permission_level VARCHAR NOT NULL, -- 'read', 'write', 'admin'
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    CHECK (
        (shared_with_user_id IS NOT NULL AND shared_with_team_id IS NULL AND shared_with_organization_id IS NULL) OR
        (shared_with_user_id IS NULL AND shared_with_team_id IS NOT NULL AND shared_with_organization_id IS NULL) OR
        (shared_with_user_id IS NULL AND shared_with_team_id IS NULL AND shared_with_organization_id IS NOT NULL)
    )
);

CREATE INDEX ix_document_sharing_document_id ON document_sharing(document_id);
CREATE INDEX ix_document_sharing_user_id ON document_sharing(shared_with_user_id);
CREATE INDEX ix_document_sharing_team_id ON document_sharing(shared_with_team_id);
CREATE INDEX ix_document_sharing_organization_id ON document_sharing(shared_with_organization_id);
```

#### 1.2 Organization and Team Structure

Create tables for organization and team management:

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE TABLE teams (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE TABLE user_organizations (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL, -- 'member', 'admin'
    joined_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, organization_id)
);

CREATE TABLE user_teams (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL, -- 'member', 'admin'
    joined_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, team_id)
);
```

#### 1.3 Enhanced User Roles

Update the `users` table to support more granular roles:

```sql
ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'user';
-- Possible roles: 'user', 'power_user', 'team_admin', 'org_admin', 'super_admin', 'read_only'
```

#### 1.4 Document Visibility Field

Add a visibility field to documents:

```sql
ALTER TABLE documents ADD COLUMN visibility VARCHAR NOT NULL DEFAULT 'private';
-- Possible values: 'private', 'shared', 'team', 'organization', 'public'
```

### 2. Backend Implementation

#### 2.1 Update RAG Engine for Access Control

Modify the RAG engine to include access control in vector store searches:

```python
async def search(self, query: str, user_id: str, top_k: int = 10, **kwargs):
    """
    Search for documents with access control
    """
    # Get document IDs the user can access
    accessible_docs = await self._get_accessible_documents(user_id)
    
    # Add filter to only retrieve from accessible documents
    filter_criteria = kwargs.get("filter_criteria", {})
    filter_criteria["document_id"] = {"$in": accessible_docs}
    
    # Perform the search with access filters
    search_results = await self.vector_store.search(
        query=query,
        top_k=top_k,
        filter_criteria=filter_criteria
    )
    
    return search_results

async def _get_accessible_documents(self, user_id: str) -> List[str]:
    """
    Get documents that the user can access:
    - Documents owned by the user
    - Documents shared with the user
    - Documents shared with user's teams
    - Documents shared with user's organization
    - Public documents
    """
    # Implementation details here
```

#### 2.2 Repository Access Control Layer

Create a base access control service for repositories:

```python
class AccessControlService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_document_access(self, user_id: str, document_id: str, 
                                     required_permission: str = 'read') -> bool:
        """
        Check if a user has access to a document
        
        Args:
            user_id: User ID
            document_id: Document ID
            required_permission: Required permission level ('read', 'write', 'admin')
            
        Returns:
            True if user has access, False otherwise
        """
        # Check if user owns the document
        stmt = select(Document).where(Document.id == document_id, Document.user_id == user_id)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return True
            
        # Check if document is public
        stmt = select(Document).where(
            Document.id == document_id,
            Document.visibility == 'public'
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return True
            
        # Check individual sharing
        stmt = select(DocumentSharing).where(
            DocumentSharing.document_id == document_id,
            DocumentSharing.shared_with_user_id == user_id,
            self._permission_check(DocumentSharing.permission_level, required_permission)
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return True
            
        # Check team sharing
        # Get user's teams
        user_teams_stmt = select(UserTeam.team_id).where(UserTeam.user_id == user_id)
        user_teams = await self.session.execute(user_teams_stmt)
        team_ids = [team_id for (team_id,) in user_teams]
        
        if team_ids:
            stmt = select(DocumentSharing).where(
                DocumentSharing.document_id == document_id,
                DocumentSharing.shared_with_team_id.in_(team_ids),
                self._permission_check(DocumentSharing.permission_level, required_permission)
            )
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                return True
                
        # Check organization sharing
        # Get user's organizations
        user_orgs_stmt = select(UserOrganization.organization_id).where(UserOrganization.user_id == user_id)
        user_orgs = await self.session.execute(user_orgs_stmt)
        org_ids = [org_id for (org_id,) in user_orgs]
        
        if org_ids:
            stmt = select(DocumentSharing).where(
                DocumentSharing.document_id == document_id,
                DocumentSharing.shared_with_organization_id.in_(org_ids),
                self._permission_check(DocumentSharing.permission_level, required_permission)
            )
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                return True
                
        return False
        
    def _permission_check(self, permission_level, required_permission):
        """Map permission hierarchy for comparison"""
        permission_map = {
            'read': ['read', 'write', 'admin'],
            'write': ['write', 'admin'],
            'admin': ['admin']
        }
        return permission_level.in_(permission_map[required_permission])
```

#### 2.3 Tool Registry with Permission Checks

Update the Tool Registry to check permissions:

```python
class ToolRegistry:
    # ...existing code...
    
    async def execute_tool(self, tool_name: str, input_data: Dict[str, Any], 
                           user_id: str = None) -> Dict[str, Any]:
        """
        Execute a tool with permission checks
        
        Args:
            tool_name: Name of the tool to execute
            input_data: Tool input data
            user_id: User ID for permission checking
            
        Returns:
            Tool execution result
        """
        # Get the tool
        tool = self.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}
            
        # Check permissions if user_id provided
        if user_id:
            can_use_tool = await self._check_tool_permission(tool_name, user_id)
            if not can_use_tool:
                return {"error": f"Permission denied for tool: {tool_name}"}
                
        # Execute the tool
        return await tool.execute(input_data)
        
    async def _check_tool_permission(self, tool_name: str, user_id: str) -> bool:
        """
        Check if a user can use a tool
        
        Args:
            tool_name: Tool name
            user_id: User ID
            
        Returns:
            True if permitted, False otherwise
        """
        # Get user role
        session = await get_db_session()
        try:
            stmt = select(User.role).where(User.id == user_id)
            result = await session.execute(stmt)
            role = result.scalar_one_or_none()
            
            # Tool permission mapping
            tool_permissions = {
                # Basic tools available to all users
                'rag': ['user', 'power_user', 'team_admin', 'org_admin', 'super_admin'],
                
                # Advanced tools with restricted access
                'database': ['power_user', 'team_admin', 'org_admin', 'super_admin'],
                'calculator': ['user', 'power_user', 'team_admin', 'org_admin', 'super_admin'],
                
                # Admin-only tools
                'system': ['org_admin', 'super_admin']
            }
            
            # Check if role has permission to use the tool
            return role in tool_permissions.get(tool_name, ['super_admin'])
        finally:
            await session.close()
```

#### 2.4 Query Planner with Permission Awareness

Update the Query Planner to incorporate permissions:

```python
class QueryPlanner:
    # ...existing code...
    
    async def create_plan(self, query_id: str, query: str, user_id: str) -> QueryPlan:
        """
        Create a plan for executing a query
        
        Args:
            query_id: Unique query ID
            query: Query string
            user_id: User ID for permission checking
            
        Returns:
            QueryPlan instance
        """
        self.logger.info(f"Creating plan for query: {query}")
        
        # Store user ID for permission checking during execution
        self.current_user_id = user_id
        
        # Analyze the query
        analysis = await self.query_analyzer.analyze(query)
        
        # Determine if the query is simple or complex
        complexity = analysis.get("complexity", "simple")
        required_tools = analysis.get("requires_tools", [])
        sub_queries = analysis.get("sub_queries", [])
        
        # Create plan steps
        steps = []
        
        # Filter required tools based on user permissions
        permitted_tools = await self._filter_permitted_tools(required_tools, user_id)
        
        # Create steps with user context
        if complexity == "simple":
            # Simple query - just use RAG
            steps.append({
                "type": "tool",
                "tool": "rag",
                "input": {
                    "query": query,
                    "top_k": 5,
                    "user_id": user_id  # Include user ID for access control
                },
                "description": "Retrieve information using RAG"
            })
        else:
            # Complex query - may require multiple steps
            
            # First, add steps for any required tools
            for tool_name in permitted_tools:
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    self.logger.warning(f"Required tool not found: {tool_name}")
                    continue
                
                # Create a step for this tool with user context
                tool_input = self._create_tool_input(tool_name, query)
                tool_input["user_id"] = user_id  # Add user ID for access control
                steps.append({
                    "type": "tool",
                    "tool": tool_name,
                    "input": tool_input,
                    "description": f"Execute {tool_name} tool"
                })
            
            # Handle sub-queries with user context
            for sub_query in sub_queries:
                steps.append({
                    "type": "tool",
                    "tool": "rag",
                    "input": {
                        "query": sub_query,
                        "top_k": 3,
                        "user_id": user_id  # Include user ID for access control
                    },
                    "description": f"Retrieve information for sub-query: {sub_query}"
                })
            
            # Add a final step to synthesize the results
            steps.append({
                "type": "synthesize",
                "description": "Synthesize results from previous steps"
            })
        
        # Create the plan
        plan = QueryPlan(
            query_id=query_id,
            query=query,
            steps=steps,
            user_id=user_id  # Store user ID in the plan
        )
        
        self.logger.info(f"Created plan with {len(steps)} steps for query: {query}")
        return plan
        
    async def _filter_permitted_tools(self, tools: List[str], user_id: str) -> List[str]:
        """Filter tool list based on user permissions"""
        permitted_tools = []
        for tool_name in tools:
            can_use = await self.tool_registry._check_tool_permission(tool_name, user_id)
            if can_use:
                permitted_tools.append(tool_name)
            else:
                self.logger.warning(f"User {user_id} doesn't have permission to use tool: {tool_name}")
        return permitted_tools
```

### 3. Frontend Implementation

#### 3.1 Document Management Page Enhancements

Create a dedicated document management interface with the following features:

1. Document list with visibility indicators
2. Sharing controls for each document
3. Filter options for owned vs. shared documents
4. Batch operations for sharing with teams/organizations

#### 3.2 Sharing Interface

Design a new sharing modal/panel that appears when clicking a "Share" button:

1. User search functionality
2. Team/Organization selection
3. Permission level selection (read/write/admin)
4. Current sharing status display
5. Option to make document public

#### 3.3 Permission Management Pages

Create new administrative pages for permission management:

1. User management page for admins
2. Team creation and management page
3. Organization structure management
4. Role assignment interface
5. Bulk permission operations

#### 3.4 Navigation and Information Architecture

Update the application's navigation and information architecture:

1. Separate "My Documents" and "Shared With Me" sections
2. Add "Teams" and "Organization" sections in the sidebar
3. Create an "Admin" section for permission management
4. Add document ownership and sharing indicators throughout the UI

## Implementation Checklist

### Phase 1: Data Model and Core Backend

- [ ] **Database Schema Updates**
  - [ ] Create migration for `document_sharing` table
  - [ ] Create migration for `organizations` table
  - [ ] Create migration for `teams` table
  - [ ] Create migration for `user_organizations` table
  - [ ] Create migration for `user_teams` table
  - [ ] Add `role` column to `users` table
  - [ ] Add `visibility` column to `documents` table

- [ ] **Core Access Control Service**
  - [ ] Implement `AccessControlService` class
  - [ ] Create document access permission logic
  - [ ] Add organization & team membership checks
  - [ ] Create permission validation utilities

- [ ] **Repository Layer Updates**
  - [ ] Update `DocumentRepository` to use access control
  - [ ] Update other repositories to check permissions
  - [ ] Add sharing management methods
  - [ ] Create tests for access control logic

### Phase 2: RAG and Tool Integration

- [ ] **RAG Engine Modifications**
  - [ ] Update vector search to filter by access permissions
  - [ ] Add user context to all search operations
  - [ ] Implement document visibility filtering
  - [ ] Update query processing for permission checks

- [ ] **Tool Registry Enhancements**
  - [ ] Add permission checks to tool execution
  - [ ] Create role-based permission mappings
  - [ ] Update tool input schemas to include user context
  - [ ] Create tests for tool permission controls

- [ ] **Query Planner Updates**
  - [ ] Add user context to query plans
  - [ ] Filter tools based on user permissions
  - [ ] Enhance plan execution with permission checks
  - [ ] Create tests for permission-aware query planning

### Phase 3: Frontend Implementation

- [ ] **Document Management UI**
  - [ ] Design document list with sharing indicators
  - [ ] Implement filter tabs for different document types
  - [ ] Create document card components with ownership info
  - [ ] Add multi-select and batch operations

- [ ] **Sharing Interface**
  - [ ] Design sharing modal component
  - [ ] Implement user search functionality
  - [ ] Create team/organization selector
  - [ ] Implement permission level controls
  - [ ] Create sharing status display

- [ ] **Administrative Pages**
  - [ ] Design user management interface
  - [ ] Create team management pages
  - [ ] Implement organization structure UI
  - [ ] Design role assignment interface
  - [ ] Create permission audit reports

- [ ] **Navigation and Information Architecture**
  - [ ] Update sidebar navigation
  - [ ] Create document ownership badges
  - [ ] Implement sharing status indicators
  - [ ] Add permission-based conditional rendering

### Phase 4: Testing and Deployment

- [ ] **Unit and Integration Testing**
  - [ ] Create test cases for access control logic
  - [ ] Test document sharing functionality
  - [ ] Verify permission-based filtering
  - [ ] Test all UI components

- [ ] **End-to-End Testing**
  - [ ] Create test scenarios for different user roles
  - [ ] Test sharing workflows
  - [ ] Verify permission inheritance
  - [ ] Test edge cases and error handling

- [ ] **Documentation**
  - [ ] Update API documentation
  - [ ] Create user guide for sharing features
  - [ ] Document administrative workflows
  - [ ] Create developer documentation for permission system

- [ ] **Deployment**
  - [ ] Create database migration scripts
  - [ ] Plan data backups before migration
  - [ ] Schedule deployment window
  - [ ] Prepare rollback plan

## Frontend Design Mockups

### Document Management Page

```
+----------------------------------------------+
| Documents                                    |
+----------------------------------------------+
| [My Documents] [Shared With Me] [Team Docs]  |
+----------------------------------------------+
| [+ Upload] [+ New Folder] [Search...]        |
+----------------------------------------------+
| Filters: [All ▼] [Recent ▼] [Tags ▼]         |
+----------------------------------------------+
| ┌────────────────────────────────────────┐   |
| │ 📄 Document_1.pdf                       │   |
| │ [Private] Last modified: 2 days ago     │   |
| │ [View] [Share] [Edit] [Delete]          │   |
| └────────────────────────────────────────┘   |
| ┌────────────────────────────────────────┐   |
| │ 📄 Document_2.docx                      │   |
| │ [Shared with 3 users] Modified: Today   │   |
| │ [View] [Share] [Edit] [Delete]          │   |
| └────────────────────────────────────────┘   |
| ┌────────────────────────────────────────┐   |
| │ 📄 Team_Report.pdf                      │   |
| │ [Shared with Marketing Team] Yesterday  │   |
| │ [View] [Share] [Edit] [Delete]          │   |
| └────────────────────────────────────────┘   |
+----------------------------------------------+
```

### Sharing Modal

```
+----------------------------------------------+
| Share "Document_1.pdf"                     X |
+----------------------------------------------+
| Current visibility: Private                  |
+----------------------------------------------+
| Change visibility:                           |
| (•) Private  ( ) Team  ( ) Organization      |
| ( ) Public                                   |
+----------------------------------------------+
| Share with specific users:                   |
| [Search users...] [Add ⊕]                    |
+----------------------------------------------+
| Currently shared with:                       |
|                                              |
| No users                                     |
|                                              |
+----------------------------------------------+
| Share with teams:                            |
| [Select team ▼] [Permission ▼] [Add ⊕]       |
+----------------------------------------------+
| Currently shared with:                       |
|                                              |
| No teams                                     |
|                                              |
+----------------------------------------------+
| [Generate sharing link]  [Save Changes]      |
+----------------------------------------------+
```

### Team Management Page

```
+----------------------------------------------+
| Team Management                              |
+----------------------------------------------+
| [+ Create New Team]  [Search teams...]       |
+----------------------------------------------+
| ┌────────────────────────────────────────┐   |
| │ Marketing Team                          │   |
| │ 15 members · 28 documents               │   |
| │ [View Members] [View Documents] [Edit]  │   |
| └────────────────────────────────────────┘   |
| ┌────────────────────────────────────────┐   |
| │ Engineering                             │   |
| │ 8 members · 42 documents                │   |
| │ [View Members] [View Documents] [Edit]  │   |
| └────────────────────────────────────────┘   |
| ┌────────────────────────────────────────┐   |
| │ Executive                               │   |
| │ 3 members · 16 documents                │   |
| │ [View Members] [View Documents] [Edit]  │   |
| └────────────────────────────────────────┘   |
+----------------------------------------------+
```

## Conclusion

This implementation plan provides a comprehensive approach to enhancing Metis RAG with robust access control, document sharing, and permission management capabilities. By implementing these features, we'll create a more collaborative and secure environment that enables teams to share knowledge effectively while maintaining appropriate data boundaries.

The plan is structured into logical phases to enable incremental implementation and testing. Each phase builds on the previous one, ensuring a smooth progression from data model changes to backend implementation and finally to frontend enhancements.