#!/bin/bash
# Quick Start Script for AI Gateway
# This script helps you quickly test and run the AI Gateway system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

print_status "AI Gateway Quick Start Script"
print_status "Project directory: $PROJECT_DIR"
echo ""

# Check prerequisites
print_status "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Docker and Docker Compose are installed"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python version: $PYTHON_VERSION"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js version: $NODE_VERSION"

echo ""
print_status "All prerequisites met!"
echo ""

# Function to start infrastructure
start_infrastructure() {
    print_status "Starting infrastructure services (MongoDB, Redis, Qdrant)..."
    
    docker-compose up -d mongodb redis qdrant
    
    print_status "Waiting for services to be ready..."
    sleep 5
    
    # Check if services are healthy
    MONGO_HEALTH=$(docker-compose ps -q mongodb | xargs docker inspect -f '{{.State.Status}}' 2>/dev/null || echo "not running")
    REDIS_HEALTH=$(docker-compose ps -q redis | xargs docker inspect -f '{{.State.Status}}' 2>/dev/null || echo "not running")
    QDRANT_HEALTH=$(docker-compose ps -q qdrant | xargs docker inspect -f '{{.State.Status}}' 2>/dev/null || echo "not running")
    
    if [ "$MONGO_HEALTH" = "running" ] && [ "$REDIS_HEALTH" = "running" ] && [ "$QDRANT_HEALTH" = "running" ]; then
        print_success "All infrastructure services are running!"
    else
        print_warning "Some services may not be fully ready yet. Continuing anyway..."
    fi
}

# Function to setup backend
setup_backend() {
    print_status "Setting up Python backend..."
    
    cd "$PROJECT_DIR/app"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    print_success "Backend dependencies installed"
}

# Function to setup frontend
setup_frontend() {
    print_status "Setting up Node.js frontend..."
    
    cd "$PROJECT_DIR/wei-ui"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install
    else
        print_status "Node.js dependencies already installed"
    fi
    
    print_success "Frontend dependencies ready"
}

# Function to run tests
run_tests() {
    print_status "Running integration tests..."
    
    cd "$PROJECT_DIR/app"
    source venv/bin/activate
    
    # Run tests with verbose output
    python -m pytest tests/test_integration.py -v --tb=short 2>&1 | head -100
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_warning "Some tests may have failed. Check the output above."
    fi
}

# Function to start backend server
start_backend() {
    print_status "Starting backend server..."
    print_status "Backend will be available at: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    
    cd "$PROJECT_DIR/app"
    source venv/bin/activate
    
    # Start in background
    nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    echo $! > backend.pid
    
    sleep 3
    
    # Check if server is running
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        print_success "Backend server is running!"
    else
        print_warning "Backend server starting... Check backend.log for details"
    fi
}

# Function to start frontend server
start_frontend() {
    print_status "Starting frontend development server..."
    print_status "Frontend will be available at: http://localhost:5175"
    
    cd "$PROJECT_DIR/wei-ui"
    
    # Start in background
    nohup npm run dev > frontend.log 2>&1 &
    echo $! > frontend.pid
    
    sleep 5
    
    # Check if server is running
    if curl -s http://localhost:5175 > /dev/null 2>&1; then
        print_success "Frontend server is running!"
    else
        print_warning "Frontend server starting... Check frontend.log for details"
    fi
}

# Function to stop servers
stop_servers() {
    print_status "Stopping servers..."
    
    # Stop backend
    if [ -f "$PROJECT_DIR/app/backend.pid" ]; then
        kill $(cat "$PROJECT_DIR/app/backend.pid") 2>/dev/null || true
        rm -f "$PROJECT_DIR/app/backend.pid"
        print_success "Backend server stopped"
    fi
    
    # Stop frontend
    if [ -f "$PROJECT_DIR/wei-ui/frontend.pid" ]; then
        kill $(cat "$PROJECT_DIR/wei-ui/frontend.pid") 2>/dev/null || true
        rm -f "$PROJECT_DIR/wei-ui/frontend.pid"
        print_success "Frontend server stopped"
    fi
}

