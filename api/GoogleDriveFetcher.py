import os

from django.conf import settings
from django.http import JsonResponse
from django.db import connection

# Google libs
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
            "SELECT accessToken, refreshToken FROM service WHERE \"userId\" = %s and name = 'google' LIMIT 1",
            [int(user_id)],
        )
        row = cursor.fetchone()

    if not row:
        return JsonResponse({"error": "No account tokens found for user"}, status=404)

    access_token, refresh_token = row

    if not refresh_token:
        return JsonResponse({"error": "No refresh_token available"}, status=400)

    # Ensure required OAuth fields are present (avoid refresh error)
    token_uri = "https://oauth2.googleapis.com/token"
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    missing = [name for name, val in (("refresh_token", refresh_token),
                                       ("token_uri", token_uri),
                                       ("client_id", client_id),
                                       ("client_secret", client_secret)) if not val]
    if missing:
        return JsonResponse(
            {"error": "Missing OAuth fields required to refresh token", "missing": missing},
            status=500,
        )

    # Build credentials object. token may be stale; refresh() will update it.
    creds = Credentials(
        token=access_token or None,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )

    try:
        # Refresh if needed (this will update creds.token)
        if not creds.valid:
            print("Refreshing Google access token...")
            creds.refresh(Request())

        # Optionally persist the new access_token back to DB so next calls use it
        new_token = creds.token
        if new_token and new_token != access_token:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE accounts SET access_token = %s WHERE \"userId\" = %s and provider = 'google'",
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

        return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)