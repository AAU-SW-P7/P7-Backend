"""API for fetching and syncing OneDrive files."""
import os
from datetime import datetime, timezone
import requests

from ninja import Router, Header
from django.http import JsonResponse

# Microsoft libs
import msal

from p7.helpers import validate_internal_auth
from repository.service import get_tokens, get_service
from repository.file import save_file

fetch_onedrive_files_router = Router()

@fetch_onedrive_files_router.get("/")
def fetch_onedrive_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """Fetches all file metadata from OneDrive API and saves it to the DB.
        params:
        x_internal_auth: Internal auth token for validating the request.
        userId: The id of the user whose files are to be fetched.
    """
    try:
        access_token, service = get_file_meta_data(x_internal_auth, user_id)

        for file in get_onedrive_tree(access_token, page_limit=999):
            if "folder" in file:  # Skip folders
                continue
            update_or_create_file(file, service)
        return JsonResponse({"status": "success"}, status=200)
    except (ValueError, TypeError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)


sync_onedrive_files_router = Router()

@sync_onedrive_files_router.get("/")
def sync_onedrive_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params:
        request: The HTTP request object.
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be synced.
    """
    try:
        access_token, service = get_file_meta_data(x_internal_auth, user_id)
        updated_files = []
        for file in get_onedrive_tree(access_token, page_limit=999):
            if "folder" in file:  # Skip folders
                continue
            if file["lastModifiedDateTime"] <= service.indexedAt.isoformat():
                continue  # No changes since last sync
            # updated_files should be used, when we want to index the updated files
            updated_files.append(file)
            update_or_create_file(file, service)
        return JsonResponse({"status": "success"}, status=200)
    except (ValueError, TypeError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_file_meta_data(
    x_internal_auth,
    user_id
    ):
    """Fetches all file metadata from OneDrive API.
        params:
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be fetched.

        Returns:
        List of fetched files 
        Service object.
    """
    auth_resp = validate_internal_auth(x_internal_auth)

    if auth_resp:
        return auth_resp

    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "microsoft-entra-id")
    service = get_service(user_id, "microsoft-entra-id")

    # Build MSAL app instance
    app = msal.ConfidentialClientApplication(
        os.getenv("MICROSOFT_CLIENT_ID"),
        authority="https://login.microsoftonline.com/common",
        client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
    )

    # Scopes that should match what was consented at initial sign-in.
    # Ensure your initial auth requested offline_access and the Graph file scope.
    scopes = ["Files.Read.All"]

    # Refresh token
    result = app.acquire_token_by_refresh_token(
        refresh_token,
        scopes=scopes,
    )

    access_token = result["access_token"]
    new_refresh_token = result.get(
        "refresh_token"
    )  # May be None; only update if provided

    # Optionally update the refresh token in the database
    if new_refresh_token:
        service.refreshToken = new_refresh_token
        service.save(update_fields=["refreshToken"])

    return access_token, service

def update_or_create_file(file, service):
    """Updates or creates a File entry in the database based on OneDrive file metadata.
        params:
        file: A dictionary containing OneDrive file metadata.
        service: The service object associated with the user.
    """
    extension = os.path.splitext(file["name"])[1]
    path = (
        (file.get("parentReference", {}).get("path", "")).replace(
            "/drive/root:", ""
        )
        + "/"
        + file["name"]
    )

    save_file(
        service,
        file["id"],
        file["name"],
        extension,
        True,
        path,
        file["webUrl"],
        file.get("size", 0),
        file["createdDateTime"],
        file["lastModifiedDateTime"],
        None,
        None,
        None,
    )

def get_onedrive_tree(access_token: str, page_limit: int = 999) -> list[dict]:
    """Recursively fetches all files from OneDrive using Microsoft Graph API.
        params:
        access_token: The OAuth2 access token for authenticating API requests.
        page_limit: Number of items to fetch per API call (max 999).

        Returns:
        The result of walk() on the OneDrive root children endpoint.
    """

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    def walk(
        url: str, depth: int = 0
    ) -> list[
        dict
    ]:  # dette kan der i hvertfald godt være nogle workers som kan tage sig af
        """Recursively walks through OneDrive folders to fetch all files.
            params:
            url: The API endpoint URL to fetch items from.
            depth: Current recursion depth.
        """
        results: list[dict] = []

        while url:
            resp = requests.get(url, headers=headers, timeout=30)

            if resp.ok:
                data = resp.json()
                items = data.get("value", [])

                for obj in items:
                    if "folder" in obj:
                        child_id = obj["id"]
                        print(
                                    f"Recursing into folder "\
                                    f"{obj.get('name')} (id={child_id}) at depth {depth}"
                                )
                        results.extend(
                            walk(
                                        f"https://graph.microsoft.com/"\
                                        f"v1.0/me/drive/items/{child_id}/children"\
                                        f"?$top={page_limit}",
                                        depth + 1,
                                    )
                        )
                    elif "file" in obj:
                        results.append(obj)

            url = data.get("@odata.nextLink", None)  # follow paging if present
            if "@odata.nextLink" in data:
                print(f"Following paging link: {url}")

        return results

    return walk(
        f"https://graph.microsoft.com/v1.0/me/drive/root/children?$top={page_limit}"
    )
