#!/bin/bash

# Script to check status of all HSC project services
# Usage: sudo bash check_services_status.sh

set -e

echo "========================================="
echo "HSC Project Services Status Check"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Services to check
SERVICES=(
    "gunicorn.service"
    "nginx"
    "celery-worker"
    "celery-beat"
    "rubika-bot"
)

# Function to check service status
check_service() {
    local service=$1
    local status=$(systemctl is-active "$service" 2>/dev/null || echo "not-found")
    
    if [ "$status" = "active" ]; then
        echo -e "${GREEN}✓${NC} $service: ${GREEN}ACTIVE${NC}"
        return 0
    elif [ "$status" = "not-found" ]; then
        echo -e "${RED}✗${NC} $service: ${RED}NOT FOUND${NC}"
        return 1
    else
        echo -e "${RED}✗${NC} $service: ${RED}$status${NC}"
        return 1
    fi
}

# Check each service
FAILED_SERVICES=()
ALL_ACTIVE=true

for service in "${SERVICES[@]}"; do
    if ! check_service "$service"; then
        FAILED_SERVICES+=("$service")
        ALL_ACTIVE=false
    fi
done

echo ""
echo "========================================="

# Summary
if [ "$ALL_ACTIVE" = true ]; then
    echo -e "${GREEN}All services are ACTIVE ✓${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}Some services are NOT active ✗${NC}"
    echo ""
    echo "Failed services:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo -e "  ${RED}- $service${NC}"
    done
    echo ""
    echo "To view detailed status:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo "  sudo systemctl status $service"
    done
    echo ""
    exit 1
fi

