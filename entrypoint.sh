#!/bin/bash

# Replace ${PORT} with the environment PORT in nginx configuration template
envsubst '${PORT}' < nginx.conf.template > /etc/nginx/sites-available/default

# Start Nginx service
service nginx start

# Run database initialization sequentially before spawning concurrent workers
PYTHONPATH=. python -c "
try:
    from backend.app import create_app, db
    app = create_app()
    with app.app_context():
        db.create_all()
    print('Database initialization complete.')
except Exception as e:
    print('Database initialization bypassed/ignored:', e)
"

# Start Celery worker in the background
PYTHONPATH=. celery -A backend.celery_worker.celery worker --loglevel=info --concurrency=1 &

# Start Gunicorn in the foreground
PYTHONPATH=. exec gunicorn --bind 127.0.0.1:5000 backend.run:app
