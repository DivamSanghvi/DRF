import os
import subprocess
import sys

def stop_redis():
    """Stop Redis server"""
    redis_cmd = [
        'redis-cli',
        'shutdown'
    ]
    subprocess.run(redis_cmd)
    print("Redis server stopped.")

def stop_celery():
    """Stop Celery worker and beat"""
    celery_cmd = [
        'celery',
        '-A',
        'drf',
        'control',
        'shutdown'
    ]
    subprocess.run(celery_cmd)
    print("Celery worker and beat stopped.")

def stop_django():
    """Stop Django development server"""
    django_cmd = [
        'taskkill',
        '/F',
        '/IM',
        'python.exe'
    ]
    subprocess.run(django_cmd)
    print("Django development server stopped.")

if __name__ == '__main__':
    # Stop Django development server
    stop_django()
    
    # Stop Celery worker and beat
    stop_celery()
    
    # Stop Redis server
    stop_redis()
    
    print("\nAll services stopped.") 