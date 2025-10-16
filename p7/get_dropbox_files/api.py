"""API endpoint for fetching, saving, and syncing Dropbox files."""
from datetime import datetime, timezone, timedelta
import os
import requests

from ninja import Router, Header
from django.http import JsonResponse
from p7.helpers import validate_internal_auth, fetch_api
from repository.service import get_tokens, get_service
from repository.file import save_file

fetch_dropbox_files_router = Router()

@fetch_dropbox_files_router.get("/")
def fetch_dropbox_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """Fetches all file metadata from a user's Dropbox account and saves it to the DB
        params: 
        request: The HTTP request object.
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be fetched.
    """
    try:
        files, service = get_file_meta_data(x_internal_auth, user_id)

        for file in files:
            if file[".tag"] != "file":
                continue
            update_or_create_file(file, service)
        return JsonResponse({"status": "success"}, status=200)
    except KeyError as e:
        response = JsonResponse({"error": f"Missing key: {str(e)}"}, status=500)
        return response
    except ValueError as e:
        response = JsonResponse({"error": f"Value error: {str(e)}"}, status=500)
        return response
    except ConnectionError as e:
        response = JsonResponse({"error": f"Connection error: {str(e)}"}, status=500)
        return response
    except RuntimeError as e:
        response = JsonResponse({"error": f"Runtime error: {str(e)}"}, status=500)
        return response
    except TypeError as e:
        response = JsonResponse({"error": f"Type error: {str(e)}"}, status=500)
        return response
    except OSError as e:
        response = JsonResponse({"error": f"OS error: {str(e)}"}, status=500)
        return response


sync_dropbox_files_router = Router()
@sync_dropbox_files_router.get("/")
def update_dropbox_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """Fetches file metadata and updates files that have been modified since the last sync.
        params: 
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be synced.
    """
    try:
        files, service = get_file_meta_data(x_internal_auth, user_id)
        updated_files = []
        for file in files:
            if file[".tag"] != "file":
                continue
            if file["server_modified"] <= service.indexedAt:
                continue  # No changes since last sync
            # updated_files should be used, when we want to index the updated files
            updated_files.append(file)
            update_or_create_file(file, service)
        return JsonResponse({"status": "success"}, status=200)
    except KeyError as e:
        response = JsonResponse({"error": f"Missing key: {str(e)}"}, status=500)
        return response
    except ValueError as e:
        response = JsonResponse({"error": f"Value error: {str(e)}"}, status=500)
        return response
    except ConnectionError as e:
        response = JsonResponse({"error": f"Connection error: {str(e)}"}, status=500)
        return response
    except RuntimeError as e:
        response = JsonResponse({"error": f"Runtime error: {str(e)}"}, status=500)
        return response
    except TypeError as e:
        response = JsonResponse({"error": f"Type error: {str(e)}"}, status=500)
        return response
    except OSError as e:
        response = JsonResponse({"error": f"OS error: {str(e)}"}, status=500)
        return response

