# HSC Server Deployment Guide

## Requirements

- Ubuntu 24.04+ (tested on 26.04)
- Python 3.14
- PostgreSQL 16
- Redis 7
- Nginx + Certbot
- Domain: `miepcoj.ir`

## 1. Initial Server Setup

```bash
# Create user
sudo adduser --disabled-password --gecos "" hsc_admin
sudo usermod -aG sudo hsc_admin

# System packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-dev python3-pip \
    postgresql postgresql-contrib redis-server \
    nginx certbot python3-certbot-nginx \
    git curl ufw fail2ban \
    build-essential libpq-dev

# Firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# fail2ban
sudo systemctl enable fail2ban
```

## 2. PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER hsc_admin WITH PASSWORD 'CHANGE_ME';"
sudo -u postgres psql -c "CREATE DATABASE hsc_production OWNER hsc_admin;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hsc_production TO hsc_admin;"
```

## 3. Clone and Setup

```bash
sudo -u hsc_admin bash -c '
git clone -b mkt https://github.com/mohamadkazemt/HSC.git /var/www/HSC
cd /var/www/HSC
python3 -m venv venv
venv/bin/pip install -r requirements.txt --no-compile
mkdir -p logs media static
'
```

## 4. Environment File

Create `/var/www/HSC/.env`:

```ini
# Django Core
DEBUG=False
SECRET_KEY=CHANGE_ME
ALLOWED_HOSTS=miepcoj.ir,www.miepcoj.ir,t.miepcoj.ir
CSRF_TRUSTED_ORIGINS=https://miepcoj.ir,https://www.miepcoj.ir,https://t.miepcoj.ir

# Database
DB_NAME=hsc_production
DB_USER=hsc_admin
DB_PASSWORD=CHANGE_ME
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0

# SMS (SMSIR)
SMSIR_API_KEY=CHANGE_ME
SMSIR_LINE_NUMBER=CHANGE_ME

# Email (disabled)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# AI (disabled)
AI_API_KEY=
AI_API_BASE_URL=
AI_MODEL=
AI_PROVIDER=

# API Keys (disabled)
GOOGLE_API_KEYS=
GROQ_API_KEY=
OPENROUTER_API_KEY=

# Rubika proxy (leave empty if not using proxy)
RUBIKA_PROXY_URL=
```

## 5. Django Setup

```bash
sudo -u hsc_admin bash -c '
cd /var/www/HSC
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production venv/bin/python manage.py migrate --no-input
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production venv/bin/python manage.py collectstatic --noinput
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production venv/bin/python manage.py createsuperuser
'
```

## 6. Python 3.14 Patches

**These are automatically applied by `hsc-deploy.sh` on every deploy.** But for initial setup, run:

```bash
sudo -u hsc_admin /var/www/HSC/venv/bin/python - <<'EOF'
import pathlib, textwrap
VENV = pathlib.Path("/var/www/HSC/venv")
SITE = next(p for p in VENV.glob("lib/python3.*/site-packages") if p.is_dir())

# Django 4.2 BaseContext.__copy__ (copy(super()) fails in Python 3.14)
f = SITE / "django" / "template" / "context.py"
s = f.read_text()
if "self.__class__.__new__(self.__class__)" not in s:
    s = s.replace(
        "duplicate = copy(super())",
        "duplicate = self.__class__.__new__(self.__class__)\n"
        "        duplicate.__dict__.update(self.__dict__)"
    )
    f.write_text(s)
    print("Patched Django context.py")

# aiohttp TimerContext (current_task() returns None in threads)
f = SITE / "aiohttp" / "helpers.py"
s = f.read_text()
if "return TimerNoop()" not in s:
    s = s.replace(
        'raise RuntimeError("Timer context is used outside of a task")',
        "return TimerNoop()"
    )
    f.write_text(s)
    print("Patched aiohttp helpers.py")

