#!/bin/bash

# Replace ${PORT} with the environment PORT in nginx configuration template
envsubst '${PORT}' < nginx.conf.template > /etc/nginx/sites-available/default

# Start Nginx service
service nginx start

# Start Celery worker in the background
PYTHONPATH=. celery -A backend.celery_worker.celery worker --loglevel=info &

# Start Gunicorn in the foreground
PYTHONPATH=. exec gunicorn --bind 127.0.0.1:5000 backend.run:app