def get_file_meta_data(
    x_internal_auth,
    user_id
    ):
    """Fetches all file metadata from Dropbox API via list_folder endpoint.
        params:
        x_internal_auth: Internal auth token for validating the request.
        user_id: The id of the user whose files are to be fetched.

        Returns:
        list of fetched files
        service object.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    if not user_id:
        response = JsonResponse({"error": "user_id required"}, status=400)
        return response

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "dropbox")
    service = get_service(user_id, "dropbox")

    try:
        access_token, access_token_expiration = _get_new_access_token(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        files = _fetch_recursive_files(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        for file in files:
            if file[".tag"] != "file":
                continue

            extension = os.path.splitext(file["name"])[1]
            path = file["path_display"]
            link = "https://www.dropbox.com/preview" + path
            # Behøves vi dette? Vi kunne jo tage "path" ("path" + "name")
            # og smække "https://www.dropbox.com/preview" på frontenden
    url = "https://api.dropboxapi.com/2/files/list_folder"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    data = {
        "path": "",
        "recursive": True,
        "include_deleted": False,
        "include_has_explicit_shared_members": False,
        "include_mounted_folders": True,
        "limit": 2000,
        "include_non_downloadable_files": True,
    }
    response_json = fetch_api(url, headers, data).json()
    files = response_json["entries"]

    pages_searched = 1

    if (
        "has_more" in response_json
        and response_json["has_more"]
        and "cursor" in response_json
    ):
        cursor = response_json["cursor"]
        while cursor:
            response = fetch_api(
                url + "/continue", headers=headers, data={"cursor": cursor}
            )
            response_json = response.json()
            cursor = response_json.get("cursor")
            if "entries" in response_json:
                files.extend(response_json["entries"])
                pages_searched += 1
                break  # for testing, remove later
            if "has_more" in response_json and not response_json["has_more"]:
                break
    return files, service

def update_or_create_file(file, service):
    """ Updates or creates a file record in the database based on Dropbox file metadata.
        params:
        file: A dictionary containing Dropbox file metadata.
        service: The service object associated with the user.
    """
    extension = os.path.splitext(file["name"])[1]
    path = file["path_display"]
    link = "https://www.dropbox.com/preview" + path
    # Behøves vi dette?
    # Vi kunne jo tage "path" ("path" + "name")
    # og smække "https://www.dropbox.com/preview" på frontenden

    # Vi burde nok fjerne "name" fra path for at spare plads
    save_file(
        service,
        file["id"],
        file["name"],
        extension,
        file["is_downloadable"],
        path,
        link,
        file["size"],
        file["client_modified"],
        file["server_modified"],
        None,
        None,
        None,
    )

def _fetch_recursive_files(
    service,
    access_token: str,
    access_token_expiration: datetime,
    refresh_token: str,
) -> list[dict]:
    """Helper function to fetch the initial set of files from Dropbox."""

    response_json = fetch_api(
        "https://api.dropboxapi.com/2/files/list_folder", 
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        data={
            "path": "",
            "recursive": True,
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_mounted_folders": True,
            "limit": 2000,
            "include_non_downloadable_files": True,
        }
    ).json()
    files = response_json["entries"]

    if (
        "has_more" in response_json
        and response_json["has_more"]
        and "cursor" in response_json
    ):
        cursor = response_json["cursor"]
        while cursor:
            access_token, access_token_expiration = _get_new_access_token(
                service,
                access_token,
                access_token_expiration,
                refresh_token,
            )

            response = fetch_api(
                "https://api.dropboxapi.com/2/files/list_folder/continue", 
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                data={
                    "cursor": cursor,
                }
            )
            response_json = response.json()
            cursor = response_json.get("cursor")

            if "entries" in response_json:
                files.extend(response_json["entries"])

            if "has_more" in response_json and not response_json["has_more"]:
                break

    print(files)
    return files

def _get_new_access_token(
    service,
    access_token: str,
    access_token_expiration: datetime,
    refresh_token: str,
) -> tuple[str, datetime]:
    """Helper function to get a new access token using the refresh token.

    params:
        refresh_token (str): The refresh token to use for obtaining a new access token.
    
    returns:
        str: A string with the new access token.
    """
    now = datetime.now(timezone.utc)
    if access_token_expiration.tzinfo is None:
        access_token_expiration = access_token_expiration.replace(tzinfo=timezone.utc)

    if access_token_expiration <= now:
        print("Refreshing Dropbox access token...")
        try:
            token_resp = requests.post(
                "https://api.dropbox.com/oauth2/token", 
                headers={},
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": os.getenv("DROPBOX_CLIENT_ID"),
                    "client_secret": os.getenv("DROPBOX_CLIENT_SECRET"),
                },
                timeout=10
            )
        except requests.RequestException:
            pass # do error handling here?

        if token_resp.status_code != 200:
            pass # do error handling here?

        token_json = token_resp.json()
        new_access_token = token_json.get("access_token")

        expires_in = token_json.get("expires_in")
        access_token_expiration = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        service.accessToken = new_access_token
        service.accessTokenExpiration = access_token_expiration
        service.save(update_fields=["accessToken", "accessTokenExpiration"])

        return new_access_token, access_token_expiration

    return access_token, access_token_expiration
