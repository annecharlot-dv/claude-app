# Claude App - Platform Architecture Guide
*A Multi-Tenant SaaS Platform for Universal Space Management*

## 🎯 **Executive Summary**

Claude App is a **platform-first, multi-tenant SaaS solution** designed to serve as the universal foundation for space management across any industry. Rather than building industry-specific solutions, we prioritize a robust, scalable platform that can be configured and customized for coworking spaces, hotels, government facilities, universities, residential buildings, and any other space-based business model.

### **Platform-First Philosophy**
- **Foundation First**: Build rock-solid SaaS infrastructure before industry features
- **Configuration Over Customization**: Industry differences handled through configuration, not code forks
- **Universal Core**: All industries share the same booking, user management, and billing systems
- **Scalable Architecture**: Single platform serves unlimited tenants across all verticals

### **Architectural Evolution**
*Note: The original specifications planned for a Next.js/TypeScript full-stack approach, but we've pivoted to a more pragmatic multi-service architecture that better serves our platform-first goals while maintaining development velocity.*

---

## 🏗️ **Current Platform Architecture**

### **Technology Stack**

#### **Backend Foundation**
- **Framework**: FastAPI (Python) with async/await support
- **Database**: PostgreSQL 15+ with row-level security for tenant isolation
- **ORM**: SQLAlchemy with Alembic migrations
- **Authentication**: JWT tokens with bcrypt password hashing
- **Caching**: Redis for session management and performance optimization (planned)
- **Task Queue**: Celery with Redis broker for background processing (planned)

#### **Frontend Platform**
- **Framework**: React 18 with modern hooks and context
- **State Management**: React Query (@tanstack/react-query) for server state
- **Routing**: React Router DOM with protected routes
- **Styling**: Tailwind CSS with component library
- **Build Tool**: Create React App with CRACO customization
- **Performance**: Code splitting, lazy loading, bundle optimization

#### **Content Management**
- **CMS**: PayloadCMS v3 with TypeScript configuration
- **Database Adapter**: PostgreSQL adapter for unified data layer
- **Rich Text**: Slate editor for content creation
- **Multi-language**: Built-in localization support (en, es, fr, de)
- **File Management**: Optimized uploads with size limits and CDN integration

#### **Infrastructure & DevOps**
- **Deployment**: Vercel with multi-environment support (staging/production)
- **Database Hosting**: PostgreSQL with connection pooling
- **File Storage**: Vercel Blob (development) → Cloudflare R2 (production)
- **Monitoring**: Custom performance tracking and health checks
- **CI/CD**: GitHub Actions with comprehensive testing pipeline

#### **Current Architecture Benefits**
- **Separation of Concerns**: FastAPI handles business logic, React handles UI, PayloadCMS handles content
- **Technology Expertise**: Leverage Python ecosystem for backend, React ecosystem for frontend
- **Deployment Flexibility**: Each service can be optimized and scaled independently
- **Development Velocity**: Teams can work on different services simultaneously

---

## 🏢 **Multi-Tenant Platform Foundation**

### **Tenant Isolation Strategy**

#### **Database-Level Isolation**
```sql
-- Core tenant table
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  subdomain VARCHAR(63) UNIQUE NOT NULL,
  custom_domain VARCHAR(253),
  plan_tier VARCHAR(50) DEFAULT 'basic',
  industry_type VARCHAR(50) DEFAULT 'general',
  settings JSONB DEFAULT '{}',
  features JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Row-Level Security for all tenant data
CREATE POLICY tenant_isolation ON members
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- All tables include tenant_id with automatic filtering
CREATE TABLE members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email VARCHAR(320) NOT NULL,
  profile JSONB DEFAULT '{}',
  role VARCHAR(50) DEFAULT 'member',
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **Application-Level Tenant Context**
```python
# Tenant middleware for request processing
class TenantMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract tenant from subdomain or custom domain
        hostname = request.headers.get("host", "")
        tenant = await self.resolve_tenant(hostname)
        
        # Set tenant context for database queries
        request.state.tenant_id = tenant.id
        request.state.tenant = tenant
        
        response = await call_next(request)
        return response

