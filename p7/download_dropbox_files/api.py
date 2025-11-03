"""API endpoint to download Dropbox files for a user."""

import requests
import os
import json

from ninja import Router, Header
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
    """Download Dropbox files for a given user.

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
        )
        
        return JsonResponse(files, safe=False)
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
):
    """Download files recursively from a user's Dropbox account."""

    dropbox_files = fetch_downloadable_files(service)
    if not dropbox_files:
        return False # do error handling here

    files = []
    for dropbox_file in dropbox_files:
        response = requests.post(
            "https://content.dropboxapi.com/2/files/download",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Dropbox-API-Arg": json.dumps({"path": dropbox_file.serviceFileId}),
            },
        )
        
        dropbox_result = json.loads(response.headers.get("Dropbox-API-Result"))
        dropbox_content = response.content.decode('utf-8', errors='ignore') if response.content else None
        
        if response.status_code != 200 and dropbox_result is None:
            # do better error handling
            raise ConnectionError(f"Dropbox download failed for {dropbox_file}: {response.status_code} - {response.text}")

        if dropbox_content:
            try:
                update_tsvector(
                    dropbox_file,
                    dropbox_result.get("name"),
                    dropbox_content,
                )
                
                dropbox_result['content'] = dropbox_content
                files.append(dropbox_result)
            except Exception as e:
                # don't fail the whole loop for a tsvector error; optionally log
                return False # do error handling here

    return files
