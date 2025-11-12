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
 
# Expose the Django port
EXPOSE 8000
 
# Run Django server
CMD ["sh", "-c", "python manage.py makemigrations repository && python manage.py migrate repository --noinput && python manage.py makemigrations && python manage.py migrate --noinput && Q_CLUSTER_NAME=high python manage.py qcluster & Q_CLUSTER_NAME=low python manage.py qcluster & exec python manage.py runserver 0.0.0.0:8000"]