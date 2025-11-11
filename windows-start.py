"""
Python script to start production server.
It runs these commands concurrently:
- In ./backend folder: uvicorn app.main:app --host 0.0.0.0 --port 8888
- In ./frontend folder: npm run start -- --port 3333
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()
# Read executables from environment variables, fallback to defaults
NPM_EXE = os.environ.get('NPM_EXE', 'npm')
PYTHON_EXE = os.environ.get('PYTHON_EXE', 'python3')

# Start backend server
backend_cmd = [
    PYTHON_EXE,
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8888",
]
backend_proc = subprocess.Popen(
    backend_cmd,
    cwd=os.path.join(os.path.dirname(__file__), "backend"),
)

# Start frontend server
frontend_cmd = [NPM_EXE, "run", "start", "--", "--port", "3333"]
frontend_proc = subprocess.Popen(
    frontend_cmd,
    cwd=os.path.join(os.path.dirname(__file__), "frontend"),
)

try:
    backend_proc.wait()
    frontend_proc.wait()
except KeyboardInterrupt:
    backend_proc.terminate()
    frontend_proc.terminate()
    backend_proc.wait()
    frontend_proc.wait()
