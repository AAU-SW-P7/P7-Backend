"""
URL configuration for p7 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from api.views import hello
from api.GoogleDriveFetcher import fetch_drive_files as fetch_google_drive_files
from api.OneDriveFetcher import fetch_drive_files as fetch_onedrive_files

urlpatterns = [
    path("django/admin/", admin.site.urls),
    path("django/hi/", hello),
    path("django/getGoogleDriveFiles", fetch_google_drive_files),
    path("django/getOneDriveFiles", fetch_onedrive_files)
]