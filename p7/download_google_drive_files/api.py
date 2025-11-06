"""API for fetching and saving Google Drive files."""

import io
import os
from ninja import Router, Header
from django.http import JsonResponse

# Google libs
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from repository.file import update_tsvector
from repository.service import get_tokens, get_service
from repository.user import get_user
from p7.helpers import validate_internal_auth
from p7.get_google_drive_files.helper import get_new_access_token
from p7.fetch_downloadable_files.api import fetch_downloadable_files

download_google_drive_files_router = Router()


@download_google_drive_files_router.get("/")
def download_google_drive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Download Google Drive files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose Google Drive files are to be downloaded.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    access_token, _, refresh_token = get_tokens(user_id, "google")
    service = get_service(user_id, "google")

    try:
        # Build credentials object. token may be stale; refresh() will update it.
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )

        access_token = get_new_access_token(
            service,
            creds,
            access_token,
        )

        # Build Drive service and list files
        drive_api = build("drive", "v3", credentials=creds)

        files = download_recursive_files(
            drive_api,
            service,
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
    drive_api,
    service,
):
    """Download files recursively from a user's Google Drive account."""

    google_drive_files = fetch_downloadable_files(service)
    if not google_drive_files:
        print("No downloadable Google Drive files found.")

    files = []
    for google_drive_file in google_drive_files:
        file_id = google_drive_file.serviceFileId
        name = google_drive_file.name

        try:
            try:
                request = drive_api.files().export(
                    fileId=file_id, mimeType="text/plain"
                )
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                content = fh.getvalue().decode(
                    "utf-8-sig", errors="ignore"
                )  # decode with utf-8-sig to remove BOM if present

                update_tsvector(
                    google_drive_file,
                    google_drive_file.name,
                    content,
                )

                files.append(
                    {
                        "id": file_id,
                        "content": content,
                    }
                )
            except (ValueError, TypeError, RuntimeError):
                # Regular binary file -> get_media
                request = drive_api.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                content = fh.getvalue().decode(
                    "utf-8-sig", errors="ignore"
                )  # decode with utf-8-sig to remove BOM if present

                update_tsvector(
                    google_drive_file,
                    google_drive_file.name,
                    content,
                )

                files.append(
                    {
                        "id": file_id,
                        "content": content,
                    }
                )
        except (ValueError, TypeError, RuntimeError) as e:
            # log and continue
            print(f"Failed to download {file_id} ({name}): {e}")

    return files
