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

def run_gunicorn():
    """Run Gunicorn server"""
    gunicorn_cmd = [
        'gunicorn',
        'drf.wsgi:application',
        '--bind',
        '0.0.0.0:8000',
        '--workers',
        '4',
        '--threads',
        '2',
        '--timeout',
        '120'
    ]
    subprocess.Popen(gunicorn_cmd)
    print("Gunicorn server started.")

def run_prod():
    """Run the application in production mode"""
    # Run Redis server
    run_redis()
    
    # Wait for Redis to start
    time.sleep(2)
    
    # Run Celery worker
    run_celery_worker()
    
    # Run Celery Beat
    run_celery_beat()
    
    # Run Gunicorn server
    run_gunicorn()
    
    print("\nAll services started. Press Ctrl+C to stop.")
    
    try:
        # Keep the script running
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping all services...")
        sys.exit(0)

if __name__ == '__main__':
    run_prod() 