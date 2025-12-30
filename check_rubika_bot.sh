#!/bin/bash

# بررسی وضعیت Rubika Bot
# Usage: sudo bash check_rubika_bot.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================="
echo "بررسی وضعیت Rubika Bot"
echo "========================================="
echo ""

PROJECT_DIR="/var/www/HSC"
VENV_DIR="$PROJECT_DIR/venv"
ERRORS=0

# 1. Check service
echo "1. بررسی سرویس:"
echo "----------------------------------------"
if systemctl is-active --quiet rubika-bot; then
    echo -e "${GREEN}✓ سرویس rubika-bot فعال است${NC}"
    systemctl status rubika-bot --no-pager -l | head -15
else
    echo -e "${RED}✗ سرویس rubika-bot فعال نیست${NC}"
    ((ERRORS++))
    systemctl status rubika-bot --no-pager -l | head -10
fi
echo ""

# 2. Check process
echo "2. بررسی پروسه:"
echo "----------------------------------------"
if pgrep -f "run_rubika_bot\|rubika" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ پروسه Rubika Bot در حال اجرا است${NC}"
    ps aux | grep -E "run_rubika_bot|rubika" | grep -v grep | head -5
else
    echo -e "${RED}✗ پروسه Rubika Bot یافت نشد${NC}"
    ((ERRORS++))
fi
echo ""

# 3. Check logs
echo "3. بررسی لاگ‌های اخیر:"
echo "----------------------------------------"
RECENT_ERRORS=$(journalctl -u rubika-bot --since "1 hour ago" --no-pager 2>/dev/null | grep -i "error\|exception\|failed\|traceback" 2>/dev/null | wc -l || echo "0")

if [ "$RECENT_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✓ هیچ خطایی در لاگ در 1 ساعت گذشته${NC}"
elif [ "$RECENT_ERRORS" -lt 5 ]; then
    echo -e "${YELLOW}⚠ $RECENT_ERRORS خطا در لاگ در 1 ساعت گذشته${NC}"
else
    echo -e "${RED}✗ $RECENT_ERRORS خطا در لاگ در 1 ساعت گذشته${NC}"
    ((ERRORS++))
fi

echo ""
echo "آخرین خطوط لاگ:"
journalctl -u rubika-bot -n 10 --no-pager 2>/dev/null | tail -5
echo ""

# 4. Check Django connection (if bot uses Django)
echo "4. بررسی اتصال Django:"
echo "----------------------------------------"
if [ -d "$VENV_DIR" ] && [ -d "$PROJECT_DIR" ]; then
    cd "$PROJECT_DIR" 2>/dev/null
    if sudo -u hsc_admin "$VENV_DIR/bin/python" manage.py check --database default > /dev/null 2>&1; then
        echo -e "${GREEN}✓ اتصال به دیتابیس Django برقرار است${NC}"
    else
        echo -e "${RED}✗ اتصال به دیتابیس Django برقرار نیست${NC}"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠ Virtual environment یافت نشد${NC}"
fi
echo ""

# Summary
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Rubika Bot به درستی کار می‌کند!${NC}"
    exit 0
else
    echo -e "${RED}✗ $ERRORS مشکل یافت شد${NC}"
    echo ""
    echo "دستورات عیب‌یابی:"
    echo "  sudo systemctl status rubika-bot"
    echo "  sudo journalctl -u rubika-bot -n 100"
    echo "  sudo systemctl restart rubika-bot"
    exit 1
fi

