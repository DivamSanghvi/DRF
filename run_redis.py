import os
import subprocess
import sys

def run_redis():
    """Run Redis server"""
    redis_cmd = [
        'redis-server',
        '--port',
        '6379'
    ]
    subprocess.Popen(redis_cmd)

if __name__ == '__main__':
    # Run Redis server
    run_redis()
    
    print("Redis server started. Press Ctrl+C to stop.")
    
    try:
        # Keep the script running
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping Redis server...")
        sys.exit(0) 