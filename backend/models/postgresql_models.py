"""
SQLAlchemy Models for PostgreSQL
Replaces Pydantic models with proper relational models
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID, TSVECTOR as TSVectorType
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint, Index
import uuid
from datetime import datetime

Base = declarative_base()

# Cross-database JSON type
class CrossDBJSON(TypeDecorator):
    """JSON type that works with both PostgreSQL and SQLite"""
    impl = JSON
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

# Cross-database UUID type  
class CrossDBUUID(TypeDecorator):
    """UUID type that works with both PostgreSQL and SQLite"""
    impl = String
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

# Cross-database TSVector type
class CrossDBTSVector(TypeDecorator):
    """TSVector type that works with both PostgreSQL and SQLite"""
    impl = Text
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(TSVectorType)
        else:
            return dialect.type_descriptor(Text())

class Tenant(Base):
    """Tenant model with PostgreSQL optimizations"""
    __tablename__ = 'tenants'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    subdomain = Column(String(50), unique=True, nullable=False, index=True)
    custom_domain = Column(String(255), index=True)
    industry_module = Column(String(50), nullable=False, index=True)
    plan = Column(String(20), default='starter', index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # JSONB fields for flexible data
    branding = Column(JSONB, default={})
    settings = Column(JSONB, default={})
    feature_toggles = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="tenant", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    forms = relationship("Form", back_populates="tenant", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_tenants_subdomain', 'subdomain'),
        Index('idx_tenants_industry_active', 'industry_module', 'is_active'),
        Index('idx_tenants_branding_gin', 'branding', postgresql_using='gin'),
        Index('idx_tenants_settings_gin', 'settings', postgresql_using='gin'),
    )

class User(Base):
    """User model with tenant isolation"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    company_id = Column(String(100), index=True)
    
    # JSONB for flexible profile data
    profile = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    assigned_leads = relationship("Lead", back_populates="assigned_user")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', name='unique_email_per_tenant'),
        Index('idx_users_tenant_email', 'tenant_id', 'email'),
        Index('idx_users_role_active', 'role', 'is_active'),
        Index('idx_users_profile_gin', 'profile', postgresql_using='gin'),
    )

class UserPassword(Base):
    """Separate table for password hashes"""
    __tablename__ = 'user_passwords'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Page(Base):
    """Page model for CMS"""
    __tablename__ = 'pages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    meta_title = Column(String(255))
    meta_description = Column(Text)
    status = Column(String(20), default='draft', index=True)
    template_id = Column(String(100))
    is_homepage = Column(Boolean, default=False, index=True)
    
    # JSONB for content blocks
    content_blocks = Column(JSONB, default=[])
    
    # Full-text search
    search_keywords = Column(Text)
    search_vector = Column(TSVectorType)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="pages")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('slug', 'tenant_id', name='unique_slug_per_tenant'),
        Index('idx_pages_tenant_status', 'tenant_id', 'status'),
        Index('idx_pages_search_gin', 'search_vector', postgresql_using='gin'),
        Index('idx_pages_content_gin', 'content_blocks', postgresql_using='gin'),
    )

class Lead(Base):
    """Lead model for lead management"""
    __tablename__ = 'leads'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    company = Column(String(255))
    status = Column(String(50), default='new_inquiry', index=True)
    source = Column(String(100), index=True)
    notes = Column(Text)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'), index=True)
    
    # JSONB for custom fields
    custom_fields = Column(JSONB, default={})
    
    # Tour scheduling
    tour_scheduled_at = Column(DateTime(timezone=True))
    tour_completed_at = Column(DateTime(timezone=True))
    converted_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="leads")
    assigned_user = relationship("User", back_populates="assigned_leads")
    form_submissions = relationship("FormSubmission", back_populates="lead")
    
    # Indexes
    __table_args__ = (
        Index('idx_leads_tenant_email', 'tenant_id', 'email'),
        Index('idx_leads_status_created', 'status', 'created_at'),
        Index('idx_leads_custom_fields_gin', 'custom_fields', postgresql_using='gin'),
    )

class Form(Base):
    """Form model for lead capture"""
    __tablename__ = 'forms'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    success_message = Column(Text, default="Thank you for your submission!")
    redirect_url = Column(String(500))
    is_active = Column(Boolean, default=True, index=True)
    
    # JSONB for form fields and configuration
    fields = Column(JSONB, default=[])
    email_notifications = Column(JSONB, default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="forms")
    submissions = relationship("FormSubmission", back_populates="form")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('name', 'tenant_id', name='unique_form_name_per_tenant'),
        Index('idx_forms_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_forms_fields_gin', 'fields', postgresql_using='gin'),
    )

class FormSubmission(Base):
    """Form submission model"""
    __tablename__ = 'form_submissions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id = Column(UUID(as_uuid=True), ForeignKey('forms.id'), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('leads.id'), index=True)
    
    # Submission data
    data = Column(JSONB, nullable=False)
    source_url = Column(String(500))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    form = relationship("Form", back_populates="submissions")
    lead = relationship("Lead", back_populates="form_submissions")
    
    # Indexes
    __table_args__ = (
        Index('idx_form_submissions_form_created', 'form_id', 'created_at'),
        Index('idx_form_submissions_data_gin', 'data', postgresql_using='gin'),
    )

class Template(Base):
    """Template model for page templates"""
    __tablename__ = 'templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    industry_module = Column(String(50), nullable=False, index=True)
    preview_image = Column(String(500))
    is_active = Column(Boolean, default=True, index=True)
    
    # JSONB for template configuration
    layout_config = Column(JSONB, default={})
    default_content = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_templates_industry_active', 'industry_module', 'is_active'),
        Index('idx_templates_layout_gin', 'layout_config', postgresql_using='gin'),
    )

class Widget(Base):
    """Widget model for page widgets"""
    __tablename__ = 'widgets'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # JSONB for widget configuration
    config = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_widgets_tenant_type', 'tenant_id', 'type'),
        Index('idx_widgets_config_gin', 'config', postgresql_using='gin'),
    )

class TourSlot(Base):
    """Tour slot model for scheduling"""
    __tablename__ = 'tour_slots'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    staff_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    max_bookings = Column(Integer, default=1)
    current_bookings = Column(Integer, default=0)
    is_available = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_tour_slots_tenant_date', 'tenant_id', 'date'),
        Index('idx_tour_slots_staff_available', 'staff_user_id', 'is_available'),
    )

class Tour(Base):
    """Tour booking model"""
    __tablename__ = 'tours'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('leads.id'), nullable=False, index=True)
    tour_slot_id = Column(UUID(as_uuid=True), ForeignKey('tour_slots.id'), nullable=False, index=True)
    staff_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default='scheduled', index=True)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_tours_tenant_scheduled', 'tenant_id', 'scheduled_at'),
        Index('idx_tours_status_created', 'status', 'created_at'),
    )