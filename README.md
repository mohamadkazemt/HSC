# HSC Project

A Django-based web application for managing and tracking various aspects of the HSC system.

## Features

- User authentication and authorization
- Dashboard for data visualization
- Data management and reporting
- Responsive design
- Secure file handling
- **Centralized notification system** with safe creation, actor skip, and async Celery tasks
- **Unified SMS service** with validation, retry (Celery), rate limiting, and template helpers
- **Automated cleanup** of old notifications via scheduled tasks

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd HSC
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add the following variables:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/hsc_db
SMSIR_API_KEY=your-smsir-key
SMSIR_LINE_NUMBER=3000xxxx
NOTIFICATION_SKIP_ACTOR_DEFAULT=True  # Optional override
NOTIFICATION_RETENTION_DAYS=90  # Auto-cleanup threshold
SMS_RATE_LIMIT_ENABLED=True
SMS_RATE_LIMIT_PER_USER_HOUR=10
SMS_RATE_LIMIT_GLOBAL_MINUTE=100
CRITICAL_POSITIONS="مدیر HSE,بازرس شیفت ایمنی"  # Optional roles for escalation
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

### Running Celery Workers (Async Notifications & SMS Retry)
Ensure Redis is running (or your chosen broker) then start workers:
```powershell
celery -A HSCprojects worker -l info
```
For beat (scheduled tasks like notification cleanup):
```powershell
celery -A HSCprojects beat -l info
```

## System Architecture

### Notification System (`dashboard.notification_utils`)
All apps now use centralized `safe_notification()` function which:
- Prevents duplicate notifications to actor (unless `skip_actor_check=True`)
- Logs failures without breaking flow
- Supports async creation via `dashboard.tasks.create_notification_task`

### SMS System (`core.sms_service`)
Unified SMS sending with:
- Mobile number validation (Iranian format)
- Parameter sanitization
- Rate limiting (configurable per-user and global)
- JSON parsing with fallback
- Track ID extraction from responses

### Rate Limiting (`core.sms_throttle`)
Prevents SMS flooding via Redis-backed counters:
- Per-user hourly limit (default: 10)
- Global system limit per minute (default: 100)
- Per-mobile hourly limit for manual numbers

### Scheduled Tasks (`dashboard.tasks`)
- `cleanup_old_notifications`: Removes read notifications older than retention threshold
- Configured via Celery Beat in settings


## Project Structure

```
HSC/
├── hsc/                 # Main project directory
├── apps/               # Django applications
│   ├── accounts/      # User management
│   ├── dashboard/     # Dashboard functionality
│   └── reports/       # Reporting system
├── static/            # Static files
├── templates/         # HTML templates
├── media/            # User uploaded files
├── requirements.txt   # Project dependencies
└── manage.py         # Django management script
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 