"""API endpoint to download OneDrive files for a user."""

# Microsoft libs
import os
import msal
import requests

from ninja import Router, Header
from django.http import JsonResponse
from repository.file import update_tsvector
from repository.service import get_tokens, get_service
from repository.user import get_user
from p7.helpers import validate_internal_auth
from p7.get_onedrive_files.helper import get_new_access_token
from p7.fetch_downloadable_files.api import fetch_downloadable_files

download_onedrive_files_router = Router()


@download_onedrive_files_router.get("/")
def download_onedrive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Download OneDrive files for a given user.

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

    access_token, access_token_expiration, refresh_token = get_tokens(
        user_id, "onedrive"
    )
    service = get_service(user_id, "onedrive")

    try:
        app = msal.ConfidentialClientApplication(
            os.getenv("MICROSOFT_CLIENT_ID"),
            authority="https://login.microsoftonline.com/common",
            client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
        )
        access_token = get_new_access_token(
            service, app, access_token, access_token_expiration, refresh_token
        )
        print(access_token)

        files = download_recursive_files(
            service,
            access_token,
        )
        return JsonResponse(files, safe=False)
    except KeyError as e:
        response = JsonResponse({"error": f"Missing key: {str(e)}"}, status=500)
        print("ERROR 1")
        return response
    except ValueError as e:
        response = JsonResponse({"error": f"Value error: {str(e)}"}, status=500)
        print("ERROR 2")
        return response
    except ConnectionError as e:
        response = JsonResponse({"error": f"Connection error: {str(e)}"}, status=500)
        print("ERROR 3")
        return response
    except RuntimeError as e:
        response = JsonResponse({"error": f"Runtime error: {str(e)}"}, status=500)
        print("ERROR 4")
        return response
    except TypeError as e:
        response = JsonResponse({"error": f"Type error: {str(e)}"}, status=500)
        print("ERROR 5")
        return response
    except OSError as e:
        response = JsonResponse({"error": f"OS error: {str(e)}"}, status=500)
        print("ERROR 6")
        return response


def download_recursive_files(
    service,
    access_token: str,
):
    """Download files recursively from a user's OneDrive account.

    Returns a list of File-like objects (from the `repository.models.File` type)
    or False on error.
    """

    # Tell static type checkers that we expect a list of File objects here.
    onedrive_files = fetch_downloadable_files(service)
    if not onedrive_files:
        return []  # Return empty as it has a filetype we do not handle yet

    files = []
    for file in onedrive_files:
        # `file` is expected to be an instance of `repository.models.File`.
        response = requests.post(
            f"https://graph.microsoft.com/v1.0/me/drive/items/{file.serviceFileId}/content",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            timeout=1000,
        )

        file_content = (
            response.content.decode("utf-8", errors="ignore")
            if response.content
            else None
        )

        if response.status_code != 200:
            # Do better error handling
            raise ConnectionError(
                f"Onedrive download failed for {file}: {response.status_code} - {response.text}"
            )

        if file_content:
            try:
                update_tsvector(
                    file,
                    file.name,
                    file_content,
                )
                files.append(
                    {
                        "id": file.serviceFileId,
                        "name": file.name,
                        "content": file_content,
                    }
                )
            except (ValueError, TypeError, KeyError, RuntimeError) as e:
                print(f"Failed to download {file.serviceFileId} ({file.name}): {e}")
    return files