# asyncio.timeouts Timeout (current_task() returns None in threads)
f = pathlib.Path("/usr/lib/python3.14/asyncio/timeouts.py")
s = f.read_text()
if "Timeout should be used inside a task" in s:
    s = s.replace(
        'raise RuntimeError("Timeout should be used inside a task")',
        "self._state = _State.ENTERED\n"
        "            self._task = None\n"
        "            self._timeout_handler = None\n"
        "            return self"
    )
    s = s.replace("if self._task.uncancel()", "if self._task is not None and self._task.uncancel()")
    f.write_text(s)
    print("Patched asyncio timeouts.py")

print("Done")
EOF
```

## 7. Systemd Services

### Gunicorn

```bash
sudo tee /etc/systemd/system/gunicorn.service <<'UNIT'
[Unit]
Description=Gunicorn HSC Django Application
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
User=hsc_admin
Group=hsc_admin
WorkingDirectory=/var/www/HSC
EnvironmentFile=/var/www/HSC/.env
Environment=DJANGO_SETTINGS_MODULE=HSCprojects.settings.production
ExecStart=/var/www/HSC/venv/bin/gunicorn \
    --workers 3 \
    --worker-class sync \
    --worker-tmp-dir /dev/shm \
    --bind unix:/run/gunicorn/hsc.sock \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1500 \
    --max-requests-jitter 150 \
    --access-logfile /var/www/HSC/logs/gunicorn-access.log \
    --error-logfile /var/www/HSC/logs/gunicorn-error.log \
    --log-level info \
    HSCprojects.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
LimitNOFILE=65536
NoNewPrivileges=true
PrivateTmp=true
ReadWritePaths=/var/www/HSC/logs /var/www/HSC/media /var/www/HSC/static /run/gunicorn

[Install]
WantedBy=multi-user.target
UNIT
```

### Celery Worker

**Must use `--pool=solo`** (not `prefork`). Python 3.14's asyncio task registry breaks after `os.fork()`.

```bash
sudo tee /etc/systemd/system/celery-worker.service <<'UNIT'
[Unit]
Description=Celery Worker HSC
After=network.target redis-server.service postgresql.service
Wants=redis-server.service postgresql.service

[Service]
User=hsc_admin
Group=hsc_admin
WorkingDirectory=/var/www/HSC
EnvironmentFile=/var/www/HSC/.env
Environment=DJANGO_SETTINGS_MODULE=HSCprojects.settings.production
Environment=DJANGO_ALLOW_ASYNC_UNSAFE=true
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects worker --pool=solo -l info --without-gossip --without-mingle --without-heartbeat
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=60
LimitNOFILE=65536
NoNewPrivileges=true
PrivateTmp=true
MemoryMax=800M

[Install]
WantedBy=multi-user.target
UNIT
```

### Celery Beat

```bash
sudo tee /etc/systemd/system/celery-beat.service <<'UNIT'
[Unit]
Description=Celery Beat HSC
After=network.target redis-server.service celery-worker.service
Wants=redis-server.service

[Service]
User=hsc_admin
Group=hsc_admin
WorkingDirectory=/var/www/HSC
EnvironmentFile=/var/www/HSC/.env
Environment=DJANGO_SETTINGS_MODULE=HSCprojects.settings.production
ExecStart=/var/www/HSC/venv/bin/celery -A HSCprojects beat --schedule=/var/www/HSC/logs/celerybeat-schedule --pidfile=/var/www/HSC/logs/celerybeat.pid --loglevel=info
Restart=on-failure
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
LimitNOFILE=65536
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT
```

Enable all:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn celery-worker celery-beat
```

## 8. Nginx

