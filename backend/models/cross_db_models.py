"""
Cross-Database SQLAlchemy Models
Compatible with both PostgreSQL and SQLite for development
"""

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import TSVECTOR as TSVectorType
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

Base = declarative_base()


# Cross-database JSON type
class CrossDBJSON(TypeDecorator):
    """JSON type that works with both PostgreSQL and SQLite"""

    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


# Cross-database UUID type
class CrossDBUUID(TypeDecorator):
    """UUID type that works with both PostgreSQL and SQLite"""

    impl = String

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))


# Cross-database TSVector type
class CrossDBTSVector(TypeDecorator):
    """TSVector type that works with both PostgreSQL and SQLite"""

    impl = Text

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(TSVectorType)
        else:
            return dialect.type_descriptor(Text())


class Tenant(Base):
    """Tenant model with cross-database compatibility"""

    __tablename__ = "tenants"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    subdomain = Column(String(50), unique=True, nullable=False, index=True)
    custom_domain = Column(String(255), index=True)
    industry_module = Column(String(50), nullable=False, index=True)
    plan = Column(String(20), default="starter", index=True)
    is_active = Column(Boolean, default=True, index=True)

    # JSON fields for flexible data
    branding = Column(CrossDBJSON, default=lambda: {})
    settings = Column(CrossDBJSON, default=lambda: {})
    feature_toggles = Column(CrossDBJSON, default=lambda: {})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="tenant", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")
    forms = relationship("Form", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """User model with cross-database compatibility"""

    __tablename__ = "users"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(
        CrossDBUUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    company_id = Column(String(100), index=True)

    # Password stored separately for security
    hashed_password = Column(String(255), nullable=False)

    # JSON field for flexible profile data
    profile = Column(CrossDBJSON, default=lambda: {})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    assigned_leads = relationship("Lead", back_populates="assigned_user")

    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_email"),
        Index("idx_users_tenant_role_active", "tenant_id", "role", "is_active"),
    )


class Page(Base):
    """Page model with cross-database compatibility"""

    __tablename__ = "pages"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(
        CrossDBUUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    title = Column(String(200), nullable=False)
    slug = Column(String(100), nullable=False, index=True)

    # Content stored as JSON for flexibility
    content_blocks = Column(CrossDBJSON, default=lambda: [])

    # SEO fields
    meta_title = Column(String(200))
    meta_description = Column(Text)

    # Status and settings
    status = Column(String(20), default="draft", index=True)
    template_id = Column(String(100))
    is_homepage = Column(Boolean, default=False, index=True)

    # Full-text search
    search_keywords = Column(Text)
    search_vector = Column(CrossDBTSVector)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="pages")

    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_tenant_slug"),
        Index("idx_pages_tenant_status", "tenant_id", "status"),
    )


class Lead(Base):
    """Lead model with cross-database compatibility"""

    __tablename__ = "leads"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(
        CrossDBUUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    company = Column(String(200))

    # Lead management
    status = Column(String(50), default="new_inquiry", index=True)
    source = Column(String(100), index=True)
    notes = Column(Text)
    assigned_to = Column(CrossDBUUID(), ForeignKey("users.id"), index=True)

    # Custom fields as JSON
    custom_fields = Column(CrossDBJSON, default=lambda: {})

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

    # Constraints
    __table_args__ = (
        Index("idx_leads_tenant_status", "tenant_id", "status"),
        Index("idx_leads_tenant_email", "tenant_id", "email"),
    )


class Form(Base):
    """Form model with cross-database compatibility"""

    __tablename__ = "forms"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(
        CrossDBUUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Form configuration as JSON
    fields = Column(CrossDBJSON, default=lambda: [])

    # Settings
    success_message = Column(Text, default="Thank you for your submission!")
    redirect_url = Column(String(500))
    email_notifications = Column(CrossDBJSON, default=lambda: [])
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="forms")
    submissions = relationship("FormSubmission", back_populates="form")


class FormSubmission(Base):
    """Form submission model with cross-database compatibility"""

    __tablename__ = "form_submissions"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id = Column(CrossDBUUID(), ForeignKey("forms.id"), nullable=False, index=True)
    lead_id = Column(CrossDBUUID(), ForeignKey("leads.id"), index=True)

    # Submission data as JSON
    data = Column(CrossDBJSON, default=lambda: {})

    # Metadata
    source_url = Column(String(500))
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    form = relationship("Form", back_populates="submissions")
    lead = relationship("Lead", back_populates="form_submissions")


class Template(Base):
    """Template model with cross-database compatibility"""

    __tablename__ = "templates"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    industry_module = Column(String(50), nullable=False, index=True)
    preview_image = Column(String(500))

    # Template configuration as JSON
    layout_config = Column(CrossDBJSON, default=lambda: {})
    default_content = Column(CrossDBJSON, default=lambda: {})

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Widget(Base):
    """Widget model with cross-database compatibility"""

    __tablename__ = "widgets"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(
        CrossDBUUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False, index=True)

    # Widget configuration as JSON
    config = Column(CrossDBJSON, default=lambda: {})

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TourSlot(Base):
    """Tour slot model with cross-database compatibility"""

    __tablename__ = "tour_slots"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(
        CrossDBUUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    staff_user_id = Column(CrossDBUUID(), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    max_bookings = Column(Integer, default=1)
    is_available = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Tour(Base):
    """Tour model with cross-database compatibility"""

    __tablename__ = "tours"

    id = Column(CrossDBUUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(
        CrossDBUUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )
    lead_id = Column(CrossDBUUID(), ForeignKey("leads.id"), nullable=False)
    tour_slot_id = Column(CrossDBUUID(), ForeignKey("tour_slots.id"), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    staff_user_id = Column(CrossDBUUID(), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="scheduled", index=True)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