# Function to show status
show_status() {
    print_status "Checking system status..."
    
    echo ""
    echo "=== Infrastructure Services ==="
    docker-compose ps mongodb redis qdrant 2>/dev/null || echo "Not running"
    
    echo ""
    echo "=== Backend Server ==="
    if [ -f "$PROJECT_DIR/app/backend.pid" ]; then
        if kill -0 $(cat "$PROJECT_DIR/app/backend.pid") 2>/dev/null; then
            print_success "Running (PID: $(cat $PROJECT_DIR/app/backend.pid))"
            echo "URL: http://localhost:8000"
        else
            print_error "Not running (stale PID file)"
        fi
    else
        print_error "Not running"
    fi
    
    echo ""
    echo "=== Frontend Server ==="
    if [ -f "$PROJECT_DIR/wei-ui/frontend.pid" ]; then
        if kill -0 $(cat "$PROJECT_DIR/wei-ui/frontend.pid") 2>/dev/null; then
            print_success "Running (PID: $(cat $PROJECT_DIR/wei-ui/frontend.pid))"
            echo "URL: http://localhost:5175"
        else
            print_error "Not running (stale PID file)"
        fi
    else
        print_error "Not running"
    fi
    
    echo ""
    echo "=== API Health Check ==="
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        curl -s http://localhost:8000/api/v1/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/api/v1/health
    else
        print_error "Cannot connect to backend API"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "================================"
    echo "    AI Gateway Quick Start"
    echo "================================"
    echo ""
    echo "1) Full Setup (Infrastructure + Backend + Frontend)"
    echo "2) Start Infrastructure Only (Docker services)"
    echo "3) Setup Backend Only"
    echo "4) Setup Frontend Only"
    echo "5) Run Tests"
    echo "6) Start Backend Server"
    echo "7) Start Frontend Server"
    echo "8) Start Both Servers"
    echo "9) Stop All Servers"
    echo "10) Show Status"
    echo "11) Stop Infrastructure"
    echo "0) Exit"
    echo ""
    echo -n "Select an option: "
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read choice
        
        case $choice in
            1)
                stop_servers
                start_infrastructure
                setup_backend
                setup_frontend
                start_backend
                start_frontend
                print_success "Full setup complete!"
                echo ""
                echo "Frontend: http://localhost:5175"
                echo "Backend API: http://localhost:8000"
                echo "API Docs: http://localhost:8000/docs"
                ;;
            2)
                start_infrastructure
                ;;
            3)
                setup_backend
                ;;
            4)
                setup_frontend
                ;;
            5)
                run_tests
                ;;
            6)
                start_backend
                ;;
            7)
                start_frontend
                ;;
            8)
                start_backend
                start_frontend
                ;;
            9)
                stop_servers
                ;;
            10)
                show_status
                ;;
            11)
                docker-compose down
                print_success "Infrastructure stopped"
                ;;
            0)
                print_status "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
        
        echo ""
        echo "Press Enter to continue..."
        read
    done
else
    # Command line mode
    case $1 in
        setup)
            stop_servers
            start_infrastructure
            setup_backend
            setup_frontend
            print_success "Setup complete!"
            ;;
        start)
            start_backend
            start_frontend
            print_success "Servers started!"
            ;;
        stop)
            stop_servers
            ;;
        test|tests)
            run_tests
            ;;
        status)
            show_status
            ;;
        infrastructure)
            if [ "$2" = "stop" ]; then
                docker-compose down
            else
                start_infrastructure
            fi
            ;;
        *)
            echo "Usage: $0 [setup|start|stop|test|status|infrastructure]"
            echo ""
            echo "Commands:"
            echo "  setup         - Full setup (infrastructure + dependencies)"
            echo "  start         - Start backend and frontend servers"
            echo "  stop          - Stop all servers"
            echo "  test          - Run integration tests"
            echo "  status        - Show system status"
            echo "  infrastructure [stop] - Start/stop Docker infrastructure"
            exit 1
            ;;
    esac
fi