```bash
sudo tee /etc/nginx/conf.d/rate_limit.conf <<'CONF'
limit_req_zone $binary_remote_addr zone=rubika_webhook:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;
CONF

sudo tee /etc/nginx/sites-available/hsc <<'CONF'
server {
    server_name miepcoj.ir www.miepcoj.ir t.miepcoj.ir;
    client_max_body_size 55M;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    server_tokens off;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 5;
    gzip_types text/plain text/css text/javascript text/xml
        application/json application/javascript application/xml application/xml+rss
        application/x-javascript image/svg+xml;

    location /static/ {
        alias /var/www/HSC/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location /media/ {
        alias /var/www/HSC/media/;
        expires 7d;
        access_log off;
        location ~ /\. { deny all; }
        autoindex off;
    }

    location ~ /\. { deny all; }
    location ~* \.(env|sqlite3|py|pyc|log)$ { deny all; }

    location /rubika_bot/webhook/ {
        limit_req zone=rubika_webhook burst=20 nodelay;
        proxy_pass http://unix:/run/gunicorn/hsc.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    location /admin/ {
        limit_req zone=auth_limit burst=10 nodelay;
        proxy_pass http://unix:/run/gunicorn/hsc.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location /accounts/login/ {
        limit_req zone=auth_limit burst=5 nodelay;
        proxy_pass http://unix:/run/gunicorn/hsc.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn/hsc.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
    }

    listen 443 ssl;
    listen [::]:443 ssl ipv6only=on;
    ssl_certificate /etc/letsencrypt/live/miepcoj.ir/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/miepcoj.ir/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = www.miepcoj.ir) { return 301 https://$host$request_uri; }
    if ($host = miepcoj.ir) { return 301 https://$host$request_uri; }
    listen 80;
    listen [::]:80;
    server_name miepcoj.ir www.miepcoj.ir t.miepcoj.ir;
    return 404;
}
CONF

sudo ln -sf /etc/nginx/sites-available/hsc /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

TLS (auto-renew):

```bash
sudo certbot --nginx -d miepcoj.ir -d www.miepcoj.ir -d t.miepcoj.ir
```

## 9. Backup Cron

```bash
sudo tee /usr/local/bin/hsc-backup.sh <<'SCRIPT'
#!/bin/bash
set -euo pipefail
export PGPASSWORD="CHANGE_ME"
BACKUP_DIR="/var/backups/hsc"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="hsc_production"
DB_USER="hsc_admin"
mkdir -p "${BACKUP_DIR}/db" "${BACKUP_DIR}/media"
pg_dump -U "${DB_USER}" -h 127.0.0.1 "${DB_NAME}" | gzip > "${BACKUP_DIR}/db/hsc_${DATE}.sql.gz"
tar czf "${BACKUP_DIR}/media/hsc_media_${DATE}.tar.gz" -C /var/www/HSC media/
tar czf "${BACKUP_DIR}/hsc_config_${DATE}.tar.gz" -C /var/www/HSC .env HSCprojects/settings/
find "${BACKUP_DIR}/db" -name "hsc_*.sql.gz" -mtime +7 -delete
find "${BACKUP_DIR}/media" -name "hsc_media_*.tar.gz" -mtime +7 -delete
find "${BACKUP_DIR}" -maxdepth 1 -name "hsc_config_*.tar.gz" -mtime +30 -delete
echo "Backup completed: ${DATE}"
SCRIPT
sudo chmod +x /usr/local/bin/hsc-backup.sh

# Daily backup at 3 AM
echo "0 3 * * * /usr/local/bin/hsc-backup.sh >> /var/www/HSC/logs/backup.log 2>&1" | crontab -u hsc_admin -
```

## 10. Deploy Script

```bash
sudo tee /usr/local/bin/hsc-deploy.sh <<'SCRIPT'
#!/bin/bash
set -euo pipefail
LOCKFILE="/home/hsc_admin/.hsc-deploy.lock"
exec 200>"${LOCKFILE}"
flock -n 200 || { echo "Another deployment running"; exit 1; }

PROJECT_DIR="/var/www/HSC"
VENV="${PROJECT_DIR}/venv"
BRANCH="mkt"
REQ_HASH_FILE="/home/hsc_admin/.hsc_req_hash"

echo "=== HSC Deployment $(date) ==="
cd "${PROJECT_DIR}"

PREV_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "none")

