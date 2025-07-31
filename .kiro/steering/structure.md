# Project Structure

## Root Directory Organization

```
├── backend/                 # Python FastAPI backend
├── frontend/               # React frontend application
├── tests/                  # Shared test utilities
├── .emergent/             # Emergent AI configuration
├── .kiro/                 # Kiro IDE configuration and steering
└── README.md              # Project documentation
```

## Backend Structure (`backend/`)

```
backend/
├── server.py                    # Main FastAPI application and routes
├── claude_platform_core.py     # Core platform orchestration
├── requirements.txt             # Python dependencies
├── .env                        # Environment configuration
├── kernels/                    # Shared business logic kernels
│   ├── base_kernel.py          # Abstract base for all kernels
│   ├── identity_kernel.py      # User authentication & authorization
│   ├── booking_kernel.py       # Resource booking logic
│   ├── financial_kernel.py     # Payment and billing
│   ├── cms_kernel.py          # Content management
│   └── communication_kernel.py # Notifications and workflows
├── modules/                    # Industry-specific customizations
│   ├── base_module.py          # Abstract base for all modules
│   ├── module_registry.py      # Module loading and management
│   ├── coworking_module.py     # Coworking space customizations
│   ├── government_module.py    # Government facility customizations
│   ├── hotel_module.py         # Hotel/hospitality customizations
│   ├── university_module.py    # University customizations
│   ├── creative_studio_module.py # Creative studio customizations
│   └── residential_module.py   # Residential customizations
├── cms_engine/                 # Enhanced CMS functionality
│   └── coworking_cms.py        # Coworking-specific CMS features
└── seed_*.py                   # Database seeding scripts
```

## Frontend Structure (`frontend/`)

```
frontend/
├── public/                     # Static assets
├── src/
│   ├── components/             # Reusable React components
│   ├── contexts/              # React context providers (Auth, Tenant)
│   ├── pages/                 # Page-level components
│   │   ├── cms/               # CMS-related pages
│   │   ├── Dashboard.js       # Main dashboard
│   │   ├── LoginPage.js       # Authentication
│   │   ├── Forms.js           # Form management
│   │   ├── Leads.js           # Lead management
│   │   └── Tours.js           # Tour scheduling
│   ├── services/              # API service functions
│   ├── App.js                 # Main application component
│   └── index.js               # Application entry point
├── package.json               # Node.js dependencies
├── craco.config.js           # Build configuration overrides
├── tailwind.config.js        # Tailwind CSS configuration
└── .env                      # Frontend environment variables
```

## Key Architecture Principles

### Multi-Tenant Data Isolation
- All database documents include `tenant_id` for data separation
- API routes automatically filter by current user's tenant
- Each tenant gets subdomain-based routing

### Kernel-Module Pattern
- **Kernels**: Universal business logic shared across all tenants
- **Modules**: Industry-specific customizations, terminology, and workflows
- Clean separation allows adding new industries without affecting core logic

### Role-Based Access Control
- Hierarchical user roles: Platform Admin → Account Owner → Property Manager → Front Desk → Member
- Industry modules define role-specific permissions and terminology
- Route protection based on required roles

### API Route Organization
- All API routes prefixed with `/api`
- RESTful resource naming conventions
- Consistent error handling and response formats
- Automatic OpenAPI documentation generation

## File Naming Conventions

### Backend (Python)
- Snake_case for files and variables
- PascalCase for classes
- Descriptive module names ending with purpose (e.g., `_kernel.py`, `_module.py`)

### Frontend (JavaScript)
- PascalCase for React components
- camelCase for functions and variables
- Descriptive component names indicating purpose (e.g., `PageEditor.js`, `ProtectedRoute.js`)

## Configuration Management

### Environment Variables
- Development: `.env` files in respective directories
- Production: Environment-specific configuration
- Sensitive data (API keys, secrets) never committed to version control

### Feature Toggles
- Tenant-level feature toggles stored in database
- Module-specific feature configurations
- Runtime feature flag evaluation