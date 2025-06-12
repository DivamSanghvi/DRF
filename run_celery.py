import os
import django
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf.settings')

# Initialize Django
django.setup()

# Create Celery app
app = Celery('drf')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

if __name__ == '__main__':
    app.start() 