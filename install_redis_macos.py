import os
import subprocess
import sys

def install_redis():
    """Install Redis on macOS"""
    print("Installing Redis...")
    
    # Install Redis using Homebrew
    subprocess.run(['brew', 'install', 'redis'])
    
    # Start Redis service
    subprocess.run(['brew', 'services', 'start', 'redis'])
    
    print("Redis installed successfully!")
    print("\nTo start Redis server, run:")
    print("brew services start redis")
    
    print("\nTo stop Redis server, run:")
    print("brew services stop redis")
    
    print("\nTo check Redis status, run:")
    print("brew services list")
    
    print("\nTo start Redis CLI, run:")
    print("redis-cli")

if __name__ == '__main__':
    install_redis() 