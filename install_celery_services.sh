#!/bin/bash

# Script to install and setup Celery services + Rubika Bot
# Run with sudo: sudo bash install_celery_services.sh

set -e

echo "========================================="
echo "Installing Services for HSC Project"
echo "  - Celery Worker"
echo "  - Celery Beat"
echo "  - Rubika Bot"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Variables
PROJECT_DIR="/var/www/HSC"
LOGS_DIR="$PROJECT_DIR/logs"
SERVICE_DIR="/etc/systemd/system"

# Create logs directory if not exists
echo "Creating logs directory..."
mkdir -p "$LOGS_DIR"
chown hsc_admin:hsc_admin "$LOGS_DIR"

# Copy service files
echo "Copying service files..."
cp celery-worker.service "$SERVICE_DIR/"
cp celery-beat.service "$SERVICE_DIR/"
cp rubika-bot.service "$SERVICE_DIR/"

# Set permissions
chmod 644 "$SERVICE_DIR/celery-worker.service"
chmod 644 "$SERVICE_DIR/celery-beat.service"
chmod 644 "$SERVICE_DIR/rubika-bot.service"

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
echo "Enabling services..."
systemctl enable celery-worker.service
systemctl enable celery-beat.service
systemctl enable rubika-bot.service

# Stop services if running (to restart with new config)
echo "Stopping old services if running..."
systemctl stop celery-worker.service 2>/dev/null || true
systemctl stop celery-beat.service 2>/dev/null || true
systemctl stop rubika-bot.service 2>/dev/null || true

# Start services
echo "Starting services..."
systemctl start celery-worker.service
systemctl start celery-beat.service
systemctl start rubika-bot.service

# Check status
echo ""
echo "========================================="
echo "Service Status:"
echo "========================================="
systemctl status celery-worker.service --no-pager
echo ""
echo "----------------------------------------"
echo ""
systemctl status celery-beat.service --no-pager
echo ""
echo "----------------------------------------"
echo ""
systemctl status rubika-bot.service --no-pager

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Useful commands:"
echo ""
echo "Check Status:"
echo "  - Worker:      sudo systemctl status celery-worker"
echo "  - Beat:        sudo systemctl status celery-beat"
echo "  - Rubika Bot:  sudo systemctl status rubika-bot"
echo ""
echo "View Logs:"
echo "  - Worker:      sudo journalctl -u celery-worker -f"
echo "  - Beat:        sudo journalctl -u celery-beat -f"
echo "  - Rubika Bot:  sudo journalctl -u rubika-bot -f"
echo ""
echo "Restart Services:"
echo "  - Worker:      sudo systemctl restart celery-worker"
echo "  - Beat:        sudo systemctl restart celery-beat"
echo "  - Rubika Bot:  sudo systemctl restart rubika-bot"
echo ""
echo "Stop Services:"
echo "  - Worker:      sudo systemctl stop celery-worker"
echo "  - Beat:        sudo systemctl stop celery-beat"
echo "  - Rubika Bot:  sudo systemctl stop rubika-bot"
echo ""
echo "Start All:       sudo systemctl start celery-worker celery-beat rubika-bot"
echo "Stop All:        sudo systemctl stop celery-worker celery-beat rubika-bot"
echo "Restart All:     sudo systemctl restart celery-worker celery-beat rubika-bot"
echo ""
