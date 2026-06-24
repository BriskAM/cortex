# Stage 1: Build the frontend static assets
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production unified container (Flask + Celery + Nginx)
FROM python:3.11-slim

WORKDIR /app

ENV FLASK_ENV=production

# Install system dependencies (nginx, gettext-base for envsubst, and build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    gettext-base \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python package manager and backend dependencies
RUN pip install --no-cache-dir --upgrade pip
COPY backend/pyproject.toml backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/ ./backend/

# Copy compiled frontend static assets to Nginx default folder
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# Copy entrypoint script and Nginx config template
COPY entrypoint.sh nginx.conf.template ./
RUN chmod +x entrypoint.sh

# Expose service port (Railway binds to $PORT dynamically)
EXPOSE 8080

CMD ["./entrypoint.sh"]
