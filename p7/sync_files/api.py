"""API for syncing files from all services for a user."""
from ninja import Router, Header
from django.http import JsonResponse

from p7.get_dropbox_files.api import sync_dropbox_files
from p7.get_google_drive_files.api import sync_google_drive_files
from p7.get_onedrive_files.api import sync_onedrive_files
from repository.service import get_service

sync_files_router = Router()
@sync_files_router.get("/")
def sync_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """Sync files from all available services for a given user.
        params:
            x_internal_auth (str): The internal auth header for validating the request.
            user_id (str): The ID of the user whose files are to be synced.
    """
    dropbox_service = get_service(user_id, "dropbox")
    google_drive_service = get_service(user_id, "google")
    onedrive_service = get_service(user_id, "microsoft-entra-id")

    dropbox_updated_files = []

    google_drive_updated_files = []

    onedrive_updated_files = []

    if dropbox_service and not isinstance(dropbox_service, JsonResponse):
        dropbox_updated_files = sync_dropbox_files(x_internal_auth, user_id)
    if google_drive_service and not isinstance(google_drive_service, JsonResponse):
        google_drive_updated_files = sync_google_drive_files(x_internal_auth, user_id)
    if onedrive_service and not isinstance(onedrive_service, JsonResponse):
        onedrive_updated_files = sync_onedrive_files(x_internal_auth, user_id)

    combined_updated_files = (
        dropbox_updated_files + google_drive_updated_files + onedrive_updated_files
    )

    return JsonResponse({"ok": True}, status=200)