# Database client with tenant context
async def get_tenant_db(tenant_id: str):
    await database.execute(
        "SELECT set_config('app.current_tenant', :tenant_id, true)",
        {"tenant_id": tenant_id}
    )
    return database
```

### **Domain Management**
- **Subdomain Routing**: `client1.claude-app.com`, `client2.claude-app.com`
- **Custom Domains**: `members.clientspace.com` → platform infrastructure
- **SSL Management**: Automatic certificate provisioning
- **CDN Integration**: Global content delivery with edge caching

---

## 🔧 **Core Platform Components**

### **1. Authentication & Authorization System**

#### **Multi-Level User Hierarchy**
```python
class UserRole(Enum):
    # Platform Level (SaaS Management)
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_SUPPORT = "platform_support"
    
    # Tenant Level (Space Management)
    TENANT_OWNER = "tenant_owner"
    TENANT_ADMIN = "tenant_admin"
    TENANT_MANAGER = "tenant_manager"
    TENANT_STAFF = "tenant_staff"
    
    # Client Level (Space Users)
    MEMBER = "member"
    GUEST = "guest"

class User(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    role: UserRole
    permissions: List[str]
    profile: Dict[str, Any]
    is_active: bool
    last_login: Optional[datetime]
```

#### **Permission System**
- **Role-Based Access Control (RBAC)**: Predefined roles with specific permissions
- **Attribute-Based Access Control (ABAC)**: Dynamic permissions based on context
- **Tenant-Scoped Permissions**: All permissions automatically scoped to tenant
- **API-Level Authorization**: Every endpoint validates permissions

### **2. Universal Resource Management**

#### **Hierarchical Space Structure**
```python
class Location(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    location_type: str  # 'building', 'floor', 'room', 'desk', 'equipment'
    parent_id: Optional[UUID]  # For hierarchical structure
    hierarchy_level: int  # 1=Building, 2=Floor, 3=Room, 4=Desk
    capacity: Optional[int]
    amenities: List[str]
    custom_fields: Dict[str, Any]  # Industry-specific data
    operating_hours: Dict[str, Any]
    pricing_rules: Dict[str, Any]
    availability_rules: Dict[str, Any]

class BookableResource(BaseModel):
    id: UUID
    location_id: UUID
    tenant_id: UUID
    name: str
    resource_type: str  # Configurable per industry
    booking_rules: Dict[str, Any]
    pricing: Dict[str, Any]
    equipment: List[str]
    images: List[str]
    status: str  # 'active', 'maintenance', 'disabled'
```

#### **Universal Booking Engine**
```python
class Booking(BaseModel):
    id: UUID
    tenant_id: UUID
    resource_id: UUID
    user_id: UUID
    start_time: datetime
    end_time: datetime
    status: str  # 'pending', 'confirmed', 'cancelled', 'completed'
    attendees: int
    equipment_needed: List[str]
    special_requirements: str
    recurring_pattern: Optional[Dict[str, Any]]
    payment_status: str
    total_cost: Decimal

class BookingService:
    async def check_availability(
        self, 
        resource_id: UUID, 
        start_time: datetime, 
        end_time: datetime,
        tenant_id: UUID
    ) -> bool:
        # Universal availability checking logic
        pass
    
    async def create_booking(
        self, 
        booking_data: BookingCreate,
        tenant_id: UUID
    ) -> Booking:
        # Universal booking creation with validation
        pass
```

### **3. Billing & Subscription Platform**

#### **Flexible Pricing Engine**
```python
class PricingRule(BaseModel):
    id: UUID
    tenant_id: UUID
    resource_id: Optional[UUID]  # None for tenant-wide rules
    rule_type: str  # 'base', 'member_discount', 'time_modifier', 'seasonal'
    base_price: Decimal
    currency: str
    billing_frequency: str  # 'hourly', 'daily', 'monthly', 'per_use'
    conditions: Dict[str, Any]  # When this rule applies
    discount_percent: Optional[float]
    multiplier: Optional[float]

class SubscriptionPlan(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str
    price: Decimal
    billing_cycle: str  # 'monthly', 'yearly'
    features: List[str]
    usage_limits: Dict[str, int]
    is_active: bool
```

#### **Multi-Processor Payment System**
```python
class PaymentProcessor:
    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        tenant_id: UUID
    ) -> PaymentResult:
        # Unified payment processing interface
        pass

class StripeProcessor(PaymentProcessor):
    # Stripe-specific implementation
    pass

class SquareProcessor(PaymentProcessor):
    # Square-specific implementation
    pass
```

### **4. Communication Platform**

#### **Multi-Channel Messaging System**
```python
class MessageTemplate(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    template_type: str  # 'email', 'sms', 'push', 'in_app'
    subject: Optional[str]
    content: str
    variables: List[str]  # Available template variables
    trigger_events: List[str]
    is_active: bool

class CommunicationService:
    async def send_message(
        self,
        template_id: UUID,
        recipient: str,
        variables: Dict[str, Any],
        tenant_id: UUID
    ) -> MessageResult:
        # Universal message sending
        pass
    
    async def create_automation(
        self,
        trigger: str,
        conditions: Dict[str, Any],
        actions: List[Dict[str, Any]],
        tenant_id: UUID
    ) -> Automation:
        # Workflow automation creation
        pass
```

### **5. Content Management System**

#### **Flexible CMS Architecture**
```python
class Page(BaseModel):
    id: UUID
    tenant_id: UUID
    title: str
    slug: str
    content_blocks: List[Dict[str, Any]]  # Flexible content structure
    template: str
    meta_data: Dict[str, Any]  # SEO and custom fields
    is_published: bool
    language: str
    created_at: datetime
    updated_at: datetime

class ContentBlock(BaseModel):
    block_type: str  # 'text', 'image', 'booking_widget', 'member_directory'
    content: Dict[str, Any]
    styling: Dict[str, Any]
    permissions: Dict[str, Any]  # Who can see this block
```

---

## 🎨 **Industry Configuration System**

### **Configuration-Driven Customization**

#### **Industry Templates**
```python
class IndustryTemplate(BaseModel):
    industry_type: str  # 'coworking', 'hotel', 'government', 'university'
    default_settings: Dict[str, Any]
    resource_types: List[str]
    booking_workflows: Dict[str, Any]
    user_roles: List[str]
    page_templates: List[str]
    required_fields: List[str]
    optional_features: List[str]

# Example: Coworking Template
COWORKING_TEMPLATE = IndustryTemplate(
    industry_type="coworking",
    default_settings={
        "booking_advance_days": 30,
        "cancellation_policy": "24_hours",
        "member_directory_public": True
    },
    resource_types=["hot_desk", "dedicated_desk", "private_office", "meeting_room"],
    booking_workflows={
        "hot_desk": "instant_booking",
        "meeting_room": "approval_required"
    },
    user_roles=["member", "day_pass", "corporate_admin"],
    page_templates=["coworking_homepage", "membership_plans", "community_events"],
    required_fields=["company", "membership_type"],
    optional_features=["community_board", "event_management", "visitor_management"]
)
```

#### **Dynamic Feature Flags**
```python
class FeatureFlag(BaseModel):
    id: UUID
    tenant_id: UUID
    feature_name: str
    is_enabled: bool
    configuration: Dict[str, Any]
    rollout_percentage: float  # For gradual rollouts
    target_users: List[str]  # Specific user targeting

class FeatureService:
    async def is_feature_enabled(
        self,
        feature_name: str,
        tenant_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bool:
        # Check if feature is enabled for this tenant/user
        pass
```

---

## 📊 **Analytics & Reporting Platform**

### **Universal Analytics Framework**
```python
class AnalyticsEvent(BaseModel):
    id: UUID
    tenant_id: UUID
    event_type: str  # 'booking_created', 'user_login', 'payment_processed'
    user_id: Optional[UUID]
    resource_id: Optional[UUID]
    properties: Dict[str, Any]
    timestamp: datetime

class MetricDefinition(BaseModel):
    name: str
    description: str
    calculation: str  # SQL or formula
    dimensions: List[str]  # Grouping options
    filters: List[str]  # Available filters

class DashboardWidget(BaseModel):
    id: UUID
    tenant_id: UUID
    widget_type: str  # 'chart', 'metric', 'table'
    metric: str
    configuration: Dict[str, Any]
    permissions: List[str]  # Who can view this widget
```

---

## 🔌 **Integration Framework**

### **Plugin Architecture**
```python
class Integration(BaseModel):
    id: UUID
    name: str
    category: str  # 'payment', 'email', 'access_control', 'analytics'
    provider: str
    api_config: Dict[str, Any]
    webhook_endpoints: List[str]
    data_mappings: Dict[str, str]
    is_active: bool

class IntegrationManager:
    async def enable_integration(
        self,
        tenant_id: UUID,
        integration_id: UUID,
        config: Dict[str, Any]
    ) -> IntegrationResult:
        # Enable integration for specific tenant
        pass
    
    async def sync_data(
        self,
        tenant_id: UUID,
        integration_id: UUID,
        data_type: str
    ) -> SyncResult:
        # Bi-directional data synchronization
        pass
```

### **Webhook System**
```python
class WebhookEndpoint(BaseModel):
    id: UUID
    tenant_id: UUID
    url: str
    events: List[str]  # Which events to send
    secret: str  # For signature verification
    is_active: bool
    retry_policy: Dict[str, Any]

class WebhookService:
    async def send_webhook(
        self,
        event: AnalyticsEvent,
        endpoints: List[WebhookEndpoint]
    ) -> List[WebhookResult]:
        # Send webhooks with retry logic
        pass
```

---

## 🚀 **Development Roadmap**

### **Phase 1: Platform Foundation (Months 1-4)**

#### **Critical Infrastructure Fixes**
1. **Complete PostgreSQL Migration** ⚠️ *URGENT*
   - Eliminate MongoDB dependency (currently dual-database system)
   - Fix undefined `db` object references in `backend/server.py`
   - Implement proper row-level security policies
   - Set up proper indexing and performance optimization
   - Migrate existing data from MongoDB to PostgreSQL

2. **Fix PayloadCMS Integration** ⚠️ *URGENT*
   - Resolve missing module imports in `payload.config.ts`
   - Fix `__dirname` reference errors
   - Ensure PostgreSQL adapter is properly configured
   - Test CMS functionality end-to-end

3. **Authentication & Authorization**
   - Complete JWT token system implementation (partially done)
   - Fix missing `timedelta` import in `backend/models/tenant.py`
   - Implement role-based permission system
   - Add multi-factor authentication support
   - Prepare SSO infrastructure (SAML, OAuth2)

4. **Multi-Tenant Architecture**
   - Complete tenant isolation middleware implementation
   - Fix subdomain and custom domain routing
   - Ensure all database queries are tenant-scoped
   - Build admin dashboard for tenant management

5. **Core APIs & Infrastructure**
   - Complete RESTful API design with OpenAPI documentation
   - Implement rate limiting and security headers
   - Add Redis caching layer (currently missing)
   - Build webhook system for real-time integrations
   - Improve error handling and structured logging

6. **Billing Infrastructure**
   - Complete Stripe Connect integration
   - Implement subscription management system
   - Add usage tracking and metering
   - Build invoice generation and payment processing

### **Phase 2: Universal Core Features (Months 5-8)**

#### **Resource Management**
1. **Hierarchical Location System**
   - Buildings → Floors → Rooms → Desks structure
   - Flexible resource types and attributes
   - Capacity management and constraints
   - Operating hours and availability rules

2. **Universal Booking Engine**
   - Real-time availability checking
   - Conflict detection and resolution
   - Recurring booking patterns
   - Booking approval workflows

3. **User Management**
   - Member profiles with custom fields
   - Corporate account management
   - Team and group organization
   - Bulk operations and imports

4. **Communication System**
   - Email template system
   - SMS and push notification support
   - Automated workflow triggers
   - Multi-language message support

### **Phase 3: Platform Enhancement (Months 9-12)**

#### **Advanced Features**
1. **Analytics & Reporting**
   - Custom dashboard builder
   - Real-time metrics and KPIs
   - Data export and API access
   - Predictive analytics foundation

2. **Content Management**
   - Fix PayloadCMS integration
   - Page builder with drag-and-drop
   - Industry-specific templates
   - SEO optimization tools

3. **Integration Framework**
   - Plugin architecture for third-party tools
   - Pre-built integrations (Stripe, Mailchimp, etc.)
   - Webhook management interface
   - API marketplace preparation

4. **Performance & Scalability**
   - Redis caching implementation
   - Database query optimization
   - CDN integration for static assets
   - Load testing and monitoring

### **Phase 4: Industry Customization (Months 13-16)**

#### **Configuration System**
1. **Industry Templates**
   - Coworking space configuration
   - Hotel and hospitality settings
   - Government compliance features
   - University academic integration

2. **Custom Field System**
   - Dynamic form builder
   - Industry-specific data collection
   - Validation rules and constraints
   - Reporting on custom fields

3. **Workflow Customization**
   - Configurable booking flows
   - Approval processes
   - Automated actions and triggers
   - Industry-specific integrations

---

## 🔒 **Security & Compliance**

### **Data Security**
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access Control**: Row-level security, API rate limiting
- **Authentication**: Multi-factor authentication, session management
- **Audit Logging**: Complete audit trail for all operations
- **Data Backup**: Automated daily backups with point-in-time recovery

### **Compliance Framework**
- **GDPR**: Data portability, right to deletion, consent management
- **SOC 2**: Security controls, availability monitoring
- **PCI DSS**: Payment data security (handled by Stripe)
- **Industry-Specific**: HIPAA, SOX, government compliance as needed

---

## 📈 **Performance & Monitoring**

### **Application Performance**
- **Caching Strategy**: Multi-layer caching (Redis, CDN, browser)
- **Database Optimization**: Query optimization, connection pooling
- **API Performance**: Response time monitoring, rate limiting
- **Frontend Performance**: Code splitting, lazy loading, bundle optimization

### **Monitoring & Alerting**
- **Application Monitoring**: Error tracking, performance metrics
- **Infrastructure Monitoring**: Server health, database performance
- **Business Metrics**: Usage analytics, conversion tracking
- **Alert System**: Real-time alerts for critical issues

---

## 🚨 **Current Technical Debt & Priorities**

### **Critical Issues Requiring Immediate Attention**

#### **1. Database Architecture Problems**
- **Incomplete PostgreSQL Migration**: System currently uses both MongoDB and PostgreSQL
- **Missing Database Context**: `db` object referenced but not properly initialized in server code
- **No Row-Level Security**: Multi-tenant isolation not properly implemented
- **Data Consistency Issues**: Risk of data corruption with dual-database system

#### **2. PayloadCMS Integration Broken**
- **Configuration Errors**: Missing modules and `__dirname` references
- **Database Adapter Issues**: PostgreSQL adapter not properly configured
- **Import Problems**: TypeScript configuration conflicts

#### **3. Missing Core Infrastructure**
- **No Caching Layer**: Redis not implemented, impacting performance
- **Incomplete Authentication**: JWT system partially implemented
- **Missing Import**: `timedelta` not imported in tenant model
- **No Webhook System**: Real-time integrations not possible

#### **4. Testing & Quality Assurance**
- **Zero Test Coverage**: No unit or integration tests for PostgreSQL layer
- **No Performance Monitoring**: Query optimization and monitoring missing
- **No Error Tracking**: Structured error handling incomplete

### **Immediate Action Plan**

#### **Week 1-2: Database Stabilization**
1. Complete PostgreSQL migration and eliminate MongoDB
2. Fix all `db` object references in backend code
3. Implement proper tenant isolation with row-level security
4. Add missing imports (`timedelta` in tenant.py)

#### **Week 3-4: CMS Integration Fix**
1. Resolve PayloadCMS configuration errors
2. Fix missing module imports and `__dirname` issues
3. Test CMS functionality end-to-end
4. Ensure PostgreSQL adapter works correctly

#### **Week 5-8: Core Infrastructure**
1. Implement Redis caching layer
2. Complete JWT authentication system
3. Add proper error handling and logging
4. Build webhook system foundation

---

## 💡 **Key Architectural Principles**

### **1. Platform-First Design**
- Build universal features that work across all industries
- Use configuration and templates for industry-specific needs
- Maintain unified codebase with feature flags for customization
- **Current Status**: Foundation exists but needs stabilization

### **2. Tenant Isolation**
- Complete data isolation between tenants
- Scalable multi-tenancy with row-level security
- Custom domains and branding per tenant
- **Current Status**: Partially implemented, needs completion

### **3. API-Driven Architecture**
- All functionality exposed through well-documented APIs
- Webhook system for real-time integrations
- Mobile-ready API design
- **Current Status**: Basic APIs exist, webhooks missing

### **4. Configuration Over Customization**
- Industry differences handled through configuration
- Template system for common use cases
- Custom fields and workflows without code changes
- **Current Status**: Framework exists, needs expansion

### **5. Security by Design**
- Security considerations in every architectural decision
- Compliance-ready from day one
- Audit logging and data protection built-in
- **Current Status**: Basic security implemented, needs enhancement

---

## 🎯 **Success Metrics**

### **Platform Metrics**
- **Tenant Growth**: Monthly new tenant acquisition
- **Feature Adoption**: Usage of core platform features
- **API Usage**: Integration and webhook utilization
- **Performance**: Response times, uptime, error rates

### **Business Metrics**
- **Revenue per Tenant**: Monthly recurring revenue growth
- **Churn Rate**: Tenant retention and satisfaction
- **Support Tickets**: Platform stability and usability
- **Time to Value**: How quickly new tenants see benefits

---

## 🎯 **Strategic Recommendations**

### **Focus on Platform Stability First**
Rather than pursuing the ambitious multi-industry vision immediately, we recommend:

1. **Stabilize Current Architecture**: Fix critical technical debt before adding features
2. **Complete Core Platform**: Finish multi-tenancy, authentication, and billing systems
3. **Prove Platform Concept**: Validate with one industry (coworking) before expanding
4. **Build Configuration System**: Create framework for industry customization
5. **Scale Gradually**: Add industries through configuration, not custom code

### **Technology Stack Validation**
The current FastAPI + React + PayloadCMS architecture is well-suited for:
- **Rapid Development**: Familiar technologies with good ecosystem support
- **Team Expertise**: Leverage existing Python and React knowledge
- **Service Separation**: Clear boundaries between business logic, UI, and content
- **Deployment Flexibility**: Each service can be optimized independently

### **Success Metrics for Platform Foundation**
- **Technical Stability**: Zero critical bugs, 99.9% uptime
- **Development Velocity**: New features deployed weekly
- **Tenant Onboarding**: New tenant setup in under 30 minutes
- **Performance**: API response times under 200ms
- **Security**: Pass security audit and compliance requirements

---

This platform-first architecture ensures that Claude App can serve any industry while maintaining a single, scalable codebase. However, **immediate focus must be on stabilizing the foundation** - completing the PostgreSQL migration, fixing PayloadCMS integration, and implementing proper caching and error handling. Only after this technical debt is resolved should we pursue the broader multi-industry vision.

The current architecture provides a solid foundation for growth, but **execution must prioritize stability over features** to ensure long-term success.
