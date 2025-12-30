#!/bin/bash

# بررسی کامل تمام سرویس‌های HSC
# Usage: sudo bash check_all_services.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================="
echo "بررسی کامل تمام سرویس‌های HSC"
echo "========================================="
echo ""

# Services
SERVICES=(
    "gunicorn.service"
    "nginx"
    "celery-worker"
    "celery-beat"
    "rubika-bot"
)

ALL_OK=true
FAILED=()

# Check each service
for service in "${SERVICES[@]}"; do
    echo -n "بررسی $service... "
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo -e "${GREEN}✓ فعال${NC}"
    else
        status=$(systemctl is-active "$service" 2>/dev/null || echo "not-found")
        echo -e "${RED}✗ $status${NC}"
        ALL_OK=false
        FAILED+=("$service")
    fi
done

echo ""
echo "========================================="

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✓ تمام سرویس‌ها فعال هستند${NC}"
    echo ""
    
    # بررسی جزئیات
    echo "جزئیات:"
    echo "----------------------------------------"
    for service in "${SERVICES[@]}"; do
        echo ""
        echo "$service:"
        systemctl status "$service" --no-pager -l | head -8 | tail -5
    done
    exit 0
else
    echo -e "${RED}✗ برخی سرویس‌ها فعال نیستند${NC}"
    echo ""
    echo "سرویس‌های غیرفعال:"
    for service in "${FAILED[@]}"; do
        echo -e "  ${RED}- $service${NC}"
    done
    echo ""
    echo "برای راه‌اندازی:"
    echo "  sudo systemctl start ${FAILED[*]}"
    echo ""
    exit 1
fi

