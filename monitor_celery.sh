#!/bin/bash

# اسکریپت مانیتورینگ Celery برای سرور
# این فایل را در سرور در مسیر /usr/local/bin/monitor_celery.sh کپی کنید

LOG_FILE="/var/log/celery-monitor.log"
ALERT_LOG="/var/log/celery-alerts.log"
MAX_QUEUE_SIZE=100

echo "=== Celery Monitor - $(date) ===" >> "$LOG_FILE"

# بررسی Celery Worker
if ! systemctl is-active --quiet celery.service; then
    echo "⚠️ $(date): Celery worker is DOWN! Attempting restart..." >> "$ALERT_LOG"
    systemctl restart celery.service
    sleep 5
    if systemctl is-active --quiet celery.service; then
        echo "✅ $(date): Celery worker restarted successfully" >> "$ALERT_LOG"
    else
        echo "❌ $(date): Failed to restart Celery worker!" >> "$ALERT_LOG"
    fi
else
    echo "✅ Celery worker: Running" >> "$LOG_FILE"
fi

# بررسی Celery Beat
if ! systemctl is-active --quiet celery-beat.service; then
    echo "⚠️ $(date): Celery beat is DOWN! Attempting restart..." >> "$ALERT_LOG"
    systemctl restart celery-beat.service
    sleep 5
    if systemctl is-active --quiet celery-beat.service; then
        echo "✅ $(date): Celery beat restarted successfully" >> "$ALERT_LOG"
    else
        echo "❌ $(date): Failed to restart Celery beat!" >> "$ALERT_LOG"
    fi
else
    echo "✅ Celery beat: Running" >> "$LOG_FILE"
fi

# بررسی Redis
if ! systemctl is-active --quiet redis.service && ! systemctl is-active --quiet redis-server.service; then
    echo "⚠️ $(date): Redis is DOWN! Attempting restart..." >> "$ALERT_LOG"
    systemctl restart redis 2>/dev/null || systemctl restart redis-server 2>/dev/null
    sleep 3
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ $(date): Redis restarted successfully" >> "$ALERT_LOG"
    else
        echo "❌ $(date): Failed to restart Redis!" >> "$ALERT_LOG"
    fi
else
    # بررسی اتصال Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis: Running and responding" >> "$LOG_FILE"
        
        # بررسی تعداد task های در صف
        QUEUE_SIZE=$(redis-cli LLEN celery 2>/dev/null || echo "0")
        echo "📊 Queue size: $QUEUE_SIZE tasks" >> "$LOG_FILE"
        
        if [ "$QUEUE_SIZE" -gt "$MAX_QUEUE_SIZE" ]; then
            echo "⚠️ $(date): High queue size detected: $QUEUE_SIZE tasks (threshold: $MAX_QUEUE_SIZE)" >> "$ALERT_LOG"
        fi
    else
        echo "❌ $(date): Redis not responding to ping!" >> "$ALERT_LOG"
    fi
fi

# بررسی Gunicorn
if ! systemctl is-active --quiet gunicorn.service; then
    echo "⚠️ $(date): Gunicorn is DOWN!" >> "$ALERT_LOG"
else
    echo "✅ Gunicorn: Running" >> "$LOG_FILE"
fi

# بررسی Health Check Endpoint (اختیاری)
HEALTH_CHECK_URL="http://localhost/rubika-bot/health/"
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ Health check: OK" >> "$LOG_FILE"
elif [ "$HEALTH_STATUS" = "503" ]; then
    echo "⚠️ $(date): Health check returned degraded status (503)" >> "$ALERT_LOG"
else
    echo "❌ $(date): Health check failed with status: $HEALTH_STATUS" >> "$ALERT_LOG"
fi

# پاکسازی لاگ‌های قدیمی (نگهداری 7 روز اخیر)
find /var/log/celery*.log -mtime +7 -delete 2>/dev/null

echo "" >> "$LOG_FILE"
