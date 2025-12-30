#!/bin/bash

# Stash تغییرات محلی و pull کردن
# Usage: bash git_stash_and_pull.sh

echo "========================================="
echo "Stash تغییرات و Pull"
echo "========================================="
echo ""

# بررسی وضعیت git
echo "1. بررسی وضعیت Git:"
echo "----------------------------------------"
git status --short

echo ""
echo "2. Stash کردن تغییرات محلی:"
echo "----------------------------------------"
git stash push -m "Local changes before pull - $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo "3. Pull کردن تغییرات:"
echo "----------------------------------------"
git pull

echo ""
echo "4. بررسی تغییرات Stash شده:"
echo "----------------------------------------"
git stash list | head -5

echo ""
echo "========================================="
echo "✓ انجام شد"
echo "========================================="
echo ""
echo "اگر می‌خواهید تغییرات stash شده را برگردانید:"
echo "  git stash pop"
echo ""
echo "اگر می‌خواهید تغییرات stash شده را ببینید:"
echo "  git stash show -p stash@{0}"
echo ""

