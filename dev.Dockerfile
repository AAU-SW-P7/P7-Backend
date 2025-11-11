# Use the official Python runtime image
FROM python:3.13-alpine
 
# Create the app directory
RUN mkdir /app
 
# Set the working directory inside the container
WORKDIR /app
 
# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 
 
# Upgrade pip
RUN pip install --upgrade pip 
 
# Copy the Django project  and install dependencies
COPY requirements.txt  /app/
 
# run this command to install all dependencies 
RUN pip install --no-cache-dir -r requirements.txt
 
# Copy the Django project to the container
COPY . /app/
 
# Expose the Django port
EXPOSE 8000
 
# Run Django’s development server
# Start both qclusters in the background, then exec the runserver in the foreground.
# Using `&` for both qclusters prevents the first (high) from blocking the second.
CMD ["sh", "-c", "python manage.py makemigrations repository && python manage.py migrate repository --noinput && python manage.py makemigrations && python manage.py migrate --noinput && Q_CLUSTER_NAME=high python manage.py qcluster & Q_CLUSTER_NAME=low python manage.py qcluster & exec python manage.py runserver 0.0.0.0:8000"]