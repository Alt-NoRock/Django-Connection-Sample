# Production stage
FROM python:3.11-slim


# Create non-root user with home directory
RUN groupadd -r django && useradd -r -g django -m django

WORKDIR /app

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Create static files directory and set permissions
RUN mkdir -p /app/staticfiles \
    && chown -R django:django /app \
    && chown -R django:django /home/django

# Switch to non-root user
USER django

# Collect static files
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000

CMD ["python", "-m", "daphne", "-b", "0.0.0.0", "-p", "8000", "myproject.asgi:application"]