#!/bin/bash

# Comprehensive service management script for HSC project
# Usage: 
#   sudo bash service_manager.sh status    - Check all services
#   sudo bash service_manager.sh restart   - Restart all services
#   sudo bash service_manager.sh start     - Start all services
#   sudo bash service_manager.sh stop      - Stop all services
#   sudo bash service_manager.sh logs      - View logs

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Services
SERVICES=(
    "gunicorn.service"
    "nginx"
    "celery-worker"
    "celery-beat"
    "rubika-bot"
)

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Function to check service status
check_status() {
    echo "========================================="
    echo "HSC Project Services Status"
    echo "========================================="
    echo ""
    
    ALL_ACTIVE=true
    FAILED_SERVICES=()
    
    for service in "${SERVICES[@]}"; do
        local status=$(systemctl is-active "$service" 2>/dev/null || echo "not-found")
        local enabled=$(systemctl is-enabled "$service" 2>/dev/null || echo "unknown")
        
        if [ "$status" = "active" ]; then
            echo -e "${GREEN}✓${NC} $service"
            echo "    Status: ${GREEN}$status${NC}"
            echo "    Enabled: $enabled"
        elif [ "$status" = "not-found" ]; then
            echo -e "${RED}✗${NC} $service"
            echo "    Status: ${RED}NOT FOUND${NC}"
            ALL_ACTIVE=false
            FAILED_SERVICES+=("$service")
        else
            echo -e "${RED}✗${NC} $service"
            echo "    Status: ${RED}$status${NC}"
            echo "    Enabled: $enabled"
            ALL_ACTIVE=false
            FAILED_SERVICES+=("$service")
        fi
        echo ""
    done
    
    echo "========================================="
    if [ "$ALL_ACTIVE" = true ]; then
        echo -e "${GREEN}All services are ACTIVE ✓${NC}"
    else
        echo -e "${RED}Some services are NOT active ✗${NC}"
    fi
    echo ""
}

# Function to manage services (start/stop/restart)
manage_services() {
    local action=$1
    local action_upper=$(echo "$action" | tr '[:lower:]' '[:upper:]')
    
    echo "========================================="
    echo "$action_upper HSC Project Services"
    echo "========================================="
    echo ""
    
    ALL_SUCCESS=true
    FAILED_SERVICES=()
    
    for service in "${SERVICES[@]}"; do
        echo -e "${YELLOW}$action_upper $service...${NC}"
        
        if systemctl "$action" "$service" 2>/dev/null; then
            sleep 2
            if [ "$action" = "restart" ] || [ "$action" = "start" ]; then
                if systemctl is-active --quiet "$service"; then
                    echo -e "${GREEN}✓ $service ${action}ed successfully${NC}"
                else
                    echo -e "${RED}✗ $service ${action}ed but is not active${NC}"
                    ALL_SUCCESS=false
                    FAILED_SERVICES+=("$service")
                fi
            else
                echo -e "${GREEN}✓ $service ${action}ed successfully${NC}"
            fi
        else
            echo -e "${RED}✗ Failed to $action $service${NC}"
            ALL_SUCCESS=false
            FAILED_SERVICES+=("$service")
        fi
        echo ""
    done
    
    echo "========================================="
    if [ "$ALL_SUCCESS" = true ]; then
        echo -e "${GREEN}All services ${action}ed successfully! ✓${NC}"
    else
        echo -e "${RED}Some services failed to $action ✗${NC}"
        for service in "${FAILED_SERVICES[@]}"; do
            echo -e "  ${RED}- $service${NC}"
        done
    fi
    echo ""
}

# Function to view logs
view_logs() {
    echo "========================================="
    echo "HSC Project Services Logs"
    echo "========================================="
    echo ""
    echo "Select a service to view logs:"
    echo ""
    
    for i in "${!SERVICES[@]}"; do
        echo "  $((i+1)). ${SERVICES[$i]}"
    done
    echo "  $(( ${#SERVICES[@]} + 1 )). All services (last 50 lines each)"
    echo ""
    read -p "Enter choice [1-$(( ${#SERVICES[@]} + 1 ))]: " choice
    
    if [ "$choice" -ge 1 ] && [ "$choice" -le "${#SERVICES[@]}" ]; then
        service="${SERVICES[$((choice-1))]}"
        echo ""
        echo -e "${BLUE}Viewing logs for $service (Press Ctrl+C to exit)${NC}"
        echo ""
        journalctl -u "$service" -f --no-pager
    elif [ "$choice" -eq $(( ${#SERVICES[@]} + 1 )) ]; then
        echo ""
        for service in "${SERVICES[@]}"; do
            echo "========================================="
            echo "Logs for $service (last 50 lines):"
            echo "========================================="
            journalctl -u "$service" -n 50 --no-pager
            echo ""
        done
    else
        echo -e "${RED}Invalid choice${NC}"
        exit 1
    fi
}

# Main script logic
case "${1:-status}" in
    status)
        check_status
        ;;
    restart)
        manage_services "restart"
        check_status
        ;;
    start)
        manage_services "start"
        check_status
        ;;
    stop)
        manage_services "stop"
        check_status
        ;;
    logs)
        view_logs
        ;;
    *)
        echo "Usage: $0 {status|restart|start|stop|logs}"
        echo ""
        echo "Commands:"
        echo "  status   - Check status of all services"
        echo "  restart  - Restart all services"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  logs     - View logs interactively"
        exit 1
        ;;
esac

