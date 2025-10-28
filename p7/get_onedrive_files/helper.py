"""Helper functions for Google Drive file operations."""
import os
from datetime import datetime, timezone
import requests

from repository.file import save_file

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

def fetch_recursive_files(
    app,
    service,
    access_token: str,
    access_token_expiration: datetime,
    refresh_token: str,
    page_limit: int = 999,
) -> list[dict]:
    """Helper function to fetch the initial set of files from Dropbox."""

    access_token = get_new_access_token(
        service,
        app,
        access_token,
        access_token_expiration,
        refresh_token,
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    def walk(
        url: str,
        depth: int = 0,
        access_token: str = access_token,
    ) -> list[
        dict
    ]:  # dette kan der i hvertfald godt være nogle workers som kan tage sig af
        results: list[dict] = []

        while url:
            access_token = get_new_access_token(
                service,
                app,
                access_token,
                access_token_expiration,
                refresh_token,
            )
            headers["Authorization"] = f"Bearer {access_token}"
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
                                access_token,
                            )
                        )
                    elif "file" in obj:
                        results.append(obj)

            url = data.get("@odata.nextLink", None)  # follow paging if present
            if "@odata.nextLink" in data:
                print(f"Following paging link: {url}")

        return [result for result in results if not "folder" in result]

    return walk(
        f"https://graph.microsoft.com/v1.0/me/drive/root/children?$top={page_limit}",
        depth=0,
        access_token=access_token,
    )

def get_new_access_token(
    service,
    app,
    access_token: str,
    access_token_expiration: datetime,
    refresh_token: str,
) -> str:
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
        print("Refreshing OneDrive access token...")
        # Refresh token
        result = app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=["Files.Read.All"],
        )

        new_access_token = result["access_token"]
        new_refresh_token = result.get(
            "refresh_token"
        )

        # Optionally update the refresh token in the database
        if new_access_token or new_refresh_token:
            service.accessToken = new_access_token
            service.refreshToken = new_refresh_token
            service.save(update_fields=["accessToken", "refreshToken"])

        return new_access_token

    return access_token
