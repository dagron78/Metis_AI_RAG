import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, 
    DateTime, ForeignKey, JSON, Table, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref

from app.db.session import Base

# Association table for document-tag many-to-many relationship
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', UUID(as_uuid=True), ForeignKey('documents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('added_at', DateTime, default=datetime.utcnow)
)

class Document(Base):
    """Document model for database"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=True)  # Can be null if we only store metadata
    doc_metadata = Column(JSONB, default={})  # Renamed from 'metadata' to 'doc_metadata'
    folder = Column(String, ForeignKey('folders.path'), default="/")
    uploaded = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    processing_strategy = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    is_public = Column(Boolean, default=False)  # Whether the document is publicly accessible
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=True)

    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=document_tags, back_populates="documents")
    folder_rel = relationship("Folder", back_populates="documents")
    citations = relationship("Citation", back_populates="document")
    user = relationship("User", back_populates="documents")
    shared_with = relationship("DocumentPermission", back_populates="document", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="documents")

    # Indexes
    __table_args__ = (
        Index('ix_documents_filename', filename),
        Index('ix_documents_folder', folder),
        Index('ix_documents_processing_status', processing_status),
        Index('ix_documents_is_public', is_public),
        Index('ix_documents_organization_id', organization_id),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"


class DocumentPermission(Base):
    """Document permission model for database"""
    __tablename__ = "document_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    permission_level = Column(String, nullable=False)  # 'read', 'write', 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="shared_with")
    user = relationship("User", back_populates="document_permissions")

    # Indexes and constraints
    __table_args__ = (
        Index('ix_document_permissions_document_id', document_id),
        Index('ix_document_permissions_user_id', user_id),
        UniqueConstraint('document_id', 'user_id', name='uq_document_permissions_document_user'),
    )

    def __repr__(self):
        return f"<DocumentPermission(document_id={self.document_id}, user_id={self.user_id}, level='{self.permission_level}')>"


class Chunk(Base):
    """Chunk model for database"""
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False)
    content = Column(Text, nullable=False)
    chunk_metadata = Column(JSONB, default={})  # Renamed from 'metadata' to 'chunk_metadata'
    index = Column(Integer, nullable=False)  # Position in the document
    embedding_quality = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    citations = relationship("Citation", back_populates="chunk")

    # Indexes
    __table_args__ = (
        Index('ix_chunks_document_id', document_id),
        Index('ix_chunks_document_id_index', document_id, index),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.index})>"


class Tag(Base):
    """Tag model for database"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)

    # Relationships
    documents = relationship("Document", secondary=document_tags, back_populates="tags")

    # Indexes
    __table_args__ = (
        Index('ix_tags_name', name),
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


class Folder(Base):
    """Folder model for database"""
    __tablename__ = "folders"

    path = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    parent_path = Column(String, ForeignKey('folders.path'), nullable=True)
    document_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="folder_rel")
    subfolders = relationship("Folder",
                             backref=backref("parent", remote_side=[path]),
                             cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_folders_parent_path', parent_path),
    )

    def __repr__(self):
        return f"<Folder(path='{self.path}', name='{self.name}')>"


class Conversation(Base):
    """Conversation model for database"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    conv_metadata = Column(JSONB, default={})  # Renamed from 'metadata' to 'conv_metadata'
    message_count = Column(Integer, default=0)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", back_populates="conversations")

    # Indexes
    __table_args__ = (
        Index('ix_conversations_created_at', created_at),
        Index('ix_conversations_updated_at', updated_at),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, message_count={self.message_count})>"


class Message(Base):
    """Message model for database"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    timestamp = Column(DateTime, default=datetime.utcnow)
    token_count = Column(Integer, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_messages_conversation_id', conversation_id),
        Index('ix_messages_timestamp', timestamp),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"


class Citation(Base):
    """Citation model for database"""
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('messages.id'), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=True)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey('chunks.id'), nullable=True)
    relevance_score = Column(Float, nullable=True)
    excerpt = Column(Text, nullable=True)
    character_range_start = Column(Integer, nullable=True)
    character_range_end = Column(Integer, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="citations")
    document = relationship("Document", back_populates="citations")
    chunk = relationship("Chunk", back_populates="citations")

    # Indexes
    __table_args__ = (
        Index('ix_citations_message_id', message_id),
        Index('ix_citations_document_id', document_id),
        Index('ix_citations_chunk_id', chunk_id),
    )

    def __repr__(self):
        return f"<Citation(id={self.id}, message_id={self.message_id}, document_id={self.document_id})>"


