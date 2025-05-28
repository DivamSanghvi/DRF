# DRF Project

A Django REST Framework project following MVC architecture.

## Project Structure

```
drf/
├── core/                 # Core app for common functionality
├── api/                  # Main API app
├── manage.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

## Project Architecture

This project follows the MVC (Model-View-Controller) architecture:

- **Models**: Define data structure and business logic
- **Views**: Handle HTTP requests and responses
- **Controllers**: Process data and implement business rules

## API Documentation

API documentation is available at `/api/docs/` when running the server. 