#!/bin/bash

# Grantha Unified Development Runner
# Similar to deepwiki-open setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values from .env
DEFAULT_API_PORT=8000
DEFAULT_FRONTEND_PORT=3000

# Load environment variables if .env exists
if [ -f ".env" ]; then
    source .env
    echo -e "${GREEN}✓${NC} Loaded environment from .env"
else
    echo -e "${YELLOW}⚠${NC} No .env file found, using defaults"
fi

API_PORT=${API_PORT:-$DEFAULT_API_PORT}
FRONTEND_PORT=${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}

function print_usage() {
    echo -e "${BLUE}Grantha Development Runner${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  api           Start only the Python API server (port $API_PORT)"
    echo "  frontend      Start only the frontend development server (port $FRONTEND_PORT)"
    echo "  dev           Start both API and frontend in development mode"
    echo "  build         Build the frontend for production"
    echo "  install       Install all dependencies"
    echo "  setup         Full setup: install dependencies and create .env from template"
    echo "  clean         Clean all build artifacts and dependencies"
    echo "  test          Run all tests"
    echo "  lint          Run linting and formatting"
    echo "  help          Show this help message"
    echo ""
}

function check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗${NC} Python 3 is required but not installed"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Python $(python3 --version | cut -d' ' -f2) found"
}

function check_node() {
    if ! command -v node &> /dev/null; then
        echo -e "${RED}✗${NC} Node.js is required but not installed"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    MAJOR_VERSION=$(echo $NODE_VERSION | cut -d'.' -f1)
    
    if [ "$MAJOR_VERSION" -lt 20 ]; then
        echo -e "${RED}✗${NC} Node.js v20+ is required, but v$NODE_VERSION is installed"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Node.js v$NODE_VERSION found"
}

function check_pnpm() {
    if ! command -v pnpm &> /dev/null; then
        echo -e "${YELLOW}⚠${NC} pnpm not found, installing..."
        npm install -g pnpm
    fi
    echo -e "${GREEN}✓${NC} pnpm $(pnpm --version) found"
}

function setup_python_env() {
    echo -e "${BLUE}Setting up Python environment...${NC}"
    
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    pip install -e .
    
    echo -e "${GREEN}✓${NC} Python environment ready"
}

function install_frontend_deps() {
    echo -e "${BLUE}Installing frontend dependencies...${NC}"
    cd frontend
    pnpm install
    cd ..
    echo -e "${GREEN}✓${NC} Frontend dependencies installed"
}

function start_api() {
    echo -e "${BLUE}Starting API server on port $API_PORT...${NC}"
    source venv/bin/activate
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
    
    if [ "$API_RELOAD" = "true" ]; then
        python -m uvicorn src.grantha.api.app:create_app --factory --reload --host $API_HOST --port $API_PORT
    else
        python -m uvicorn src.grantha.api.app:create_app --factory --host $API_HOST --port $API_PORT
    fi
}

function start_frontend() {
    echo -e "${BLUE}Starting frontend development server on port $FRONTEND_PORT...${NC}"
    cd frontend
    pnpm run dev
}

function start_dev() {
    echo -e "${BLUE}Starting Grantha in development mode...${NC}"
    echo -e "${GREEN}API:${NC}      http://localhost:$API_PORT"
    echo -e "${GREEN}Frontend:${NC} http://localhost:$FRONTEND_PORT"
    echo -e "${GREEN}API Docs:${NC} http://localhost:$API_PORT/docs"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
    
    # Start API in background
    (start_api) &
    API_PID=$!
    
    # Wait a moment for API to start
    sleep 3
    
    # Start frontend in background
    (start_frontend) &
    FRONTEND_PID=$!
    
    # Function to cleanup on exit
    cleanup() {
        echo -e "\n${YELLOW}Stopping servers...${NC}"
        kill $API_PID 2>/dev/null
        kill $FRONTEND_PID 2>/dev/null
        exit
    }
    
    # Set trap to cleanup on script exit
    trap cleanup SIGINT SIGTERM
    
    # Wait for both processes
    wait $API_PID $FRONTEND_PID
}

function build_frontend() {
    echo -e "${BLUE}Building frontend for production...${NC}"
    cd frontend
    pnpm run build
    cd ..
    echo -e "${GREEN}✓${NC} Frontend built successfully"
}

function install_all() {
    check_python
    check_node
    check_pnpm
    setup_python_env
    install_frontend_deps
    echo -e "${GREEN}✓${NC} All dependencies installed"
}

function setup_project() {
    echo -e "${BLUE}Setting up Grantha project...${NC}"
    
    # Create .env from template if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}✓${NC} Created .env from template"
            echo -e "${YELLOW}⚠${NC} Please update .env with your API keys"
        else
            echo -e "${RED}✗${NC} No .env.example found"
            exit 1
        fi
    fi
    
    # Create logs directory
    mkdir -p logs
    
    install_all
    echo -e "${GREEN}✓${NC} Project setup complete!"
}

function clean_all() {
    echo -e "${BLUE}Cleaning build artifacts and dependencies...${NC}"
    
    # Clean Python
    rm -rf venv __pycache__ .pytest_cache build dist *.egg-info
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Clean frontend
    rm -rf frontend/node_modules frontend/.svelte-kit frontend/dist
    
    # Clean logs
    rm -rf logs/*.log
    
    echo -e "${GREEN}✓${NC} Cleaned successfully"
}

function run_tests() {
    echo -e "${BLUE}Running tests...${NC}"
    source venv/bin/activate
    python -m pytest tests/
    
    cd frontend
    pnpm run test
    cd ..
    
    echo -e "${GREEN}✓${NC} All tests passed"
}

function run_lint() {
    echo -e "${BLUE}Running linting and formatting...${NC}"
    
    # Python linting
    source venv/bin/activate
    black src/ tests/
    isort src/ tests/
    
    # Frontend linting
    cd frontend
    pnpm run lint
    pnpm run format
    cd ..
    
    echo -e "${GREEN}✓${NC} Linting complete"
}

# Main command handling
case "${1:-help}" in
    "api")
        check_python
        start_api
        ;;
    "frontend")
        check_node
        check_pnpm
        start_frontend
        ;;
    "dev")
        check_python
        check_node
        check_pnpm
        start_dev
        ;;
    "build")
        check_node
        check_pnpm
        build_frontend
        ;;
    "install")
        install_all
        ;;
    "setup")
        setup_project
        ;;
    "clean")
        clean_all
        ;;
    "test")
        check_python
        check_node
        check_pnpm
        run_tests
        ;;
    "lint")
        check_python
        check_node
        check_pnpm
        run_lint
        ;;
    "help"|*)
        print_usage
        ;;
esac