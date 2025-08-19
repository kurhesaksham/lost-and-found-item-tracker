import os
from datetime import datetime
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'logger.log')

def log(func):
    @wraps(func)  # Keeps original function name for Flask
    def wrapper(*args, **kwargs):
        with open(LOG_FILE, "a") as file:
            file.write(f"[{datetime.now().isoformat()}] Function '{func.__name__}' executed\n")
        return func(*args, **kwargs)
    return wrapper
