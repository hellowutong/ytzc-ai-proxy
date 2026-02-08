#!/bin/bash
#
# AI Gateway Setup Script
# Automated setup for first-time installation
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "=========================================="
echo "  AI Gateway Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   log_error "Please do not run as root"
   exit 1
fi

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check Python (for local development)
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python version: $PYTHON_VERSION"
    fi
    
    # Check Node.js (for frontend development)
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_info "Node.js version: $NODE_VERSION"
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warning "Created .env from template. Please edit it with your settings."
        else
            log_error ".env.example not found"
            exit 1
        fi
    else
        log_info ".env already exists"
    fi
    
    # Generate secure passwords if not set
    if grep -q "your_secure_password" .env; then
        log_info "Generating secure passwords..."
        
        MONGODB_ROOT_PASSWORD=$(openssl rand -base64 32)
        MONGODB_PASSWORD=$(openssl rand -base64 32)
        REDIS_PASSWORD=$(openssl rand -base64 32)
        QDRANT_API_KEY=$(openssl rand -base64 32)
        
        sed -i "s/your_secure_password_here/$MONGODB_ROOT_PASSWORD/g" .env
        sed -i "s/your_app_password_here/$MONGODB_PASSWORD/g" .env
        sed -i "s/your_redis_password_here/$REDIS_PASSWORD/g" .env
        sed -i "s/your_qdrant_api_key_here/$QDRANT_API_KEY/g" .env
        
        log_success "Secure passwords generated"
    fi
}

# Setup directories
setup_directories() {
    log_info "Creating directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p backups
    mkdir -p docker/nginx/ssl
    mkdir -p docker/nginx/logs
    
    log_success "Directories created"
}

# Setup configuration
setup_config() {
    log_info "Setting up configuration..."
    
    if [ ! -f "config.yml" ]; then
        log_error "config.yml not found. Please create it first."
        exit 1
    fi
    
    log_info "Configuration file found"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Backend dependencies
    if [ -d "app" ]; then
        log_info "Setting up Python virtual environment..."
        cd app
        
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        pip install -q --upgrade pip
        pip install -q -r requirements.txt
        
        log_success "Backend dependencies installed"
        cd ..
    fi
    
    # Frontend dependencies
    if [ -d "wei-ui" ]; then
        log_info "Installing frontend dependencies..."
        cd wei-ui
        
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        
        log_success "Frontend dependencies installed"
        cd ..
    fi
}

# Make scripts executable
setup_scripts() {
    log_info "Setting up scripts..."
    
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_success "Scripts are ready"
}

# Start infrastructure services
start_infrastructure() {
    log_info "Starting infrastructure services..."
    
    docker-compose up -d mongodb redis qdrant
    
    # Wait for services
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    log_info "Checking service health..."
    
    # Check MongoDB
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        log_success "MongoDB is ready"
    else
        log_warning "MongoDB may not be fully ready yet"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is ready"
    else
        log_warning "Redis may not be fully ready yet"
    fi
    
    # Check Qdrant
    if curl -sf http://localhost:6333/healthz > /dev/null 2>&1; then
        log_success "Qdrant is ready"
    else
        log_warning "Qdrant may not be fully ready yet"
    fi
}

# Main setup
main() {
    check_prerequisites
    setup_environment
    setup_directories
    setup_config
    install_dependencies
    setup_scripts
    start_infrastructure
    
    echo ""
    echo "=========================================="
    log_success "Setup completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Review and edit configuration:"
    echo "   - Edit config.yml to configure your models"
    echo "   - Edit .env to set your passwords"
    echo ""
    echo "2. Start the backend (development):"
    echo "   cd app"
    echo "   source venv/bin/activate"
    echo "   uvicorn main:app --reload"
    echo ""
    echo "3. Start the frontend (development):"
    echo "   cd wei-ui"
    echo "   npm run dev"
    echo ""
    echo "4. Or deploy with Docker:"
    echo "   ./scripts/deploy.sh local"
    echo ""
    echo "5. Access the application:"
    echo "   Frontend: http://localhost:5175"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "For production deployment, see:"
    echo "   docs/DEPLOYMENT.md"
    echo ""
}

main
