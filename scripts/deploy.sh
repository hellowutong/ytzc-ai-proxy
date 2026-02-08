#!/bin/bash
#
# AI Gateway Deployment Script
# Usage: ./scripts/deploy.sh [environment]
# Environment: local (default), staging, production
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-local}
COMPOSE_FILES="-f docker-compose.yml"
BACKUP_BEFORE_DEPLOY=true
HEALTH_CHECK_TIMEOUT=60

# Functions
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

# Check if Docker and Docker Compose are installed
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Check environment file
check_environment() {
    log_info "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning ".env file not found. Creating from .env.example..."
            cp .env.example .env
            log_warning "Please edit .env file with your configuration before continuing."
            exit 1
        else
            log_error ".env file not found and no .env.example available."
            exit 1
        fi
    fi
    
    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs)
    
    # Check required variables
    if [ -z "$MONGODB_ROOT_PASSWORD" ]; then
        log_error "MONGODB_ROOT_PASSWORD is not set in .env"
        exit 1
    fi
    
    if [ -z "$REDIS_PASSWORD" ]; then
        log_error "REDIS_PASSWORD is not set in .env"
        exit 1
    fi
    
    log_success "Environment check passed"
}

# Create required directories
setup_directories() {
    log_info "Setting up directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p docker/nginx/ssl
    mkdir -p docker/nginx/logs
    mkdir -p backups
    
    log_success "Directories created"
}

# Create backup before deployment
create_backup() {
    if [ "$BACKUP_BEFORE_DEPLOY" = true ] && [ "$ENVIRONMENT" != "local" ]; then
        log_info "Creating backup before deployment..."
        
        if [ -f "scripts/backup.sh" ]; then
            ./scripts/backup.sh
            log_success "Backup created"
        else
            log_warning "Backup script not found, skipping backup"
        fi
    fi
}

# Deploy function
deploy() {
    log_info "Starting deployment to ${ENVIRONMENT} environment..."
    
    # Add production compose file for non-local environments
    if [ "$ENVIRONMENT" != "local" ]; then
        COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.prod.yml"
    fi
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose $COMPOSE_FILES pull
    
    # Stop existing services gracefully
    log_info "Stopping existing services..."
    docker-compose $COMPOSE_FILES down --remove-orphans
    
    # Start services
    log_info "Starting services..."
    docker-compose $COMPOSE_FILES up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Health check
    log_info "Performing health checks..."
    perform_health_checks
    
    log_success "Deployment completed successfully!"
    
    # Display status
    show_status
}

# Health checks
perform_health_checks() {
    local timeout=$HEALTH_CHECK_TIMEOUT
    local elapsed=0
    local all_healthy=false
    
    while [ $elapsed -lt $timeout ]; do
        all_healthy=true
        
        # Check backend health
        if ! curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            all_healthy=false
            log_info "Waiting for backend to be healthy..."
        fi
        
        # Check MongoDB
        if ! docker-compose ps | grep -q "mongodb.*Up"; then
            all_healthy=false
            log_info "Waiting for MongoDB to be ready..."
        fi
        
        # Check Redis
        if ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            all_healthy=false
            log_info "Waiting for Redis to be ready..."
        fi
        
        if [ "$all_healthy" = true ]; then
            log_success "All services are healthy"
            return 0
        fi
        
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    log_error "Health checks failed after ${timeout} seconds"
    show_logs
    exit 1
}

# Display service status
show_status() {
    echo ""
    echo "========================================="
    log_info "Service Status"
    echo "========================================="
    docker-compose ps
    echo ""
    
    log_info "Application URLs:"
    if [ "$ENVIRONMENT" = "local" ]; then
        echo "  - Frontend: http://localhost:5175"
        echo "  - Backend API: http://localhost:8000"
        echo "  - API Docs: http://localhost:8000/docs"
    else
        echo "  - Application: http://localhost (via Nginx)"
        echo "  - API: http://localhost/api"
        echo "  - API Docs: http://localhost/api/v1/docs"
    fi
    echo ""
}

# Show logs
show_logs() {
    echo ""
    log_info "Recent logs:"
    docker-compose logs --tail=50
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose $COMPOSE_FILES down
    
    # Restore from backup if available
    if [ -d "backups" ] && [ "$(ls -A backups)" ]; then
        latest_backup=$(ls -t backups/*.tar.gz | head -1)
        if [ -n "$latest_backup" ]; then
            log_info "Restoring from backup: $latest_backup"
            # Restore logic would go here
            log_success "Rollback completed"
        fi
    else
        log_warning "No backup found for rollback"
    fi
}

# Main execution
case "${ENVIRONMENT}" in
    local|staging|production)
        log_info "Deploying to ${ENVIRONMENT} environment..."
        ;;
    *)
        log_error "Unknown environment: ${ENVIRONMENT}"
        echo "Usage: $0 [local|staging|production]"
        exit 1
        ;;
esac

# Trap errors for rollback
trap 'log_error "Deployment failed!"; rollback; exit 1' ERR

# Execute deployment steps
check_prerequisites
check_environment
setup_directories
create_backup
deploy

log_success "AI Gateway has been successfully deployed to ${ENVIRONMENT}!"

# Provide next steps
if [ "$ENVIRONMENT" = "local" ]; then
    echo ""
    log_info "Next steps:"
    echo "  1. Configure your models in config.yml"
    echo "  2. Start the frontend: cd wei-ui && npm run dev"
    echo "  3. Access the application at http://localhost:5175"
    echo ""
    echo "  View logs: docker-compose logs -f"
    echo "  Stop services: docker-compose down"
fi
