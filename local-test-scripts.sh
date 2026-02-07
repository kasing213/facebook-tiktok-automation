#!/bin/bash
# LOCAL E2E TEST SCRIPTS - NOT FOR PRODUCTION
# These scripts run tests in isolation using port 8080 mock backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Safety check to prevent running in CI/production
if [[ "$CI" == "true" ]] || [[ "$NODE_ENV" == "production" ]]; then
    echo -e "${RED}❌ LOCAL TEST SCRIPTS BLOCKED IN PRODUCTION ENVIRONMENT${NC}"
    echo "This is a safety measure to prevent conflicts with production systems."
    exit 1
fi

echo -e "${BLUE}🧪 Facebook-Automation Local E2E Test Runner${NC}"
echo -e "${YELLOW}⚠️  FOR LOCAL TESTING ONLY - NOT FOR PRODUCTION${NC}"
echo ""

# Function to start mock backend
start_mock_backend() {
    echo -e "${BLUE}📡 Starting mock backend on port 8080...${NC}"

    # Check if port 8080 is already in use
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port 8080 is already in use. Stopping existing process...${NC}"
        pkill -f "local-mock-server" || true
        sleep 2
    fi

    # Start mock server in background
    node local-mock-server.js > local-mock.log 2>&1 &
    MOCK_PID=$!
    echo $MOCK_PID > local-mock.pid

    # Wait for server to start
    echo -n "Waiting for mock server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/health >/dev/null 2>&1; then
            echo -e " ${GREEN}✅ Ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done

    echo -e " ${RED}❌ Failed to start mock server${NC}"
    return 1
}

# Function to start frontend with local env
start_frontend() {
    echo -e "${BLUE}🌐 Starting frontend with local configuration...${NC}"

    cd frontend

    # Check if .env.local exists
    if [[ ! -f ".env.local" ]]; then
        echo -e "${RED}❌ .env.local not found. Please create it first.${NC}"
        return 1
    fi

    # Start frontend in background
    npm run dev > ../local-frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../local-frontend.pid

    # Wait for frontend to start
    echo -n "Waiting for frontend to start..."
    for i in {1..60}; do
        if curl -s http://localhost:5173 >/dev/null 2>&1; then
            echo -e " ${GREEN}✅ Ready!${NC}"
            cd ..
            return 0
        fi
        echo -n "."
        sleep 1
    done

    echo -e " ${RED}❌ Failed to start frontend${NC}"
    cd ..
    return 1
}

# Function to run tests
run_tests() {
    echo -e "${BLUE}🧪 Running E2E tests...${NC}"

    cd frontend

    # Run specific test suites
    echo -e "${BLUE}Running core tests...${NC}"
    npm run test:core || TEST_FAILED=true

    if [[ "$TEST_FAILED" != "true" ]]; then
        echo -e "${BLUE}Running tenant tests...${NC}"
        npm run test:tenant || TEST_FAILED=true
    fi

    cd ..

    if [[ "$TEST_FAILED" == "true" ]]; then
        echo -e "${RED}❌ Some tests failed${NC}"
        return 1
    else
        echo -e "${GREEN}✅ All tests passed!${NC}"
        return 0
    fi
}

# Function to cleanup processes
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up local test processes...${NC}"

    # Stop frontend
    if [[ -f "local-frontend.pid" ]]; then
        PID=$(cat local-frontend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping frontend (PID: $PID)"
            kill $PID
        fi
        rm -f local-frontend.pid
    fi

    # Stop mock backend
    if [[ -f "local-mock.pid" ]]; then
        PID=$(cat local-mock.pid)
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping mock backend (PID: $PID)"
            kill $PID
        fi
        rm -f local-mock.pid
    fi

    # Clean up log files
    rm -f local-mock.log local-frontend.log

    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Start mock backend and frontend"
    echo "  test      - Run E2E tests"
    echo "  full      - Complete test run (setup + test + cleanup)"
    echo "  cleanup   - Stop all processes and clean up"
    echo "  logs      - Show service logs"
    echo ""
    echo "Examples:"
    echo "  $0 full              # Run complete test suite"
    echo "  $0 setup             # Start services only"
    echo "  $0 test              # Run tests (assumes services running)"
}

# Main command handling
case "${1:-full}" in
    "setup")
        start_mock_backend
        start_frontend
        echo -e "${GREEN}✅ Local test environment ready!${NC}"
        echo "Mock Backend: http://localhost:8080"
        echo "Frontend: http://localhost:5173"
        ;;
    "test")
        run_tests
        ;;
    "full")
        echo -e "${BLUE}🚀 Starting complete local test run...${NC}"
        cleanup  # Clean up any existing processes
        start_mock_backend
        start_frontend
        sleep 3  # Give services time to fully start
        run_tests
        TEST_RESULT=$?
        cleanup

        if [[ $TEST_RESULT -eq 0 ]]; then
            echo -e "${GREEN}🎉 Local E2E tests completed successfully!${NC}"
        else
            echo -e "${RED}💥 Local E2E tests failed${NC}"
            exit 1
        fi
        ;;
    "cleanup")
        cleanup
        ;;
    "logs")
        echo -e "${BLUE}📋 Service Logs:${NC}"
        echo -e "${YELLOW}=== Mock Backend ===${NC}"
        [[ -f "local-mock.log" ]] && tail -20 local-mock.log || echo "No mock backend log found"
        echo -e "${YELLOW}=== Frontend ===${NC}"
        [[ -f "local-frontend.log" ]] && tail -20 local-frontend.log || echo "No frontend log found"
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
