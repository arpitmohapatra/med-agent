#!/bin/bash

# MedQuery MVP Quick Start Script
# This script helps you get MedQuery running quickly

set -e

echo "🏥 MedQuery MVP Quick Start"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python $PYTHON_VERSION found"
    else
        log_error "Python 3 is required but not found"
        exit 1
    fi
    
    # Check Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        log_success "Node.js $NODE_VERSION found"
    else
        log_error "Node.js is required but not found"
        log_info "Please install Node.js from https://nodejs.org/"
        exit 1
    fi
    
    # Check npm
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        log_success "npm $NPM_VERSION found"
    else
        log_error "npm is required but not found"
        exit 1
    fi
    
    # Check Docker (optional)
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,//')
        log_success "Docker $DOCKER_VERSION found"
        DOCKER_AVAILABLE=true
    else
        log_warning "Docker not found - you'll need to install Elasticsearch manually"
        DOCKER_AVAILABLE=false
    fi
}

# Setup backend
setup_backend() {
    log_info "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create .env file
    if [ ! -f ".env" ]; then
        log_info "Creating .env file..."
        cp env.example .env
        log_warning "Please update .env with your API keys!"
    fi
    
    cd ..
    log_success "Backend setup complete!"
}

# Setup frontend
setup_frontend() {
    log_info "Setting up frontend..."
    
    cd frontend
    
    # Install dependencies
    log_info "Installing Node.js dependencies..."
    npm install
    
    cd ..
    log_success "Frontend setup complete!"
}

# Start Elasticsearch
start_elasticsearch() {
    if [ "$DOCKER_AVAILABLE" = true ]; then
        log_info "Starting Elasticsearch with Docker..."
        docker-compose up -d elasticsearch
        
        # Wait for Elasticsearch to be ready
        log_info "Waiting for Elasticsearch to be ready..."
        for i in {1..30}; do
            if curl -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
                log_success "Elasticsearch is ready!"
                return 0
            fi
            echo -n "."
            sleep 2
        done
        
        log_error "Elasticsearch failed to start"
        return 1
    else
        log_warning "Docker not available - please start Elasticsearch manually"
        log_info "Download from: https://www.elastic.co/downloads/elasticsearch"
        log_info "Or install via package manager"
        
        # Check if Elasticsearch is already running
        if curl -s http://localhost:9200/_cluster/health >/dev/null 2>&1; then
            log_success "Elasticsearch is already running!"
            return 0
        else
            log_error "Elasticsearch is not running on localhost:9200"
            log_info "Please start Elasticsearch and run this script again"
            return 1
        fi
    fi
}

# Create demo user
create_demo_user() {
    log_info "Creating demo user..."
    
    cd backend
    source venv/bin/activate
    
    cat > create_demo_user.py << 'EOF'
import asyncio
import sys
sys.path.append(".")

from app.services.auth import AuthService
from app.models.user import UserCreate

async def main():
    auth_service = AuthService()
    
    # Check if demo user exists
    if auth_service.get_user_by_username("demo"):
        print("Demo user already exists")
        return
    
    # Create demo user
    demo_user = UserCreate(
        username="demo",
        email="demo@medquery.app",
        password="password123",
        full_name="Demo User"
    )
    
    try:
        user = auth_service.create_user(demo_user)
        print(f"Created demo user: {user.username}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
EOF
    
    python create_demo_user.py
    rm create_demo_user.py
    
    cd ..
    log_success "Demo user created!"
}

# Ingest sample data
ingest_sample_data() {
    log_info "Ingesting medicine dataset..."
    
    cd backend
    source venv/bin/activate
    
    # Check if medicine_dataset.csv exists
    if [ -f "medicine_dataset.csv" ]; then
        log_info "Found medicine_dataset.csv with $(wc -l < medicine_dataset.csv) records"
        log_info "Starting with 1000 records for quick setup..."
        python scripts/ingest_medicine_dataset.py --max-records 1000 --verify
    else
        log_warning "medicine_dataset.csv not found, using sample data..."
        python scripts/ingest_data.py --sample
    fi
    
    cd ..
    log_success "Data ingested!"
}

# Start development servers
start_dev_servers() {
    log_info "Starting development servers..."
    
    # Start backend in background
    log_info "Starting backend server..."
    cd backend
    source venv/bin/activate
    python main.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait a moment for backend to start
    sleep 3
    
    # Check if backend is running
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_success "Backend is running on http://localhost:8000"
    else
        log_error "Backend failed to start"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    
    # Start frontend
    log_info "Starting frontend server..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    log_success "Development servers started!"
    log_info "Backend: http://localhost:8000"
    log_info "Frontend: http://localhost:3000"
    log_info "API Docs: http://localhost:8000/docs"
    
    # Create cleanup function
    cleanup() {
        log_info "Stopping servers..."
        kill $BACKEND_PID 2>/dev/null || true
        kill $FRONTEND_PID 2>/dev/null || true
        exit 0
    }
    
    # Trap SIGINT and SIGTERM
    trap cleanup SIGINT SIGTERM
    
    log_info "Press Ctrl+C to stop all servers"
    
    # Wait for user to stop
    wait
}

# Main execution
main() {
    check_prerequisites
    setup_backend
    setup_frontend
    
    if start_elasticsearch; then
        create_demo_user
        ingest_sample_data
        
        echo ""
        log_success "🎉 Setup complete!"
        echo ""
        log_info "Demo login credentials:"
        echo "  Username: demo"
        echo "  Password: password123"
        echo ""
        
        read -p "Start development servers now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            start_dev_servers
        else
            log_info "To start servers later, run:"
            echo "  make start-dev"
            echo "  or"
            echo "  ./quick-start.sh --dev-only"
        fi
    else
        log_error "Setup failed - Elasticsearch is required"
        exit 1
    fi
}

# Handle command line arguments
if [ "$1" = "--dev-only" ]; then
    start_dev_servers
else
    main
fi
