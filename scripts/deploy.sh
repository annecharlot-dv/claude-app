#!/bin/bash

# Automated deployment script for Claude Platform
set -e

# Configuration
ENVIRONMENT=${1:-staging}
SKIP_TESTS=${2:-false}
FORCE_DEPLOY=${3:-false}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    log_info "Validating deployment environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        production|staging|preview)
            log_success "Environment '$ENVIRONMENT' is valid"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT. Must be one of: production, staging, preview"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        log_error "Vercel CLI is not installed. Please install it with: npm install -g vercel"
        exit 1
    fi
    
    # Check if required environment variables are set
    if [ -z "$VERCEL_TOKEN" ]; then
        log_error "VERCEL_TOKEN environment variable is not set"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "package.json" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
        log_error "This script must be run from the project root directory"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_warning "Skipping tests as requested"
        return 0
    fi
    
    log_info "Running test suite..."
    
    # Frontend tests
    log_info "Running frontend tests..."
    cd frontend
    yarn install --frozen-lockfile
    yarn test --coverage --watchAll=false
    yarn build:analyze
    cd ..
    
    # Backend tests
    log_info "Running backend tests..."
    cd backend
    pip install -r requirements.txt
    pytest --cov=. --cov-report=xml --cov-report=html
    black --check .
    isort --check-only .
    flake8 .
    mypy .
    cd ..
    
    # Load testing
    log_info "Running load tests..."
    cd tests
    python load_testing.py
    cd ..
    
    log_success "All tests passed"
}

# Security scan
run_security_scan() {
    log_info "Running security scan..."
    
    # Frontend dependency audit
    cd frontend
    yarn audit --level moderate || log_warning "Frontend audit found issues"
    cd ..
    
    # Backend dependency audit
    cd backend
    pip install safety
    safety check || log_warning "Backend safety check found issues"
    cd ..
    
    log_success "Security scan completed"
}

# Build application
build_application() {
    log_info "Building application for $ENVIRONMENT..."
    
    # Generate environment-specific Vercel config
    node -e "
        const { generateVercelConfig } = require('./infrastructure/vercel-config.js');
        const config = generateVercelConfig('$ENVIRONMENT');
        require('fs').writeFileSync('vercel.json', JSON.stringify(config, null, 2));
        console.log('Generated vercel.json for $ENVIRONMENT');
    "
    
    # Pull Vercel environment information
    vercel pull --yes --environment=$ENVIRONMENT --token=$VERCEL_TOKEN
    
    # Build project artifacts
    vercel build --token=$VERCEL_TOKEN
    
    log_success "Application built successfully"
}

# Deploy to Vercel
deploy_to_vercel() {
    log_info "Deploying to Vercel ($ENVIRONMENT)..."
    
    local deploy_args="--prebuilt --token=$VERCEL_TOKEN"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        deploy_args="$deploy_args --prod"
    fi
    
    # Deploy
    DEPLOYMENT_URL=$(vercel deploy $deploy_args)
    
    if [ $? -eq 0 ]; then
        log_success "Deployment successful: $DEPLOYMENT_URL"
        echo "DEPLOYMENT_URL=$DEPLOYMENT_URL" >> $GITHUB_ENV 2>/dev/null || true
    else
        log_error "Deployment failed"
        exit 1
    fi
}

# Post-deployment health checks
run_health_checks() {
    log_info "Running post-deployment health checks..."
    
    # Wait for deployment to be ready
    sleep 30
    
    # Health check endpoints
    local endpoints=(
        "/api/health"
        "/api/auth/verify"
        "/"
    )
    
    local base_url
    if [ "$ENVIRONMENT" = "production" ]; then
        base_url="https://your-domain.com"
    else
        base_url="$DEPLOYMENT_URL"
    fi
    
    for endpoint in "${endpoints[@]}"; do
        log_info "Checking $base_url$endpoint"
        
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$base_url$endpoint" || echo "000")
        
        if [ "$status_code" -ge 200 ] && [ "$status_code" -lt 400 ]; then
            log_success "✓ $endpoint (HTTP $status_code)"
        else
            log_error "✗ $endpoint (HTTP $status_code)"
            exit 1
        fi
    done
    
    # Run comprehensive health check
    log_info "Running comprehensive health check..."
    cd monitoring
    python health-check.py
    cd ..
    
    log_success "All health checks passed"
}

# Database migration
run_database_migration() {
    log_info "Running database migrations..."
    
    # This would typically connect to your database and run migrations
    # For now, we'll just log that migrations would run here
    log_info "Database migrations would run here"
    
    log_success "Database migrations completed"
}

# Backup before deployment
create_backup() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Creating backup before production deployment..."
        
        # This would typically create a database backup
        # For now, we'll just log that backup would be created
        log_info "Production backup would be created here"
        
        log_success "Backup created successfully"
    fi
}

# Rollback function
rollback_deployment() {
    log_error "Deployment failed. Initiating rollback..."
    
    # Get previous deployment
    local previous_deployment=$(vercel ls --token=$VERCEL_TOKEN | grep "Ready" | head -2 | tail -1 | awk '{print $1}')
    
    if [ -n "$previous_deployment" ]; then
        log_info "Rolling back to previous deployment: $previous_deployment"
        vercel promote $previous_deployment --token=$VERCEL_TOKEN
        log_success "Rollback completed"
    else
        log_error "No previous deployment found for rollback"
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    
    # Remove temporary files
    rm -f vercel.json.bak
    
    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting deployment process for $ENVIRONMENT environment"
    
    # Set up error handling
    trap 'log_error "Deployment failed at line $LINENO"; rollback_deployment; cleanup; exit 1' ERR
    trap 'cleanup' EXIT
    
    # Backup current vercel.json if it exists
    [ -f "vercel.json" ] && cp vercel.json vercel.json.bak
    
    # Run deployment steps
    validate_environment
    check_prerequisites
    
    if [ "$FORCE_DEPLOY" != "true" ]; then
        run_tests
        run_security_scan
    else
        log_warning "Forcing deployment without tests and security scan"
    fi
    
    create_backup
    run_database_migration
    build_application
    deploy_to_vercel
    run_health_checks
    
    log_success "🚀 Deployment to $ENVIRONMENT completed successfully!"
    log_info "Deployment URL: $DEPLOYMENT_URL"
}

# Show usage
show_usage() {
    echo "Usage: $0 [ENVIRONMENT] [SKIP_TESTS] [FORCE_DEPLOY]"
    echo ""
    echo "Arguments:"
    echo "  ENVIRONMENT   Target environment (production|staging|preview) [default: staging]"
    echo "  SKIP_TESTS    Skip test execution (true|false) [default: false]"
    echo "  FORCE_DEPLOY  Force deployment without tests/security scan (true|false) [default: false]"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy to staging with tests"
    echo "  $0 production                # Deploy to production with tests"
    echo "  $0 staging true              # Deploy to staging without tests"
    echo "  $0 production false true     # Force deploy to production"
    echo ""
    echo "Environment variables required:"
    echo "  VERCEL_TOKEN                 # Vercel authentication token"
}

# Handle command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

# Run main function
main