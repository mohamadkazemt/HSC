# Fire Extinguisher Management System

A comprehensive Django web application for managing fire extinguishers in industrial and mining settings.

## Features

- **Fire Extinguisher Management**
  - Registration and tracking of fire extinguishers
  - Detailed information storage (serial numbers, types, capacities, etc.)
  - Status tracking (operational, needs maintenance, expired, etc.)
  - Location management
  - Replacement tracking

- **Service Management**
  - Service record creation and tracking
  - Pressure test scheduling and recording
  - Maintenance history
  - Service outcome tracking

- **Notifications**
  - Automated service reminders
  - Pressure test due notifications
  - Custom notification system
  - SMS integration (configurable)

- **Reporting**
  - Service history reports
  - Status reports
  - Location-based reports
  - Maintenance scheduling reports

## Installation

1. Add the app to your Django project's `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'fire_extinguisher_management',
    ...
]
```

2. Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create a superuser (if not already created):

```bash
python manage.py createsuperuser
```

4. Configure SMS settings (optional) in your settings.py:

```python
SMS_ENABLED = True
SMS_PROVIDER = 'your_sms_provider'
SMS_API_KEY = 'your_api_key'
```

## Usage

### Dashboard

The dashboard provides an overview of:
- Total number of fire extinguishers
- Extinguishers needing service
- Upcoming service dates
- Recent service records

### Fire Extinguisher Management

1. **Registration**
   - Click "Register New Extinguisher"
   - Fill in the required information
   - Assign a location
   - Save the record

2. **Service Records**
   - Access the extinguisher's detail page
   - Click "Record Service"
   - Fill in service details
   - Save the record

3. **Location Changes**
   - Access the extinguisher's detail page
   - Click "Change Location"
   - Select new location
   - Save the change

### Notifications

The system automatically checks for:
- Upcoming service dates
- Pressure test due dates
- Maintenance requirements

Notifications are sent via:
- In-app notifications
- SMS (if configured)

## Management Commands

### Check Service Dates

Run the following command to check for upcoming service dates and send notifications:

```bash
python manage.py check_service_dates
```

Recommended to run this command daily via a cron job.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 