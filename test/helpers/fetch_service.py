import os
import json
import pytest_check as check

from repository.models import Service, User, File

def assert_fetch_dropbox_files_success(client, userId, service):
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.count()
    initial_file_count = File.objects.filter(serviceId__userId=userId, serviceId__name=service).count()

    check.equal(initial_user_count == 3, True) # Assuming 3 users are already created for service creation
    check.equal(initial_service_count == 9, True)
    check.equal(initial_file_count == 0, True) # Assuming no files are created initially

    print(f"Fetching Dropbox files for userId: {userId}")

    try:
        response = client.get(f"/?userId={userId}", headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")})
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise
    check.equal(response.status_code, 200)

def assert_fetch_dropbox_files_invalid_auth(client, userId):
    response = client.get(f"/?userId={userId}", headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_fetch_dropbox_files_missing_header(client, userId):
    response = client.get(f"/?userId={userId}")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {'detail': [{'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string', 'type': 'string_type'}]})

def assert_fetch_dropbox_files_missing_userid(client):
    response = client.get("/")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {'detail': [{'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}, {'type': 'string_type', 'loc': ['query', 'userId'], 'msg': 'Input should be a valid string'}]})

def assert_fetch_google_files_success(client, userId, service):
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.count()
    initial_file_count = File.objects.filter(serviceId__userId=userId, serviceId__name=service).count()

    check.equal(initial_user_count == 3, True) # Assuming 3 users are already created for service creation
    check.equal(initial_service_count == 9, True)
    check.equal(initial_file_count == 0, True) # Assuming no files are created initially

    print(f"Fetching Google files for userId: {userId}")

    try:
        response = client.get(f"/?userId={userId}", headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")})
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise
    check.equal(response.status_code, 200)

def assert_fetch_google_files_invalid_auth(client, userId):
    response = client.get(f"/?userId={userId}", headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_fetch_google_files_missing_header(client, userId):
    response = client.get(f"/?userId={userId}")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {'detail': [{'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string', 'type': 'string_type'}]})

def assert_fetch_google_files_missing_userid(client):
    response = client.get("/")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {'detail': [{'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}, {'type': 'string_type', 'loc': ['query', 'userId'], 'msg': 'Input should be a valid string'}]})

def assert_fetch_onedrive_files_success(client, userId, service):
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.count()
    initial_file_count = File.objects.filter(serviceId__userId=userId, serviceId__name=service).count()

    check.equal(initial_user_count == 3, True) # Assuming 3 users are already created for service creation
    check.equal(initial_service_count == 9, True)
    check.equal(initial_file_count == 0, True) # Assuming no files are created initially

    print(f"Fetching OneDrive files for userId: {userId}")

    try:
        response = client.get(f"/?userId={userId}", headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")})
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise
    check.equal(response.status_code, 200)

def assert_fetch_onedrive_files_invalid_auth(client, userId):
    response = client.get(f"/?userId={userId}", headers={"x-internal-auth": "invalid_token"})

    check.equal(response.status_code, 401)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_fetch_onedrive_files_missing_header(client, userId):
    response = client.get(f"/?userId={userId}")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {'detail': [{'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string', 'type': 'string_type'}]})

def assert_fetch_onedrive_files_missing_userid(client):
    response = client.get("/")

    check.equal(response.status_code, 422)
    check.equal(response.json(), {'detail': [{'type': 'string_type', 'loc': ['header', 'x-internal-auth'], 'msg': 'Input should be a valid string'}, {'type': 'string_type', 'loc': ['query', 'userId'], 'msg': 'Input should be a valid string'}]})
