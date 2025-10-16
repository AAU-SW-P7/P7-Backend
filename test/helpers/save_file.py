"""Helper functions for testing save files endpoint."""
import os
from p7.get_google_drive_files.api import build_google_drive_path
import pytest_check as check

from repository.models import Service, User, File

def assert_save_file_success(client, user_id, service_name):
    """Helper function to assert successful creation of a service.
    params:
        client: Test client to make requests.
        user_id: ID of the user creating the service.
        service_name: Name of the service.
    """
    # Get initial user count
    initial_user_count = User.objects.count()
    initial_service_count = Service.objects.filter(
        userId=user_id,
        name=service_name,
    ).count()

    # Assuming 3 users are already created for service creation
    check.equal(initial_user_count == 3, True)
    check.equal(initial_service_count == 1, True)
    
    print(f"Initial service count for user {user_id} and service {service_name}: {initial_service_count}")

    response = client.get(
        f"/?user_id={user_id}",
        headers={"x-internal-auth": os.getenv("INTERNAL_API_KEY")}
    )

    data = response.json()
    
    check.equal(response.status_code, 200)
    check.is_instance(data, list)
    
    for file in data:
        check.is_instance(file, dict)
        if service_name == 'dropbox':
            # check.is_instance(file.get('.tag'), str)
            # check.is_instance(file.get('name'), str)
            # check.is_instance(file.get('path_display'), str)
            # check.is_instance(file.get('id'), str)
            # check.is_instance(file.get('client_modified'), str)
            # check.is_instance(file.get('server_modified'), str)
            # check.is_instance(file.get('size'), int)
            # check.is_instance(file.get('is_downloadable'), bool)
            
            # check.equal(file.get('.etag'), 'file')
            
            extension = os.path.splitext(file["name"])[1]
            path = file["path_display"]
            link = "https://www.dropbox.com/preview" + path

            get_file = File.objects.filter(
                serviceId__userId=user_id,
                serviceId__name=service_name,
                serviceFileId=file.get('id'),
                name=file.get('name'),
                extension=extension,
                downloadable=file.get('is_downloadable'),
                path=path,
                link=link,
                size=file.get('size'),
                createdAt=file.get('client_modified'),
                modifiedAt=file.get('server_modified'),
                lastIndexed=None,
                snippet=None,
                content=None,
            ).count()
            check.equal(get_file, 1)
        elif service_name == 'google':
            file_by_id = {file["id"]: file for file in data}
            
            extension = os.path.splitext(file.get("name", ""))[1]
            downloadable = file.get("capabilities", {}).get("canDownload")
            path = build_google_drive_path(file, file_by_id)
            
            get_file = File.objects.filter(
                serviceId__userId=user_id,
                serviceId__name=service_name,
                serviceFileId=file.get('id'),
                name=file.get('name'),
                extension=extension,
                downloadable=downloadable,
                path=path,
                link=file.get('webViewLink'),
                size=file.get('size', 0),
                createdAt=file.get('createdTime'),
                modifiedAt=file.get('modifiedTime'),
                lastIndexed=None,
                snippet=None,
                content=None,
            ).count()
            check.equal(get_file, 1)
        elif service_name == 'microsoft-entra-id':
            extension = os.path.splitext(file["name"])[1]
            path = (
                (file.get("parentReference", {}).get("path", "")).replace(
                    "/drive/root:", ""
                )
                + "/"
                + file["name"]
            )
            
            get_file = File.objects.filter(
                serviceId__userId=user_id,
                serviceId__name=service_name,
                serviceFileId=file.get('id'),
                name=file.get('name'),
                extension=extension,
                downloadable=1,
                path=path,
                link=file.get('webUrl'),
                size=file.get('size', 0),
                createdAt=file.get('createdDateTime'),
                modifiedAt=file.get('lastModifiedDateTime'),
                lastIndexed=None,
                snippet=None,
                content=None,
            ).count()
            check.equal(get_file, 1)

def assert_save_file_invalid_auth(client, user_id):
    """Helper function to assert finding a service with invalid auth.

    params:
        client: Test client to make requests.
        user_id: ID of the user.
    """
    try:
        response = client.get(
            f"/?user_id={user_id}",
            headers={"x-internal-auth": "invalid_token"}
            )
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 401)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json(), {"error": "Unauthorized - invalid x-internal-auth"})

def assert_save_file_missing_header(client, user_id):
    """Helper function to assert finding a user by user_id with missing auth header.

    params:
        client: Test client to make requests.
        user_id: ID of the user.
    """
    try:
        response = client.get(f"/?user_id={user_id}")
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 422)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json(), {
        'detail': [
            {
                'loc': ['header', 'x-internal-auth'], 
                'msg': 'Input should be a valid string', 
                'type': 'string_type'
            }
        ]
    })

def assert_save_file_missing_user_id(client):
    """Helper function to assert finding a service by user ID with missing user ID.

    params:
        client: Test client to make requests.
    """
    try:
        response = client.get("/",)
    except Exception as e:
        print(f"Exception during GET request: {e}")
        raise

    check.equal(response.status_code, 422)
    check.equal(response.json() is not None, True)
    check.equal(isinstance(response.json(), dict), True)
    check.equal(response.json(), {
        'detail': [
            {
                'type': 'string_type',
                'loc': ['query', 'user_id'],
                'msg': 'Input should be a valid string'
            },
            {
                'type': 'string_type', 
                'loc': ['header', 'x-internal-auth'], 
                'msg': 'Input should be a valid string'
            }
        ]
    })
