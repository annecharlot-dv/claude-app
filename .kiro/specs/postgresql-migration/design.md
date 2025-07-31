# PostgreSQL Migration Design Document

## Overview

This design document outlines the complete migration from MongoDB to PostgreSQL for the Claude Space-as-a-Service platform. The migration will transform the current document-based MongoDB architecture into a hybrid relational-document PostgreSQL architecture that leverages PostgreSQL's advanced features including JSONB fields, row-level security (RLS), full-text search, and the official Payload CMS PostgreSQL adapter.

The migration maintains the existing multi-tenant architecture while improving data consistency, query performance, and operational simplicity by consolidating to a single database technology.

## Architecture

### Database Architecture Transformation

**Current State (MongoDB):**
- Document-based storage with flexible schemas
- Manual tenant isolation through `tenant_id` fields
- Motor async driver with PyMongo
- Separate MongoDB instance for Payload CMS

**Target State (PostgreSQL):**
- Hybrid relational-document architecture using JSONB
- Row-level security (RLS) for automatic tenant isolation
- SQLAlchemy ORM with asyncpg driver
- Single PostgreSQL instance for both FastAPI and Payload CMS
- Advanced indexing and full-text search capabilities

### Multi-Tenant Isolation Strategy

PostgreSQL Row-Level Security (RLS) will replace manual tenant filtering:

```sql
-- Enable RLS on all tenant-specific tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for tenant isolation
CREATE POLICY tenant_isolation_users ON users
    FOR ALL TO application_role
    USING (tenant_id = current_setting('app.current_tenant_id'));

CREATE POLICY tenant_isolation_pages ON pages
    FOR ALL TO application_role
    USING (tenant_id = current_setting('app.current_tenant_id'));
```

## Components and Interfaces

### 1. Database Layer Migration

#### SQLAlchemy Models
Replace Pydantic models with SQLAlchemy ORM models that support both relational and JSONB fields:

```python
# backend/models/postgresql_models.py
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Tenant(Base):
    __tablename__ = 'tenants'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    subdomain = Column(String(50), unique=True, nullable=False, index=True)
    industry_module = Column(String(50), nullable=False, index=True)
    plan = Column(String(20), default='starter')
    is_active = Column(Boolean, default=True, index=True)
    
    # JSONB fields for flexible data
    branding = Column(JSONB, default={})
    settings = Column(JSONB, default={})
    feature_toggles = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # JSONB for flexible profile data
    profile = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    __table_args__ = (
        # Unique constraint on email per tenant
        UniqueConstraint('email', 'tenant_id', name='unique_email_per_tenant'),
    )
```

#### Database Connection Management
Replace Motor with SQLAlchemy + asyncpg:

```python
# backend/database/postgresql_connection.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os

class PostgreSQLConnection:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.engine = create_async_engine(
            self.database_url,
            poolclass=NullPool,  # Use connection pooling
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL debugging
        )
        
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session
    
    async def set_tenant_context(self, session: AsyncSession, tenant_id: str):
        """Set tenant context for RLS"""
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
            {"tenant_id": tenant_id}
        )
```

### 2. Kernel System Migration

#### Updated Base Kernel
Modify base kernel to use SQLAlchemy instead of MongoDB:

```python
# backend/kernels/postgresql_base_kernel.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod

class PostgreSQLBaseKernel(ABC):
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_record(self, model_class: Type, data: Dict[str, Any]):
        """Generic record creation"""
        record = model_class(**data)
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record
    
    async def get_by_id(self, model_class: Type, record_id: str):
        """Generic record retrieval by ID"""
        result = await self.db.execute(
            select(model_class).where(model_class.id == record_id)
        )
        return result.scalar_one_or_none()
    
    async def update_record(self, model_class: Type, record_id: str, updates: Dict[str, Any]):
        """Generic record update"""
        await self.db.execute(
            update(model_class)
            .where(model_class.id == record_id)
            .values(**updates)
        )
        await self.db.commit()
```

#### Identity Kernel Migration
Update identity kernel for PostgreSQL:

```python
# backend/kernels/postgresql_identity_kernel.py
from kernels.postgresql_base_kernel import PostgreSQLBaseKernel
from models.postgresql_models import User, Tenant, UserPassword
from sqlalchemy import select, and_
from passlib.context import CryptContext
import jwt

class PostgreSQLIdentityKernel(PostgreSQLBaseKernel):
    def __init__(self, db_session, secret_key: str):
        super().__init__(db_session)
        self.secret_key = secret_key
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def authenticate_user(self, tenant_subdomain: str, email: str, password: str):
        """Authenticate user with PostgreSQL"""
        # Find tenant
        tenant_result = await self.db.execute(
            select(Tenant).where(Tenant.subdomain == tenant_subdomain)
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            return None
        
        # Set tenant context for RLS
        await self.set_tenant_context(str(tenant.id))
        
        # Find user
        user_result = await self.db.execute(
            select(User).where(
                and_(User.email == email, User.is_active == True)
            )
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return None
        
        # Verify password
        password_result = await self.db.execute(
            select(UserPassword).where(UserPassword.user_id == user.id)
        )
        password_record = password_result.scalar_one_or_none()
        
        if not password_record or not self.pwd_context.verify(password, password_record.hashed_password):
            return None
        
        return {"user": user, "tenant": tenant}
```

### 3. Payload CMS Integration

#### PostgreSQL Adapter Configuration
Update Payload CMS to use PostgreSQL adapter:

```typescript
// payload.config.ts (Updated)
import { postgresAdapter } from '@payloadcms/db-postgres';

export default buildConfig({
  db: postgresAdapter({
    pool: {
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
      max: 20,
      min: 5,
      idle: 10000,
      acquire: 60000,
      evict: 1000,
    },
    prodMigrations: path.resolve(__dirname, 'database/migrations'),
    migrationDir: path.resolve(__dirname, 'database/migrations'),
    transactionOptions: {
      isolationLevel: 'READ_COMMITTED',
      readOnly: false,
    },
  }),
  // ... rest of configuration
});
```

#### Collection Schema Updates
Leverage PostgreSQL features in Payload collections:

```typescript
// Enhanced collections with PostgreSQL features
const Users = {
  slug: 'users',
  fields: [
    {
      name: 'tenantId',
      type: 'text',
      required: true,
      index: true,
      // Use PostgreSQL UUID type
      admin: {
        hidden: true,
      },
    },
    {
      name: 'profile',
      type: 'json', // Maps to JSONB in PostgreSQL
      admin: {
        description: 'Flexible user profile data stored as JSONB',
      },
    },
    {
      name: 'searchVector',
      type: 'text',
      admin: {
        hidden: true,
        description: 'PostgreSQL full-text search vector',
      },
    },
  ],
  hooks: {
    beforeChange: [
      ({ data, req }) => {
        // Generate search vector for full-text search
        if (data.firstName || data.lastName || data.email) {
          data.searchVector = `${data.firstName || ''} ${data.lastName || ''} ${data.email || ''}`.toLowerCase();
        }
        return data;
      },
    ],
  },
};
```

## Data Models

### Schema Migration Strategy

#### 1. Document to Relational Mapping

**MongoDB Document Structure:**
```javascript
{
  _id: ObjectId,
  tenant_id: "uuid",
  email: "user@example.com",
  profile: {
    preferences: {...},
    custom_fields: {...}
  },
  created_at: ISODate
}
```

**PostgreSQL Table Structure:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    profile JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    
    CONSTRAINT unique_email_per_tenant UNIQUE (email, tenant_id)
);

-- Indexes for performance
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_profile_gin ON users USING GIN (profile);
```

#### 2. JSONB Field Usage

Use JSONB for flexible, document-style data while maintaining relational integrity:

- **Tenant Settings**: Store configuration as JSONB
- **User Profiles**: Store custom fields and preferences
- **Page Content**: Store dynamic content blocks
- **Form Configurations**: Store field definitions and validation rules

#### 3. Full-Text Search Implementation

```sql
-- Add full-text search capabilities
ALTER TABLE pages ADD COLUMN search_vector tsvector;

-- Create search index
CREATE INDEX idx_pages_search ON pages USING GIN (search_vector);

