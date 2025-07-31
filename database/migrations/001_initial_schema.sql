-- PostgreSQL Multi-Tenant Schema for Claude Platform
-- Optimized for Vercel PostgreSQL with Row-Level Security

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom types
CREATE TYPE user_role AS ENUM (
    'platform_admin',
    'account_owner', 
    'administrator',
    'property_manager',
    'front_desk',
    'maintenance',
    'security',
    'member',
    'company_admin',
    'company_user'
);

CREATE TYPE industry_module AS ENUM (
    'coworking',
    'government',
    'commercial_re',
    'hotel',
    'university',
    'creative',
    'residential'
);

CREATE TYPE lead_status AS ENUM (
    'new_inquiry',
    'tour_scheduled',
    'tour_completed',
    'converted',
    'closed'
);

CREATE TYPE page_status AS ENUM (
    'draft',
    'published',
    'archived'
);

-- Tenants table (no RLS - platform level)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    custom_domain VARCHAR(255),
    industry_module industry_module NOT NULL DEFAULT 'coworking',
    plan VARCHAR(50) NOT NULL DEFAULT 'starter',
    is_active BOOLEAN NOT NULL DEFAULT true,
    branding JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    feature_toggles JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for tenant lookup
CREATE INDEX idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX idx_tenants_custom_domain ON tenants(custom_domain) WHERE custom_domain IS NOT NULL;
CREATE INDEX idx_tenants_industry ON tenants(industry_module);
CREATE INDEX idx_tenants_active ON tenants(is_active) WHERE is_active = true;

-- Users table with tenant isolation
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role user_role NOT NULL DEFAULT 'member',
    is_active BOOLEAN NOT NULL DEFAULT true,
    company_id UUID,
    profile JSONB DEFAULT '{}',
    password_hash VARCHAR(255) NOT NULL,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT users_email_tenant_unique UNIQUE (tenant_id, email)
);

-- Enable RLS on users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- RLS policies for users
CREATE POLICY users_tenant_isolation ON users
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Optimized indexes for users
CREATE INDEX idx_users_tenant_email ON users(tenant_id, email);
CREATE INDEX idx_users_tenant_role ON users(tenant_id, role);
CREATE INDEX idx_users_tenant_active ON users(tenant_id, is_active) WHERE is_active = true;
CREATE INDEX idx_users_tenant_login ON users(tenant_id, last_login DESC NULLS LAST);
CREATE INDEX idx_users_company ON users(company_id) WHERE company_id IS NOT NULL;

-- Pages table for CMS
CREATE TABLE pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    content_blocks JSONB DEFAULT '[]',
    meta_title VARCHAR(255),
    meta_description TEXT,
    status page_status NOT NULL DEFAULT 'draft',
    template_id UUID,
    is_homepage BOOLEAN NOT NULL DEFAULT false,
    search_keywords TEXT, -- Extracted from content for full-text search
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT pages_slug_tenant_unique UNIQUE (tenant_id, slug)
);

-- Enable RLS on pages
ALTER TABLE pages ENABLE ROW LEVEL SECURITY;

-- RLS policy for pages
CREATE POLICY pages_tenant_isolation ON pages
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Optimized indexes for pages
CREATE INDEX idx_pages_tenant_slug ON pages(tenant_id, slug);
CREATE INDEX idx_pages_tenant_status ON pages(tenant_id, status);
CREATE INDEX idx_pages_tenant_homepage ON pages(tenant_id, is_homepage) WHERE is_homepage = true;
CREATE INDEX idx_pages_tenant_updated ON pages(tenant_id, updated_at DESC);
CREATE INDEX idx_pages_search ON pages USING gin(to_tsvector('english', search_keywords));

-- Forms table
CREATE TABLE forms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    fields JSONB NOT NULL DEFAULT '[]',
    success_message TEXT NOT NULL DEFAULT 'Thank you for your submission!',
    redirect_url VARCHAR(500),
    email_notifications TEXT[] DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS on forms
ALTER TABLE forms ENABLE ROW LEVEL SECURITY;

