#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to load environment variables (only when needed)
load_env() {
    if [ -f .env ]; then
        # Properly handle .env file with spaces and special characters
        set -a
        source .env
        set +a
        echo -e "${GREEN}✓${NC} Loaded environment from .env"
    else
        echo -e "${YELLOW}⚠${NC} No .env file found, using defaults"
    fi
}

# Check dependencies
check_dependencies() {
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
    else
        echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.10+"
        exit 1
    fi

    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION found"
    else
        echo -e "${RED}✗${NC} Node.js not found. Please install Node.js 20+"
        exit 1
    fi

    # Check pnpm
    if command -v pnpm &> /dev/null; then
        PNPM_VERSION=$(pnpm --version)
        echo -e "${GREEN}✓${NC} pnpm $PNPM_VERSION found"
    else
        echo -e "${YELLOW}⚠${NC} pnpm not found. Installing..."
        npm install -g pnpm
    fi
}

# Start API server
start_api() {
    load_env
    echo -e "${BLUE}Starting API server on port 8000...${NC}"
    cd "$(dirname "$0")"
    python3 -m uvicorn src.grantha.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000
}

# Start frontend
start_frontend() {
    load_env
    echo -e "${BLUE}Starting frontend development server on port 3000...${NC}"
    cd "$(dirname "$0")/frontend"
    pnpm dev --host --port 3000
}

# Start both API and frontend
start_dev() {
    check_dependencies
    load_env
    
    echo -e "${BLUE}Starting Grantha in development mode...${NC}"
    echo -e "${GREEN}API:${NC}      http://localhost:8000"
    echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
    echo -e "${GREEN}API Docs:${NC} http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"

    # Start API in background
    start_api &
    API_PID=$!
    
    # Wait a moment for API to start
    sleep 3
    
    # Start frontend in background
    start_frontend &
    FRONTEND_PID=$!
    
    # Wait for both processes
    trap "kill $API_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait $API_PID $FRONTEND_PID
}

# Build frontend for production
build_frontend() {
    echo -e "${BLUE}Building frontend for production...${NC}"
    cd "$(dirname "$0")/frontend"
    pnpm build
    echo -e "${GREEN}✓${NC} Frontend built successfully"
}

# Install dependencies
install_deps() {
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    pip install -r requirements.txt 2>/dev/null || pip install uv && uv pip install -r pyproject.toml
    
    echo -e "${BLUE}Installing frontend dependencies...${NC}"
    cd "$(dirname "$0")/frontend"
    pnpm install
    echo -e "${GREEN}✓${NC} All dependencies installed"
}

# Setup project
setup_project() {
    echo -e "${BLUE}Setting up Grantha project...${NC}"
    
    # Create .env from template if doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} Created .env from template"
    fi
    
    # Install dependencies
    install_deps
    
    # Sync SvelteKit
    cd "$(dirname "$0")/frontend"
    pnpm exec svelte-kit sync
    
    echo -e "${GREEN}✓${NC} Project setup complete!"
}

# Stop running services
stop_services() {
    echo -e "${BLUE}Stopping Grantha services...${NC}"
    
    # Kill Python/Uvicorn processes
    if pgrep -f "uvicorn.*grantha" > /dev/null; then
        pkill -f "uvicorn.*grantha"
        echo -e "${GREEN}✓${NC} Stopped API server"
    else
        echo -e "${YELLOW}⚠${NC} API server not running"
    fi
    
    # Kill Vite/Node processes for frontend
    if pgrep -f "vite.*dev.*port.*3000" > /dev/null; then
        pkill -f "vite.*dev.*port.*3000"
        echo -e "${GREEN}✓${NC} Stopped frontend server"
    else
        echo -e "${YELLOW}⚠${NC} Frontend server not running"
    fi
    
    # Also check for processes on specific ports
    if lsof -ti:8000 > /dev/null 2>&1; then
        kill -9 $(lsof -ti:8000) 2>/dev/null
        echo -e "${GREEN}✓${NC} Cleared port 8000"
    fi
    
    if lsof -ti:3000 > /dev/null 2>&1; then
        kill -9 $(lsof -ti:3000) 2>/dev/null
        echo -e "${GREEN}✓${NC} Cleared port 3000"
    fi
    
    echo -e "${GREEN}✓${NC} All services stopped"
}

# Clean build artifacts
clean() {
    echo -e "${BLUE}Cleaning build artifacts...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -type f -name "*.pyc" -delete 2>/dev/null
    rm -rf frontend/.svelte-kit frontend/build frontend/node_modules/.cache
    rm -rf logs/*.log
    echo -e "${GREEN}✓${NC} Cleaned build artifacts"
}

# Run tests
run_tests() {
    echo -e "${BLUE}Running tests...${NC}"
    
    # Python tests
    echo -e "${BLUE}Running Python tests...${NC}"
    pytest tests/
    
    # Frontend tests
    echo -e "${BLUE}Running frontend tests...${NC}"
    cd "$(dirname "$0")/frontend"
    pnpm test
}

# Lint code
lint() {
    echo -e "${BLUE}Running linters...${NC}"
    
    # Python linting
    echo -e "${BLUE}Linting Python code...${NC}"
    ruff check src/ tests/ || black src/ tests/
    
    # Frontend linting
    echo -e "${BLUE}Linting frontend code...${NC}"
    cd "$(dirname "$0")/frontend"
    pnpm lint
}

# Show help
show_help() {
    echo -e "${BLUE}Grantha Development Runner${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  api           Start only the Python API server (port 8000)"
    echo "  frontend      Start only the frontend development server (port 3000)"
    echo "  dev           Start both API and frontend in development mode"
    echo "  stop          Stop all running Grantha services"
    echo "  build         Build the frontend for production"
    echo "  install       Install all dependencies"
    echo "  setup         Full setup: install dependencies and create .env from template"
    echo "  clean         Clean all build artifacts and dependencies"
    echo "  test          Run all tests"
    echo "  lint          Run linting and formatting"
    echo "  help          Show this help message"
}

# Main command handler
case "${1}" in
    api)
        check_dependencies
        start_api
        ;;
    frontend)
        check_dependencies
        start_frontend
        ;;
    dev)
        start_dev
        ;;
    stop)
        stop_services
        ;;
    build)
        build_frontend
        ;;
    install)
        install_deps
        ;;
    setup)
        setup_project
        ;;
    clean)
        clean
        ;;
    test)
        run_tests
        ;;
    lint)
        lint
        ;;
    help|--help|-h)
        show_help
        ;;
    ""|*)
        if [ -z "$1" ]; then
            start_dev
        else
            echo -e "${RED}Unknown command: $1${NC}"
            show_help
            exit 1
        fi
        ;;
esac