FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
COPY .env .env.example ./

# Install PostgreSQL client, development libraries, and required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Use uv to install Python dependencies
RUN uv pip install --system -e .
RUN uv pip install --system alembic

# Copy application code
COPY . .

# Expose port for Flask application
EXPOSE 5000

# Default command (can be overridden in docker-compose)
CMD ["python", "app.py"]