-- Update search vector trigger
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.title, '') || ' ' || 
        COALESCE(NEW.meta_description, '') || ' ' ||
        COALESCE(NEW.content_blocks::text, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pages_search_vector
    BEFORE INSERT OR UPDATE ON pages
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

## Error Handling

### Database Connection Errors
```python
# backend/database/error_handling.py
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException
import logging

class DatabaseErrorHandler:
    @staticmethod
    async def handle_database_error(error: Exception):
        if isinstance(error, IntegrityError):
            if "unique_email_per_tenant" in str(error):
                raise HTTPException(status_code=400, detail="Email already exists for this tenant")
            elif "subdomain" in str(error):
                raise HTTPException(status_code=400, detail="Subdomain already taken")
        
        logging.error(f"Database error: {error}")
        raise HTTPException(status_code=500, detail="Database operation failed")
```

### Migration Error Recovery
```python
# backend/migration/error_recovery.py
class MigrationErrorRecovery:
    def __init__(self, db_session):
        self.db = db_session
    
    async def rollback_migration_batch(self, batch_id: str):
        """Rollback a failed migration batch"""
        await self.db.execute(
            text("DELETE FROM migration_log WHERE batch_id = :batch_id"),
            {"batch_id": batch_id}
        )
        await self.db.commit()
    
    async def verify_data_integrity(self) -> Dict[str, Any]:
        """Verify data integrity after migration"""
        checks = {
            "tenant_count": await self.count_records("tenants"),
            "user_count": await self.count_records("users"),
            "page_count": await self.count_records("pages"),
            "orphaned_users": await self.count_orphaned_records("users", "tenants", "tenant_id"),
        }
        return checks
```

## Testing Strategy

### Unit Testing with PostgreSQL
```python
# tests/test_postgresql_kernels.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.models.postgresql_models import Base
from backend.kernels.postgresql_identity_kernel import PostgreSQLIdentityKernel

@pytest.fixture
async def test_db():
    """Create test database session"""
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test_db")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_user_authentication(test_db):
    """Test user authentication with PostgreSQL"""
    identity_kernel = PostgreSQLIdentityKernel(test_db, "test-secret")
    
    # Create test tenant and user
    tenant_data = {
        "name": "Test Tenant",
        "subdomain": "test",
        "industry_module": "coworking"
    }
    tenant = await identity_kernel.create_tenant(tenant_data)
    
    user_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "member"
    }
    user = await identity_kernel.create_user(str(tenant.id), user_data, "password123")
    
    # Test authentication
    auth_result = await identity_kernel.authenticate_user("test", "test@example.com", "password123")
    assert auth_result is not None
    assert auth_result["user"].email == "test@example.com"
```

### Integration Testing
```python
# tests/test_postgresql_integration.py
@pytest.mark.asyncio
async def test_tenant_isolation_with_rls():
    """Test that RLS properly isolates tenant data"""
    # Create two tenants with users
    tenant1 = await create_test_tenant("tenant1")
    tenant2 = await create_test_tenant("tenant2")
    
    user1 = await create_test_user(tenant1.id, "user1@tenant1.com")
    user2 = await create_test_user(tenant2.id, "user2@tenant2.com")
    
    # Set tenant context for tenant1
    await set_tenant_context(str(tenant1.id))
    
    # Query users - should only return tenant1 users
    users = await get_all_users()
    assert len(users) == 1
    assert users[0].email == "user1@tenant1.com"
```

### Performance Testing
```python
# tests/test_postgresql_performance.py
@pytest.mark.asyncio
async def test_query_performance():
    """Test query performance with PostgreSQL indexes"""
    # Create test data
    await create_test_tenants(100)
    await create_test_users_per_tenant(1000)
    
    # Test indexed queries
    start_time = time.time()
    users = await search_users_by_email("test@example.com")
    query_time = time.time() - start_time
    
    assert query_time < 0.1  # Should complete in under 100ms
    assert len(users) > 0
```

## Migration Implementation Plan

### Phase 1: Infrastructure Setup
1. Install PostgreSQL dependencies
2. Create database schema and migrations
3. Set up connection pooling and RLS policies
4. Configure Payload CMS with PostgreSQL adapter

### Phase 2: Core System Migration
1. Migrate tenant and user management
2. Update authentication and authorization
3. Migrate CMS and content management
4. Update API endpoints and middleware

### Phase 3: Data Migration
1. Create data migration scripts
2. Implement batch migration with error handling
3. Verify data integrity and completeness
4. Update search indexes and full-text search

### Phase 4: Testing and Optimization
1. Run comprehensive test suite
2. Performance testing and optimization
3. Load testing with realistic data volumes
4. Security testing of RLS policies

This design provides a comprehensive roadmap for migrating from MongoDB to PostgreSQL while maintaining all existing functionality and improving performance, data consistency, and operational simplicity.