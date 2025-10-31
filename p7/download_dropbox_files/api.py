"""API endpoint to download Dropbox files for a user."""

import requests
import os
import uuid
import json

from ninja import Router, Header
from django.conf import settings
from django.http import JsonResponse
from p7.helpers import validate_internal_auth
from p7.get_dropbox_files.helper import get_new_access_token
from p7.fetch_downloadable_files.api import fetch_downloadable_files
from repository.file import update_tsvector
from repository.service import get_tokens, get_service
from repository.user import get_user

download_dropbox_files_router = Router()
@download_dropbox_files_router.get("/")
def download_dropbox_files(
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

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "dropbox")
    service = get_service(user_id, "dropbox")

    try:
        access_token, access_token_expiration = get_new_access_token(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )
        
        files = download_recursive_files(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )
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

def download_recursive_files(
    service,
    access_token,
    access_token_expiration,
    refresh_token,
):
    """Download files recursively from a user's Dropbox account."""

    # Fetch file entries from the database for this user
    # get_dropbox_files_for_user should return an iterable of objects with
    # attributes: dropbox_path (or dropbox_id) and filename
    dropbox_files = fetch_downloadable_files(service)
    if not dropbox_files:
        return {"saved": [], "note": "no files found in database"}

    saved = []
    media_dir = os.path.join(settings.MEDIA_ROOT, "dropbox")
    os.makedirs(media_dir, exist_ok=True)

    for dropbox_file in dropbox_files:
        # Choose the arg format you store (path or id). Dropbox API accepts either.
        dropbox_arg = {"path": dropbox_file.serviceFileId}
        response = requests.post(
            "https://content.dropboxapi.com/2/files/download",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Dropbox-API-Arg": json.dumps(dropbox_arg),
            },
        )
        
        dropbox_result = json.loads(response.headers.get("Dropbox-API-Result"))
        dropbox_content = response.content.decode('utf-8', errors='ignore') if response.content else None
        
        if response.status_code != 200 and dropbox_result is None:
            raise ConnectionError(f"Dropbox download failed for {dropbox_file}: {response.status_code} - {response.text}")

        if dropbox_content:
            try:
                update_tsvector(
                    dropbox_file,
                    dropbox_result.get("name", None),
                    dropbox_content,
                )
                print(dropbox_content)
            except Exception as e:
                # don't fail the whole loop for a tsvector error; optionally log
                print(str(e))

        saved.append({
            "db_id": getattr(dropbox_file, "id", None),
            "original_name": getattr(dropbox_file, "filename", None),
        })

    return {"saved": saved}
