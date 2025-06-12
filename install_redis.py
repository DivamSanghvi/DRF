import os
import platform
import subprocess
import sys

def install_redis_windows():
    """Install Redis on Windows"""
    print("Installing Redis on Windows...")
    
    # Download Redis
    redis_url = "https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.zip"
    redis_zip = "Redis-x64-3.0.504.zip"
    
    print("Downloading Redis...")
    import urllib.request
    urllib.request.urlretrieve(redis_url, redis_zip)
    
    print("Extracting Redis...")
    import zipfile
    with zipfile.ZipFile(redis_zip, 'r') as zip_ref:
        zip_ref.extractall("redis")
    
    print("Cleaning up...")
    os.remove(redis_zip)
    
    print("Redis installed successfully!")
    print("\nTo start Redis server, run:")
    print("redis\\redis-server.exe")
    
    print("\nTo start Redis CLI, run:")
    print("redis\\redis-cli.exe")

def install_redis_linux():
    """Install Redis on Linux"""
    print("Installing Redis on Linux...")
    
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

def install_redis_macos():
    """Install Redis on macOS"""
    print("Installing Redis on macOS...")
    
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

def install_redis():
    """Install Redis based on the operating system"""
    system = platform.system().lower()
    
    if system == 'windows':
        install_redis_windows()
    elif system == 'linux':
        install_redis_linux()
    elif system == 'darwin':
        install_redis_macos()
    else:
        print(f"Unsupported operating system: {system}")
        sys.exit(1)

if __name__ == '__main__':
    install_redis() 