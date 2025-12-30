#!/bin/bash

# Script to restart all HSC project services
# Usage: sudo bash restart_all_services.sh

set -e

echo "========================================="
echo "Restarting HSC Project Services"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Services to restart
SERVICES=(
    "gunicorn.service"
    "nginx"
    "celery-worker"
    "celery-beat"
    "rubika-bot"
)

# Function to restart service
restart_service() {
    local service=$1
    echo -e "${YELLOW}Restarting $service...${NC}"
    
    if systemctl restart "$service" 2>/dev/null; then
        sleep 2
        if systemctl is-active --quiet "$service"; then
            echo -e "${GREEN}✓ $service restarted successfully${NC}"
            return 0
        else
            echo -e "${RED}✗ $service restarted but is not active${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Failed to restart $service${NC}"
        return 1
    fi
}

# Restart each service
FAILED_SERVICES=()
ALL_SUCCESS=true

for service in "${SERVICES[@]}"; do
    if ! restart_service "$service"; then
        FAILED_SERVICES+=("$service")
        ALL_SUCCESS=false
    fi
    echo ""
done

echo "========================================="

# Summary
if [ "$ALL_SUCCESS" = true ]; then
    echo -e "${GREEN}All services restarted successfully! ✓${NC}"
    echo ""
    echo "Current status:"
    for service in "${SERVICES[@]}"; do
        status=$(systemctl is-active "$service" 2>/dev/null || echo "unknown")
        echo "  $service: $status"
    done
    echo ""
    exit 0
else
    echo -e "${RED}Some services failed to restart ✗${NC}"
    echo ""
    echo "Failed services:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo -e "  ${RED}- $service${NC}"
    done
    echo ""
    echo "To troubleshoot:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo "  sudo systemctl status $service"
        echo "  sudo journalctl -u $service -n 50"
    done
    echo ""
    exit 1
fi

