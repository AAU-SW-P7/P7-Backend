"""Helper functions for fetching and processing Dropbox files."""

from datetime import datetime, timezone, timedelta
import os
import requests
from django.http import JsonResponse
from repository.file import save_file
from p7.helpers import fetch_api, smart_extension


def update_or_create_file(file, service):
    """Updates or creates a file record in the database based on Dropbox file metadata.
    params:
    file: A dictionary containing Dropbox file metadata.
    service: The service object associated with the user.
    """
    extension = smart_extension("dropbox", file["name"], file.get("mime_type"))
    path = file["path_display"]
    link = "https://www.dropbox.com/preview" + path

    save_file(
        service_id=service,
        service_file_id=file["id"],
        name=file["name"],
        extension=extension,
        downloadable=file["is_downloadable"],
        path=path,
        link=link,
        size=file["size"],
        created_at=file["client_modified"],
        modified_at=file["server_modified"],
        indexed_at=None,
        snippet=None,
    )



def fetch_recursive_files(
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
        },
    ).json()
    files = response_json["entries"]

    if (
        "has_more" in response_json
        and response_json["has_more"]
        and "cursor" in response_json
    ):
        cursor = response_json["cursor"]
        while cursor:
            access_token, access_token_expiration = get_new_access_token(
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
                },
            )
            response_json = response.json()
            cursor = response_json.get("cursor")

            if "entries" in response_json:
                files.extend(response_json["entries"])

            if "has_more" in response_json and not response_json["has_more"]:
                break
    return files


def get_new_access_token(
    service,
    access_token: str,
    access_token_expiration: datetime,
    refresh_token: str,
) -> tuple[str, datetime]:
    """Helper function to get a new access token using the refresh token.

    params:
        service (service obj): The service which may need a new access token.
        access_token (str): The current access token.
        access_token_expiration (datetime): The current expiration datetime.
        refresh_token (str): The refresh token to use for obtaining a new access token.

    returns:
        A pair of an access token and an expiration datetime.
        If the passed access token has run out, then a new access token and datetime is returned.
        Otherwise, the passed access token and datetime is returned.
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
                timeout=10,
            )
        except requests.RequestException:
            return JsonResponse({"error": "Refreshing access token failed"}, status=400)

        if token_resp.status_code != 200:
            return JsonResponse(
                {"error": "Token response not 200"}, status=token_resp.status_code
            )

        token_json = token_resp.json()
        new_access_token = token_json.get("access_token")

        expires_in = token_json.get("expires_in")
        access_token_expiration = datetime.now(timezone.utc) + timedelta(
            seconds=int(expires_in)
        )

        service.accessToken = new_access_token
        service.accessTokenExpiration = access_token_expiration
        service.save(update_fields=["accessToken", "accessTokenExpiration"])

        return new_access_token, access_token_expiration

    return access_token, access_token_expiration
