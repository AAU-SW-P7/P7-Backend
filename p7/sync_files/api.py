"""API for syncing files from all services for a user."""
from ninja import Router, Header
from django.http import JsonResponse

from p7.helpers import validate_internal_auth
from p7.sync_files.service_sync_functions import (
    sync_dropbox_files, sync_google_drive_files, sync_onedrive_files
)
from repository.service import get_service
from repository.user import get_user

sync_files_router = Router()
@sync_files_router.get("/")
def sync_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Sync files from all available services for a given user.
        params:
            x_internal_auth (str): The internal auth header for validating the request.
            user_id (str): The ID of the user whose files are to be synced.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    dropbox_service = get_service(user_id, "dropbox")
    google_drive_service = get_service(user_id, "google")
    onedrive_service = get_service(user_id, "onedrive")

    dropbox_updated_files = []
    google_drive_updated_files = []
    onedrive_updated_files = []

    # Check if services exist before syncing
    if dropbox_service and not isinstance(dropbox_service, JsonResponse):
        print("Syncing Dropbox files...")
        dropbox_updated_files = sync_dropbox_files(user_id)
    if google_drive_service and not isinstance(google_drive_service, JsonResponse):
        print("Syncing Google Drive files...")
        google_drive_updated_files = sync_google_drive_files(user_id)
    if onedrive_service and not isinstance(onedrive_service, JsonResponse):
        print("Syncing OneDrive files...")
        onedrive_updated_files = sync_onedrive_files(user_id)

    if isinstance(dropbox_updated_files, JsonResponse) \
    or isinstance(google_drive_updated_files, JsonResponse) \
    or isinstance(onedrive_updated_files, JsonResponse):
        print(dropbox_updated_files)
        print(google_drive_updated_files)
        print(onedrive_updated_files)
        return JsonResponse(
            {"error": "Error syncing files from one or more services."}, status=500
        )

    # This array is for when we want to download all updated files from all services to index them
    # combined_updated_files = (
    #     dropbox_updated_files + google_drive_updated_files + onedrive_updated_files
    # )

    return JsonResponse({"ok": True}, status=200)
