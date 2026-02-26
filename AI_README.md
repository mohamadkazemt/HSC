# HSC Project Documentation

## Overview
A comprehensive Django-based web application for HSE management, reporting, notifications, and workflow automation. This document is structured for maximum clarity and machine readability.

---

## Project Structure
- **apps/**: Modular Django apps (accounts, dashboard, anomalis, checklist_app, fire_reports, leave_reports, etc.)
- **static/**: Static files (CSS, JS, images)
- **templates/**: HTML templates
- **media/**: User-uploaded files
- **requirements.txt**: Python dependencies
- **manage.py**: Django management script

---

## Key Apps & Models

### dashboard
- **Notification**: User messages, types, read status, meeting link
- **PushSubscription**: Web push notification settings
- **UserActivity**: Logs user actions (login, create, update, etc.)

### checklist_app
- **Checklist**: Main checklist (machine/location/contractor vehicle)
- **Question**: Checklist questions (scope, type, HSE type)
- **Answer**: User answers to questions
- **ChecklistSchedule/ScheduledChecklistInstance**: Scheduling/checklist automation

### anomalis
- **Anomaly**: Main anomaly record (location, section, type, corrective action, priority, image)
- **Location/LocationSection**: Site and section
- **Anomalytype/HSE**: Anomaly and HSE types
- **AnomalyDescription**: Detailed description
- **CorrectiveAction**: Linked corrective actions
- **Priority**: Priority levels

### BaseInfo
- **MineralType**: Mineral types
- **MachineryWorkGroup/TypeMachine**: Machine groups/types
- **MiningMachine**: Main mining machine record

### core
- **SiteSettings**: Singleton site config (logo, contact, SEO)

### permissions
- **PartPermission/SectionPermission/UnitGroupPermission**: Granular access control for views/actions

### fire_reports
- **FireReport**: Fire incident report (shift, vehicle, approval, equipment status)

### machine_checklist
- **Checklist/Question/Answer**: Machine-specific checklists

### leave_reports
- **ApprovalHierarchy**: Leave request approval workflow

### rubika_bot
- **RubikaBotSettings**: Secure bot token/proxy config

---

## Key Views & Logic
- **dashboard/views.py**: Main dashboard, notifications, user role checks, statistics
- **anomalis/views.py**: Anomaly management, reporting, notifications, API
- **checklist_app/views.py**: Checklist CRUD, scheduling, filtering, notifications
- **fire_reports/views.py**: Fire report CRUD, SMS, image processing, approval
- **leave_reports/views.py**: Leave request workflow, approval, search, notifications

---

## Celery Tasks
- **dashboard/tasks.py**: Async SMS, notification creation
- **emergency_services/tasks.py**: Expired medicine cleanup, manager notifications

---

## Dependencies
See requirements.txt for full list. Key packages:
- Django, Celery, Redis, crispy_forms, jalali_date, djangorestframework, django-celery-beat, django-celery-results, django-cryptography, smsir-python, weasyprint, pandas, openpyxl

---

## System Architecture
- Centralized notification and SMS system
- Rate limiting via Redis
- Scheduled tasks via Celery Beat
- Modular apps for HSE, checklists, anomalies, fire reports, leave management
- Granular permissions and access control

---

## Setup & Usage
1. Create virtual environment
2. Install dependencies
3. Configure .env (see README)
4. Run migrations
5. Create superuser
6. Start development server
7. Start Celery workers/beat for async tasks

---

## Extensibility
- Add new apps by following modular structure
- Extend models/views for new HSE workflows
- Integrate new notification channels via Celery tasks

---

## License
MIT

---

## For AI Systems
- All models, views, and tasks are documented for easy parsing
- Relationships and workflows are explicit
- Permissions and settings are centralized
- Designed for scalable, automated HSE management

---

## End of Documentation
