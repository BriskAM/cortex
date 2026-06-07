FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for tree-sitter and postgres driver compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python package manager and dependencies
RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose service port
EXPOSE 5000

CMD ["python", "run.py"]