-- RLS policy for forms
CREATE POLICY forms_tenant_isolation ON forms
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Indexes for forms
CREATE INDEX idx_forms_tenant_active ON forms(tenant_id, is_active) WHERE is_active = true;
CREATE INDEX idx_forms_tenant_created ON forms(tenant_id, created_at DESC);

-- Leads table with partitioning by tenant for performance
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(255),
    status lead_status NOT NULL DEFAULT 'new_inquiry',
    source VARCHAR(255),
    notes TEXT,
    custom_fields JSONB DEFAULT '{}',
    assigned_to UUID REFERENCES users(id),
    tour_scheduled_at TIMESTAMPTZ,
    tour_completed_at TIMESTAMPTZ,
    converted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS on leads
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- RLS policy for leads
CREATE POLICY leads_tenant_isolation ON leads
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Optimized indexes for leads
CREATE INDEX idx_leads_tenant_email ON leads(tenant_id, email);
CREATE INDEX idx_leads_tenant_status ON leads(tenant_id, status);
CREATE INDEX idx_leads_tenant_assigned ON leads(tenant_id, assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX idx_leads_tenant_created ON leads(tenant_id, created_at DESC);
CREATE INDEX idx_leads_tenant_source ON leads(tenant_id, source);
CREATE INDEX idx_leads_tour_scheduled ON leads(tenant_id, tour_scheduled_at) WHERE tour_scheduled_at IS NOT NULL;

-- Form submissions table (partitioned by date for performance)
CREATE TABLE form_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    form_id UUID NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id),
    data JSONB NOT NULL,
    source_url VARCHAR(500),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for form submissions
CREATE TABLE form_submissions_2024_01 PARTITION OF form_submissions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE form_submissions_2024_02 PARTITION OF form_submissions
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- Add more partitions as needed

-- Enable RLS on form submissions
ALTER TABLE form_submissions ENABLE ROW LEVEL SECURITY;

-- RLS policy for form submissions (through form relationship)
CREATE POLICY form_submissions_tenant_isolation ON form_submissions
    FOR ALL
    USING (
        form_id IN (
            SELECT id FROM forms 
            WHERE tenant_id = current_setting('app.current_tenant_id')::UUID
        )
    );

-- Indexes for form submissions
CREATE INDEX idx_form_submissions_form ON form_submissions(form_id, created_at DESC);
CREATE INDEX idx_form_submissions_lead ON form_submissions(lead_id) WHERE lead_id IS NOT NULL;

-- Tours table
CREATE TABLE tours (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    staff_user_id UUID NOT NULL REFERENCES users(id),
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS on tours
ALTER TABLE tours ENABLE ROW LEVEL SECURITY;

-- RLS policy for tours
CREATE POLICY tours_tenant_isolation ON tours
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Indexes for tours
CREATE INDEX idx_tours_tenant_scheduled ON tours(tenant_id, scheduled_at);
CREATE INDEX idx_tours_tenant_staff ON tours(tenant_id, staff_user_id, scheduled_at);
CREATE INDEX idx_tours_lead ON tours(lead_id);
CREATE INDEX idx_tours_status ON tours(tenant_id, status);

-- Performance monitoring table
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id),
    metric_type VARCHAR(100) NOT NULL,
    value NUMERIC NOT NULL,
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (recorded_at);

-- Create daily partitions for performance metrics
CREATE TABLE performance_metrics_2024_01_01 PARTITION OF performance_metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-01-02');
-- Add more partitions as needed

-- Indexes for performance metrics
CREATE INDEX idx_performance_metrics_type_time ON performance_metrics(metric_type, recorded_at DESC);
CREATE INDEX idx_performance_metrics_tenant_time ON performance_metrics(tenant_id, recorded_at DESC) WHERE tenant_id IS NOT NULL;

-- Function to set tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_uuid::text, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current tenant
CREATE OR REPLACE FUNCTION get_current_tenant()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_tenant_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pages_updated_at BEFORE UPDATE ON pages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_forms_updated_at BEFORE UPDATE ON forms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tours_updated_at BEFORE UPDATE ON tours
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();