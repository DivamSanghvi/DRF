import os
import subprocess
import sys

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

if __name__ == '__main__':
    # Run Celery worker
    run_celery_worker()
    
    # Run Celery Beat
    run_celery_beat()
    
    print("Celery worker and beat started. Press Ctrl+C to stop.")
    
    try:
        # Keep the script running
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping Celery processes...")
        sys.exit(0) 