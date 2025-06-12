import os
import django
from celery.schedules import crontab
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf.settings')

# Initialize Django
django.setup()

# Create Celery app
app = Celery('drf')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    'process-pending-pdfs': {
        'task': 'api.tasks.process_multiple_pdfs_task',
        'schedule': 300.0,  # Run every 5 minutes
    },
}

if __name__ == '__main__':
    app.start() 