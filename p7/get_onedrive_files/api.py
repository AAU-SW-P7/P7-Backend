"""Fetch OneDrive files for a user and save them to the database."""
import os
from datetime import datetime, timezone
import requests

from ninja import Router, Header
from django.http import JsonResponse

# Microsoft libs
import msal

from repository.service import get_tokens, get_service
from repository.file import save_file
from p7.helpers import validate_internal_auth

fetch_onedrive_files_router = Router()

@fetch_onedrive_files_router.get("/")
def fetch_onedrive_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Fetch and save OneDrive files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose OneDrive files are to be fetched.
    """
    auth_resp = validate_internal_auth(x_internal_auth)

    if auth_resp:
        return auth_resp

    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "microsoft-entra-id")
    service = get_service(user_id, "microsoft-entra-id")

    try:
        # Build MSAL app instance
        app = msal.ConfidentialClientApplication(
            os.getenv("MICROSOFT_CLIENT_ID"),
            authority="https://login.microsoftonline.com/common",
            client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
        )

        files = _fetch_recursive_files(
            app,
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )

        for file in files:
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

        return JsonResponse(files, safe=False)
    except (ValueError, TypeError, RuntimeError) as e:
        return JsonResponse({"error": str(e)}, status=500)

def _fetch_recursive_files(
    app,
    service,
    access_token: str,
    access_token_expiration: datetime,
    refresh_token: str,
    page_limit: int = 999,
) -> list[dict]:
    """Helper function to fetch the initial set of files from Dropbox."""

    access_token = _get_new_access_token(
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
            access_token = _get_new_access_token(
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

def _get_new_access_token(
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
