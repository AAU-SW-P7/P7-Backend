# https://www.docker.com/blog/how-to-dockerize-django-app/

# Stage 1: Base build stage
FROM python:3.14-slim AS builder
 
# Create the app directory
RUN mkdir /app
 
# Set the working directory
WORKDIR /app
 
# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 
 
# Upgrade pip and install dependencies
RUN pip install --upgrade pip 
 
# Copy the requirements file first (better caching)
COPY requirements.txt /app/
 
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source into the builder (after installing requirements to keep cache)
COPY . /app

# Stage 2: Production stage
FROM python:3.14-slim
 
RUN useradd -m -r appuser && \
   mkdir /app && \
   chown -R appuser /app

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the application source from the builder stage
COPY --from=builder /app /app
 
# Set the working directory
WORKDIR /app

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

# Set default DJANGO_SETTINGS_MODULE
ENV DJANGO_SETTINGS_MODULE=p7.settings

# Add an entrypoint script
COPY prod.entrypoint.sh /usr/local/bin/prod.entrypoint.sh
RUN chmod +x /usr/local/bin/prod.entrypoint.sh && \
    chown appuser:appuser /usr/local/bin/prod.entrypoint.sh && \
    chown -R appuser:appuser /app

USER appuser
 
# Expose the Django port
EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/prod.entrypoint.sh"]
CMD ["gunicorn", "p7.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "6", "--threads", "12", "--access-logfile", "-", "--error-logfile", "-"]