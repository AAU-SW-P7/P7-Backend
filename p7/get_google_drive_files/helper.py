"""Helper functions for Google Drive file operations."""

from datetime import datetime, timezone
from typing import Dict

# Google libs
from google.auth.transport.requests import Request

from repository.file import save_file
from p7.helpers import smart_extension


def update_or_create_file(file, service, file_by_id: Dict[str, dict]):
    """Updates or creates a File record from Google Drive file metadata.
    params:
    file: A dictionary containing Google Drive file metadata.
    service: The service object associated with the user.
    file_by_id: A dictionary mapping file IDs to their metadata for path construction.
    """
    extension = smart_extension("google", file["name"], file.get("mimeType"))
    downloadable = file.get("capabilities", {}).get("canDownload")
    path = build_google_drive_path(file, file_by_id)

    save_file(
        service_id=service,
        service_file_id=file["id"],
        name=file["name"],
        extension=extension,
        downloadable=downloadable,
        path=path,
        link=file["webViewLink"],
        size=file.get("size", 0), # Can be empty
        created_at=file["createdTime"],
        modified_at=file["modifiedTime"],
        indexed_at=None,
        snippet=None,
    )


def fetch_recursive_files(
    drive_api,
    service,
    creds,
    access_token: str,
) -> list[dict]:
    """Helper function to fetch the initial set of files from Dropbox."""

    files = []
    page_token = None
    while True:
        access_token = get_new_access_token(
            service,
            creds,
            access_token,
        )

        resp = (
            drive_api.files()
            .list(
                pageSize=1000,
                fields="nextPageToken, files(id, name, parents, "
                "capabilities/canCopy, capabilities/canDownload, downloadRestrictions, "
                "kind, mimeType, starred, "
                "trashed, webContentLink, webViewLink, "
                "iconLink, hasThumbnail, viewedByMeTime, "
                "createdTime, modifiedTime, shared, "
                "ownedByMe, originalFilename, size)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return files


def get_new_access_token(
    service,
    creds,
    access_token: str,
) -> str:
    """Helper function to get a new access token using the refresh token.

    params:
        refresh_token (str): The refresh token to use for obtaining a new access token.

    returns:
        str: A string with the new access token.
    """
    # Refresh if needed (this will update creds.token)
    if not creds.valid:
        print("Refreshing Google Drive access token...")
        creds.refresh(Request())

        # Optionally persist the new access_token back to DB so next calls use it
        new_token = creds.token
        new_token_expiration = datetime.fromtimestamp(
            creds.expiry.timestamp(), tz=timezone.utc
        )
        service.accessToken = new_token
        service.accessTokenExpiration = new_token_expiration
        service.save(update_fields=["accessToken", "accessTokenExpiration"])

        return new_token

    return access_token


def build_google_drive_path(file_meta: dict, file_by_id: dict) -> str:
    """
    Build a display path like /FolderA/FolderB/filename
    using only the current `files` array.

    params:
        file_meta (dict): The metadata dictionary of the file for which to build the path.
    returns:
        str: The constructed file path.
    """
    parents = file_meta.get("parents") or []
    prefix_parts = (
        google_drive_folder_path_parts(parents[0], file_by_id) if parents else []
    )
    # Join and include filename at the end to mimic Dropbox-style path_display
    return "/" + "/".join(prefix_parts + [file_meta.get("name", "")])


def google_drive_folder_path_parts(folder_id: str, file_by_id: Dict[str, dict]) -> list:
    """
    Returns a list like ['FolderA', 'FolderB'] for a folder id.
    Stops gracefully if an ancestor isn't in `files`.
    Works for 'root' (My Drive) and shared drives (top-level folder has no parents).
    params:
        folder_id (str): The Google Drive folder ID to build the path for.
        file_by_id (Dict[str, dict]): A mapping of file IDs to their metadata dictionaries.
    returns:
        list: A list of folder names from the root to the specified folder.
    """
    if not folder_id or folder_id == "root":
        return []

    folder = file_by_id.get(folder_id)
    if not folder:  # ancestor not present in current listing
        return []  # return partial path instead of failing

    parents = folder.get("parents")
    # Use the first parent if multiple
    prefix = google_drive_folder_path_parts(parents[0], file_by_id) if parents else []
    return prefix + [folder.get("name", folder_id)]
