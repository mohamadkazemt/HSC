# HSC Project

A Django-based web application for managing and tracking various aspects of the HSC system.

## Features

- User authentication and authorization
- Dashboard for data visualization
- Data management and reporting
- Responsive design
- Secure file handling

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