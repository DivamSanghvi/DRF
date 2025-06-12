import os
import subprocess
import sys
import time

def run_redis():
    """Run Redis server"""
    redis_cmd = [
        'redis-server',
        '--port',
        '6379'
    ]
    subprocess.Popen(redis_cmd)
    print("Redis server started.")

def run_celery_worker():
    """Run Celery worker"""
    worker_cmd = [
        'celery',
        '-A',
        'drf',
        'worker',
        '--loglevel=info',
        '--pool=solo'
    ]
    subprocess.Popen(worker_cmd)
    print("Celery worker started.")

def run_celery_beat():
    """Run Celery Beat"""
    beat_cmd = [
        'celery',
        '-A',
        'drf',
        'beat',
        '--loglevel=info'
    ]
    subprocess.Popen(beat_cmd)
    print("Celery Beat started.")

def run_django_server():
    """Run Django development server"""
    django_cmd = [
        'python',
        'manage.py',
        'runserver',
        '--settings=drf.settings'
    ]
    subprocess.Popen(django_cmd)
    print("Django development server started.")

def run_dev():
    """Run the application in development mode"""
    # Run Redis server
    run_redis()
    
    # Wait for Redis to start
    time.sleep(2)
    
    # Run Celery worker
    run_celery_worker()
    
    # Run Celery Beat
    run_celery_beat()
    
    # Run Django development server
    run_django_server()
    
    print("\nAll services started. Press Ctrl+C to stop.")
    
    try:
        # Keep the script running
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping all services...")
        sys.exit(0)

if __name__ == '__main__':
    run_dev() 