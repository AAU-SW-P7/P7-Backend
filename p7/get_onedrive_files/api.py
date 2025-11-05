"""API for fetching and syncing OneDrive files."""
import os

from ninja import Router, Header
from django.http import JsonResponse
from django_q.tasks import async_task
# Microsoft libs
import msal

from p7.helpers import validate_internal_auth
from p7.get_onedrive_files.helper import (
    update_or_create_file, fetch_recursive_files
    )
from repository.service import get_tokens, get_service
from repository.user import get_user

fetch_onedrive_files_router = Router()
@fetch_onedrive_files_router.get("/")
def fetch_onedrive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Fetch and save OneDrive files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose OneDrive files are to be fetched.
    """
    auth_resp = validate_internal_auth(x_internal_auth)

    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    async_task(process_onedrive_files, user_id, cluster="high", group=f"Onedrive-{user_id}")
    return JsonResponse({"status": "processing"}, status=202)

def process_onedrive_files(user_id):
    """Process and sync OneDrive files for a given user."""
    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "onedrive")
    service = get_service(user_id, "onedrive")

    try:
        # Build MSAL app instance
        app = msal.ConfidentialClientApplication(
            os.getenv("MICROSOFT_CLIENT_ID"),
            authority="https://login.microsoftonline.com/common",
            client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
        )
        files = fetch_recursive_files(
            app,
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        for file in files:
            if not file.get("file"):
                continue

            update_or_create_file(file, service)

    except KeyError as e:
        response = JsonResponse({"error": f"Missing key: {str(e)}"}, status=500)
        return response
