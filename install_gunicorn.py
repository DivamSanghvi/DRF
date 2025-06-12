import os
import subprocess
import sys

def install_gunicorn():
    """Install Gunicorn"""
    print("Installing Gunicorn...")
    
    # Install Gunicorn
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'gunicorn==21.2.0'])
    
    print("Gunicorn installed successfully!")
    print("\nTo start Gunicorn server, run:")
    print("gunicorn drf.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2 --timeout 120")
    
    print("\nTo start the application in production mode, run:")
    print("python run_prod.py")

if __name__ == '__main__':
    install_gunicorn() 