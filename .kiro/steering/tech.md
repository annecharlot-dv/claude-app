# Technology Stack

## Backend Architecture

- **Framework**: FastAPI (Python) with async/await support
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens with bcrypt password hashing
- **API Design**: RESTful APIs with OpenAPI/Swagger documentation

### Core Architecture Patterns

- **Kernel System**: Shared business logic across all tenants (Identity, Booking, Financial, CMS, Communication)
- **Module System**: Industry-specific customizations and terminology
- **Multi-tenant**: Tenant isolation at the database level with tenant_id filtering

### Key Dependencies

```
fastapi==0.110.1
uvicorn==0.25.0
motor==3.3.1 (MongoDB async driver)
pymongo==4.5.0
pydantic>=2.6.4 (data validation)
python-jose>=3.3.0 (JWT handling)
passlib>=1.7.4 (password hashing)
boto3>=1.34.129 (AWS services)
```

## Frontend Architecture

- **Framework**: React 19 with functional components and hooks
- **Build Tool**: Create React App with CRACO for customization
- **Styling**: Tailwind CSS for utility-first styling
- **State Management**: React Query (@tanstack/react-query) for server state
- **Routing**: React Router DOM v7
- **HTTP Client**: Axios for API calls

### Key Dependencies

```
react: ^19.0.0
@tanstack/react-query: ^5.83.0
react-router-dom: ^7.5.1
axios: ^1.8.4
tailwindcss: ^3.4.17
```

## Development Tools

- **Code Quality**: Black, isort, flake8, mypy for Python; ESLint for JavaScript
- **Testing**: pytest for backend testing
- **Package Management**: pip/requirements.txt for Python, yarn for Node.js

## Common Commands

### Backend Development
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run development server
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Code formatting
black .
isort .
flake8 .
```

### Frontend Development
```bash
# Install dependencies
cd frontend
yarn install

# Run development server
yarn start

# Build for production
yarn build

# Run tests
yarn test
```

## Environment Configuration

Both backend and frontend use `.env` files for configuration:
- `backend/.env` - Database URLs, secret keys, AWS credentials
- `frontend/.env` - API endpoints, feature flags

## Database Schema

MongoDB collections follow a tenant-isolated pattern where each document includes a `tenant_id` field for multi-tenant data separation.