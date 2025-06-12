import os
import subprocess
import sys

def install_celery():
    """Install Celery"""
    print("Installing Celery...")
    
    # Install Celery and Redis
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'celery==5.3.6', 'redis==5.0.1'])
    
    print("Celery installed successfully!")
    print("\nTo start Celery worker, run:")
    print("celery -A drf worker --loglevel=info --pool=solo")
    
    print("\nTo start Celery Beat, run:")
    print("celery -A drf beat --loglevel=info")
    
    print("\nTo start both Celery worker and Beat, run:")
    print("python run_celery_all.py")

if __name__ == '__main__':
    install_celery() 