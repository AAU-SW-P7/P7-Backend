import os

from django.conf import settings
from django.http import JsonResponse
from django.db import connection

# Google libs
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

HTTP_TIMEOUT_SECONDS = 60          # per-request timeout
MAX_TOTAL_FILES = None             # set an int to hard-cap results, e.g., 20_000
RETRY_EXECUTE = 5
FIELDS = (
    "nextPageToken,"
    "files(id,name,mimeType,size,modifiedTime,parents,owners(displayName,emailAddress),"
    "driveId,trashed,webViewLink,iconLink)"
)

def fetch_drive_files(request):
    """
    Fetch files from Google Drive for a given user.
    Uses access_token and refresh_token stored in the `accounts` table.
    Provide userId either as request.user.id (if authenticated) or ?userId=...
    """
    # Determine user id
    user_id = getattr(request.user, "id", None) or request.GET.get("userId")
    if not user_id:
        return JsonResponse({"error": "userId required"}, status=400)

    # Read tokens from DB (simple raw SQL; adapt if you have an ORM model)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT access_token, refresh_token FROM accounts WHERE \"userId\" = %s LIMIT 1",
            [int(user_id)],
        )
        row = cursor.fetchone()

    if not row:
        return JsonResponse({"error": "No account tokens found for user"}, status=404)

    access_token, refresh_token = row

    if not refresh_token:
        return JsonResponse({"error": "No refresh_token available"}, status=400)

    # Build credentials object. token may be stale; refresh() will update it.
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=getattr(settings, "GOOGLE_CLIENT_ID", os.getenv("GOOGLE_ID")),
        client_secret=getattr(settings, "GOOGLE_CLIENT_SECRET", os.getenv("GOOGLE_SECRET")),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )

    try:
        # Refresh if needed (this will update creds.token)
        if not creds.valid:
            creds.refresh(Request())

        # Optionally persist the new access_token back to DB so next calls use it
        new_token = creds.token
        if new_token and new_token != access_token:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE accounts SET access_token = %s WHERE \"userId\" = %s",
                    [new_token, int(user_id)],
                )

        # Build Drive service and list files
        service = build("drive", "v3", credentials=creds)
        # Request all file fields and paginate through results
        files = []
        page_token = None
        while True:
            resp = service.files().list(
                pageSize=1000,
                fields="nextPageToken, files(id, name, parents, " \
                "                            capabilities/canCopy, capabilities/canDownload, downloadRestrictions, " \
                "                            kind, mimeType, starred, " \
                "                            trashed, webContentLink, webViewLink, " \
                "                            iconLink, hasThumbnail, viewedByMeTime, " \
                "                            createdTime, modifiedTime, shared, " \
                "                            ownedByMe, originalFilename, fullFileExtension, " \
                "                            size)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            files.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return JsonResponse({"files": files})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)