class ProcessingJob(Base):
    """Processing job model for database"""
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    document_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    strategy = Column(String, nullable=True)
    job_metadata = Column(JSONB, default={})  # Renamed from 'metadata' to 'job_metadata'
    progress_percentage = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index('ix_processing_jobs_status', status),
        Index('ix_processing_jobs_created_at', created_at),
    )

    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, status='{self.status}', progress={self.progress_percentage}%)>"


class AnalyticsQuery(Base):
    """Analytics query model for database"""
    __tablename__ = "analytics_queries"

    id = Column(Integer, primary_key=True)
    query = Column(Text, nullable=False)
    model = Column(String, nullable=True)
    use_rag = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    document_id_list = Column(JSONB, default=[])  # Renamed from 'document_ids' to 'document_id_list'
    query_type = Column(String, nullable=True)  # simple, complex, agentic
    successful = Column(Boolean, default=True)

    # Indexes
    __table_args__ = (
        Index('ix_analytics_queries_timestamp', timestamp),
        Index('ix_analytics_queries_model', model),
        Index('ix_analytics_queries_query_type', query_type),
    )

    def __repr__(self):
        return f"<AnalyticsQuery(id={self.id}, query_type='{self.query_type}', response_time={self.response_time_ms}ms)>"


class Organization(Base):
    """Organization model for database"""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    settings = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization")

    # Indexes
    __table_args__ = (
        Index('ix_organizations_name', name),
    )

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"


class OrganizationMember(Base):
    """Organization member model for database"""
    __tablename__ = "organization_members"

    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role = Column(String, nullable=False)  # 'owner', 'admin', 'member'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organizations")

    # Indexes
    __table_args__ = (
        Index('ix_organization_members_organization_id', organization_id),
        Index('ix_organization_members_user_id', user_id),
    )

    def __repr__(self):
        return f"<OrganizationMember(organization_id={self.organization_id}, user_id={self.user_id}, role='{self.role}')>"


class User(Base):
    """User model for database"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    user_metadata = Column('metadata', JSONB, default={})  # Map user_metadata attribute to 'metadata' column

    # Relationships
    documents = relationship("Document", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    document_permissions = relationship("DocumentPermission", back_populates="user", cascade="all, delete-orphan")
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    organizations = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_users_username', username),
        Index('ix_users_email', email),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Role(Base):
    """Role model for database"""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    permissions = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_roles_name', name),
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class UserRole(Base):
    """User-role association model for database"""
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")

    # Indexes
    __table_args__ = (
        Index('ix_user_roles_user_id', user_id),
        Index('ix_user_roles_role_id', role_id),
    )

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class PasswordResetToken(Base):
    """Password reset token model for database"""
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    token = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")

    # Indexes
    __table_args__ = (
        Index('ix_password_reset_tokens_token', token),
        Index('ix_password_reset_tokens_user_id', user_id),
        Index('ix_password_reset_tokens_expires_at', expires_at),
    )

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, is_used={self.is_used})>"


class Notification(Base):
    """Notification model for database"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = Column(String, nullable=False)  # e.g., 'document_shared', 'mention', 'system'
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSONB, default={})
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    # Indexes
    __table_args__ = (
        Index('ix_notifications_user_id', user_id),
        Index('ix_notifications_created_at', created_at),
        Index('ix_notifications_is_read', is_read),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}')>"


class BackgroundTask(Base):
    """Background task model for database"""
    __tablename__ = "background_tasks"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    params = Column(JSONB, nullable=True)
    priority = Column(Integer, nullable=True, default=50)
    dependencies = Column(Text, nullable=True)
    schedule_time = Column(DateTime, nullable=True)
    timeout_seconds = Column(Integer, nullable=True)
    max_retries = Column(Integer, nullable=True, default=0)
    task_metadata = Column(JSONB, nullable=True)  # Renamed from 'metadata' to 'task_metadata'
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, nullable=True, default=0)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    progress = Column(Float, nullable=True, default=0.0)
    resource_usage = Column(JSONB, nullable=True)
    execution_time_ms = Column(Float, nullable=True)

    # Indexes
    __table_args__ = (
        Index('ix_background_tasks_status', status),
        Index('ix_background_tasks_task_type', task_type),
        Index('ix_background_tasks_created_at', created_at),
        Index('ix_background_tasks_schedule_time', schedule_time),
    )

    def __repr__(self):
        return f"<BackgroundTask(id={self.id}, name='{self.name}', status='{self.status}')>"