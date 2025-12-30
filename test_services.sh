#!/bin/bash

# Advanced test script to verify all HSC services are working correctly
# Usage: sudo bash test_services.sh

set -e

echo "========================================="
echo "HSC Project Services - Comprehensive Test"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Services to test
SERVICES=(
    "gunicorn.service"
    "nginx"
    "celery-worker"
    "celery-beat"
    "rubika-bot"
)

# Test results
PASSED=0
FAILED=0
FAILED_TESTS=()

# Function to test service
test_service() {
    local service=$1
    local status=$(systemctl is-active "$service" 2>/dev/null || echo "not-found")
    
    echo -e "${BLUE}Testing $service...${NC}"
    
    # Check if service exists
    if [ "$status" = "not-found" ]; then
        echo -e "  ${RED}✗ Service not found${NC}"
        ((FAILED++))
        FAILED_TESTS+=("$service: NOT FOUND")
        return 1
    fi
    
    # Check if service is active
    if [ "$status" != "active" ]; then
        echo -e "  ${RED}✗ Service is not active (status: $status)${NC}"
        ((FAILED++))
        FAILED_TESTS+=("$service: NOT ACTIVE ($status)")
        return 1
    fi
    
    # Check if service is enabled
    local enabled=$(systemctl is-enabled "$service" 2>/dev/null || echo "unknown")
    if [ "$enabled" != "enabled" ] && [ "$enabled" != "static" ]; then
        echo -e "  ${YELLOW}⚠ Service is not enabled (will not start on boot)${NC}"
    fi
    
    # Check recent errors in logs (last 100 lines)
    local error_count=$(journalctl -u "$service" -n 100 --no-pager 2>/dev/null | grep -i "error\|failed\|exception" | wc -l || echo "0")
    if [ "$error_count" -gt 5 ]; then
        echo -e "  ${YELLOW}⚠ Found $error_count potential errors in recent logs${NC}"
    fi
    
    # Service-specific tests
    case "$service" in
        nginx)
            # Test nginx configuration
            if nginx -t 2>/dev/null; then
                echo -e "  ${GREEN}✓ Nginx configuration is valid${NC}"
            else
                echo -e "  ${RED}✗ Nginx configuration has errors${NC}"
                ((FAILED++))
                FAILED_TESTS+=("$service: CONFIG ERROR")
                return 1
            fi
            ;;
        gunicorn.service)
            # Check if gunicorn process is running
            if pgrep -f "gunicorn" > /dev/null; then
                echo -e "  ${GREEN}✓ Gunicorn process is running${NC}"
            else
                echo -e "  ${RED}✗ Gunicorn process not found${NC}"
                ((FAILED++))
                FAILED_TESTS+=("$service: PROCESS NOT RUNNING")
                return 1
            fi
            ;;
        celery-worker)
            # Check if celery worker process is running
            if pgrep -f "celery.*worker" > /dev/null; then
                echo -e "  ${GREEN}✓ Celery worker process is running${NC}"
            else
                echo -e "  ${RED}✗ Celery worker process not found${NC}"
                ((FAILED++))
                FAILED_TESTS+=("$service: PROCESS NOT RUNNING")
                return 1
            fi
            ;;
        celery-beat)
            # Check if celery beat process is running
            if pgrep -f "celery.*beat" > /dev/null; then
                echo -e "  ${GREEN}✓ Celery beat process is running${NC}"
            else
                echo -e "  ${RED}✗ Celery beat process not found${NC}"
                ((FAILED++))
                FAILED_TESTS+=("$service: PROCESS NOT RUNNING")
                return 1
            fi
            ;;
        rubika-bot)
            # Check if rubika bot process is running
            if pgrep -f "run_rubika_bot\|rubika" > /dev/null; then
                echo -e "  ${GREEN}✓ Rubika bot process is running${NC}"
            else
                echo -e "  ${RED}✗ Rubika bot process not found${NC}"
                ((FAILED++))
                FAILED_TESTS+=("$service: PROCESS NOT RUNNING")
                return 1
            fi
            ;;
    esac
    
    echo -e "  ${GREEN}✓ $service is working correctly${NC}"
    ((PASSED++))
    return 0
}

# Run tests
echo "Running comprehensive tests..."
echo ""

for service in "${SERVICES[@]}"; do
    test_service "$service"
    echo ""
done

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All services are working correctly!${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some services have issues:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}- $test${NC}"
    done
    echo ""
    echo "To troubleshoot:"
    echo "  sudo systemctl status <service-name>"
    echo "  sudo journalctl -u <service-name> -n 100"
    echo ""
    exit 1
fi

