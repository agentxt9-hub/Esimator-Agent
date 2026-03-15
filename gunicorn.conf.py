import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
loglevel = "info"
accesslog = "-"   # stdout
errorlog = "-"    # stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "zenbid"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190


def on_starting(server):
    """Run DB migrations and seed data before workers fork."""
    from app import app, run_migrations, seed_production_rates
    with app.app_context():
        from app import db
        db.create_all()
    run_migrations()
    seed_production_rates()
