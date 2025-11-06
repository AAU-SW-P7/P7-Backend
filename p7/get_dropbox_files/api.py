"""API endpoint for fetching and saving Dropbox files."""

from ninja import Router, Header
from django.http import JsonResponse
from django_q.tasks import async_task
from p7.helpers import validate_internal_auth
from p7.get_dropbox_files.helper import (
    update_or_create_file, fetch_recursive_files, get_new_access_token
)
from repository.service import get_tokens, get_service
from repository.user import get_user

fetch_dropbox_files_router = Router()
@fetch_dropbox_files_router.get("/")
def fetch_dropbox_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Fetch and save Dropbox files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose Dropbox files are to be fetched.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user
    task_id = async_task(process_dropbox_files, user_id, cluster="high", group=f"Dropbox-{user_id}")

    return JsonResponse({"task_id": task_id, "status": "processing"}, status=202)

def process_dropbox_files(user_id):
    """Process and sync Dropbox files for a given user.

    params:
        user_id (str): The ID of the user whose Dropbox files are to be processed.

    Returns:
        list: A list of processed Dropbox files or a JsonResponse with an error message.
    
    """
    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "dropbox")
    service = get_service(user_id, "dropbox")

    try:
        access_token, access_token_expiration = get_new_access_token(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        files = fetch_recursive_files(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        for file in files:
            if file[".tag"] != "file":
                continue

            update_or_create_file(file, service)
        return files

    except (KeyError, ValueError, ConnectionError, RuntimeError, TypeError, OSError) as e:
        response = JsonResponse({"error": {str(e)}}, status=500)
        return response
