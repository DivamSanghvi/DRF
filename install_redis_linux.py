import os
import subprocess
import sys

def install_redis():
    """Install Redis on Linux"""
    print("Installing Redis...")
    
    # Update package list
    subprocess.run(['sudo', 'apt-get', 'update'])
    
    # Install Redis
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'redis-server'])
    
    # Start Redis service
    subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'])
    
    # Enable Redis service on boot
    subprocess.run(['sudo', 'systemctl', 'enable', 'redis-server'])
    
    print("Redis installed successfully!")
    print("\nTo start Redis server, run:")
    print("sudo systemctl start redis-server")
    
    print("\nTo stop Redis server, run:")
    print("sudo systemctl stop redis-server")
    
    print("\nTo check Redis status, run:")
    print("sudo systemctl status redis-server")
    
    print("\nTo start Redis CLI, run:")
    print("redis-cli")

if __name__ == '__main__':
    install_redis() 