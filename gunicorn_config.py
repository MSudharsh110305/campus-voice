"""
Gunicorn Configuration for CampusVoice v5.0.0
Production-grade WSGI server configuration
"""

import os
import multiprocessing

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv('WORKER_CLASS', 'sync')  # sync, gevent, eventlet, gthread
worker_connections = int(os.getenv('WORKER_CONNECTIONS', 1000))
threads = int(os.getenv('THREADS', 4))  # For gthread worker class
max_requests = int(os.getenv('MAX_REQUESTS', 1000))
max_requests_jitter = int(os.getenv('MAX_REQUESTS_JITTER', 50))
timeout = int(os.getenv('TIMEOUT', 120))
keepalive = int(os.getenv('KEEPALIVE', 5))

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = 'logs/access.log'
errorlog = 'logs/error.log'
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'campusvoice'

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("=" * 70)
    print("CAMPUSVOICE v5.0.0 - PRODUCTION SERVER STARTING")
    print("=" * 70)
    print(f"Workers: {workers}")
    print(f"Worker Class: {worker_class}")
    print(f"Bind: {bind}")
    print("=" * 70)

def when_ready(server):
    """Called just after the server is started."""
    print("=" * 70)
    print("✅ SERVER READY - ACCEPTING CONNECTIONS")
    print("=" * 70)

def on_exit(server):
    """Called just before exiting."""
    print("=" * 70)
    print("🛑 SERVER SHUTDOWN COMPLETE")
    print("=" * 70)

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGINT/SIGQUIT")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGABRT")
