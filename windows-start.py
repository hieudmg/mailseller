"""
Python script to start production server.
It runs these commands concurrently:
- In ./backend folder: uvicorn app.main:app --host 0.0.0.0 --port 8888
- In ./frontend folder: npm run start -- --port 3333
"""

import subprocess
import sys
import os

# Start backend server
backend_cmd = [
    sys.executable,
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
frontend_cmd = ["npm", "run", "start", "--", "--port", "3333"]
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