if ! git diff --quiet 2>/dev/null; then git stash; fi
git fetch origin "${BRANCH}"
git reset --hard "origin/${BRANCH}"
COMMIT=$(git rev-parse --short HEAD)
echo "Checked out: ${COMMIT} (was: ${PREV_COMMIT})"

sudo /usr/local/bin/hsc-backup.sh

REQ_HASH=$(md5sum requirements.txt | awk '{print $1}')
CACHED_HASH=$(cat "${REQ_HASH_FILE}" 2>/dev/null || echo "none")
if [ "$REQ_HASH" != "$CACHED_HASH" ]; then
    echo "Requirements changed, installing..."
    "${VENV}/bin/pip" install -r requirements.txt -q --no-compile 2>&1
    echo "$REQ_HASH" > "${REQ_HASH_FILE}"
else
    echo "Requirements unchanged, skipping pip install"
fi

DJANGO_SETTINGS_MODULE=HSCprojects.settings.production "${VENV}/bin/python" manage.py migrate --no-input 2>&1
DJANGO_SETTINGS_MODULE=HSCprojects.settings.production "${VENV}/bin/python" manage.py collectstatic --noinput 2>&1

# Python 3.14 patches (idempotent, see section 6)
# ... (patch commands - see full deploy script in this repo)

chmod 755 "${PROJECT_DIR}"
sudo systemctl reload gunicorn
sudo systemctl restart celery-worker
sudo systemctl is-active --quiet celery-beat || sudo systemctl start celery-beat

sleep 2
HTTP_CODE=$(curl -sk -o /dev/null -w "%http_code}" -H "Host: miepcoj.ir" https://127.0.0.1/ 2>/dev/null)
if [ "${HTTP_CODE}" = "200" ] || [ "${HTTP_CODE}" = "302" ]; then
    echo "Deployed: ${COMMIT}"
else
    echo "Smoke test FAILED (HTTP ${HTTP_CODE})"
    exit 1
fi
SCRIPT
sudo chmod +x /usr/local/bin/hsc-deploy.sh
```

## 11. Logrotate

```bash
sudo tee /etc/logrotate.d/hsc <<'CONF'
/var/www/HSC/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 hsc_admin hsc_admin
    sharedscripts
    postrotate
        systemctl reload gunicorn > /dev/null 2>&1 || true
    endscript
}
CONF
```

## 12. Rubika Bot Setup

After deployment, configure the bot in Django admin:

1. Go to `/admin/` and log in
2. Find **Rubika Bot Settings** and add:
   - **Bot Token**: from Rubika panel
   - **Webhook URL**: `https://miepcoj.ir/rubika_bot/webhook/`
   - **Proxy URL**: if needed

## Quick Deploy (on existing server)

```bash
sudo /usr/local/bin/hsc-deploy.sh
```

## Key Decisions

| Decision | Why |
|---|---|
| Celery `--pool=solo` | Python 3.14 asyncio task registry is broken after `os.fork()`. Solo pool avoids fork entirely. |
| `rubpy.sync` unwrap in services.py | rubpy.sync wraps BotClient methods with sync wrappers that capture the event loop at import time. Our async helpers run on a dedicated loop thread, so the captured loop is wrong. We restore original async methods. |
| Django context.py patch | Django 4.2's `BaseContext.__copy__` uses `copy(super())` which fails in Python 3.14. |
| aiohttp TimerContext patch | `asyncio.current_task()` returns `None` for tasks running on event loops in non-main threads in Python 3.14. Patched to return `TimerNoop()` instead of crashing. |
| asyncio.timeout patch | Same root cause as aiohttp. Patched `Timeout.__aenter__` to be a no-op when no task is found. |
| Requirements hash caching | `pip install` is slow on the small server. Hash stored at `/home/hsc_admin/.hsc_req_hash` (outside git) to skip when unchanged. |
| CDN → local vendor | 21 JS/CSS libraries downloaded to `static/vendor/` to avoid external dependencies. |
