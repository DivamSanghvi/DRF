import os
import subprocess
import sys

def install_dependencies():
    """Install all dependencies"""
    print("Installing dependencies...")
    
    # Install Python packages
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # Install Redis
    print("\nInstalling Redis...")
    import install_redis
    install_redis.install_redis()
    
    # Install Celery
    print("\nInstalling Celery...")
    import install_celery
    install_celery.install_celery()
    
    # Install Gunicorn
    print("\nInstalling Gunicorn...")
    import install_gunicorn
    install_gunicorn.install_gunicorn()
    
    print("\nAll dependencies installed successfully!")
    print("\nTo start the application in development mode, run:")
    print("python run_dev.py")
    
    print("\nTo start the application in production mode, run:")
    print("python run_prod.py")
    
    print("\nTo stop all services, run:")
    print("python stop_all.py")

if __name__ == '__main__':
    install_dependencies() 