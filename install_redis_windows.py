import os
import subprocess
import sys
import urllib.request
import zipfile
import shutil

def download_redis():
    """Download Redis for Windows"""
    redis_url = "https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.zip"
    redis_zip = "Redis-x64-3.0.504.zip"
    
    print("Downloading Redis...")
    urllib.request.urlretrieve(redis_url, redis_zip)
    
    print("Extracting Redis...")
    with zipfile.ZipFile(redis_zip, 'r') as zip_ref:
        zip_ref.extractall("redis")
    
    print("Cleaning up...")
    os.remove(redis_zip)
    
    print("Redis installed successfully!")
    print("\nTo start Redis server, run:")
    print("redis\\redis-server.exe")
    
    print("\nTo start Redis CLI, run:")
    print("redis\\redis-cli.exe")

if __name__ == '__main__':
    download_redis() 