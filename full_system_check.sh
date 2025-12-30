#!/bin/bash

# بررسی کامل سیستم - تمام سرویس‌ها و تسک‌ها
# Usage: sudo bash full_system_check.sh

set -e

echo "========================================="
echo "بررسی کامل سیستم HSC"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Run all checks
echo -e "${BLUE}1. بررسی سرویس‌های اصلی...${NC}"
echo "----------------------------------------"
bash check_services_status.sh
echo ""

echo -e "${BLUE}2. بررسی کامل تسک‌های Celery...${NC}"
echo "----------------------------------------"
bash test_celery_tasks.sh
echo ""

echo "========================================="
echo -e "${GREEN}بررسی کامل انجام شد${NC}"
echo "========================================="

