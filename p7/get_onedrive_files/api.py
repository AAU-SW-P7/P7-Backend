import os
import requests
from p7.helpers import validate_internal_auth, fetch_api
from repository.service import get_tokens, get_service
from repository.file import save_file

# Helper: compute the folder path pieces for a given folder id (memoized)
from functools import lru_cache

from ninja import Router, Body, Header
from django.http import JsonResponse
from django.db import IntegrityError
from repository.models import Service, File

# Microsoft libs
import msal

fetch_onedrive_files_router = Router()

@fetch_onedrive_files_router.get("/")
def fetch_onedrive_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    userId: str = None,
):
    auth_resp = validate_internal_auth(x_internal_auth)

    if auth_resp:
        return auth_resp

    if not userId:
        return JsonResponse({"error": "userId required"}, status=400)

    access_token, refresh_token = get_tokens(userId, "microsoft-entra-id")
    service = get_service(userId, "microsoft-entra-id")

    try:
        # Build MSAL app instance
        app = msal.ConfidentialClientApplication(
            os.getenv("MICROSOFT_CLIENT_ID"),
            authority="https://login.microsoftonline.com/common",
            client_credential=os.getenv("MICROSOFT_CLIENT_SECRET"),
        )

        # Scopes that should match what was consented at initial sign-in.
        # Ensure your initial auth requested offline_access and the Graph file scope.
        scopes = ["Files.Read.All"]

        # Refresh token
        result = app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=scopes,
        )

        access_token = result["access_token"]
        new_refresh_token = result.get(
            "refresh_token"
        )  # May be None; only update if provided

        # Optionally update the refresh token in the database
        if new_refresh_token:
            service.refreshToken = new_refresh_token
            service.save(update_fields=["refreshToken"])

        def get_onedrive_tree(access_token: str, page_limit: int = 999) -> list[dict]:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            def walk(
                url: str, depth: int = 0
            ) -> list[
                dict
            ]:  # dette kan der i hvertfald godt være nogle workers som kan tage sig af
                results: list[dict] = []

                while url:
                    resp = requests.get(url, headers=headers, timeout=30)

                    if resp.ok:
                        data = resp.json()
                        items = data.get("value", [])

                        for obj in items:
                            if "folder" in obj:
                                child_id = obj["id"]
                                print(
                                    f"Recursing into folder {obj.get('name')} (id={child_id}) at depth {depth}"
                                )
                                results.extend(
                                    walk(
                                        f"https://graph.microsoft.com/v1.0/me/drive/items/{child_id}/children?$top={page_limit}",
                                        depth + 1,
                                    )
                                )
                            elif "file" in obj:
                                results.append(obj)

                    url = data.get("@odata.nextLink", None)  # follow paging if present
                    if "@odata.nextLink" in data:
                        print(f"Following paging link: {url}")

                return results

            return walk(
                f"https://graph.microsoft.com/v1.0/me/drive/root/children?$top={page_limit}"
            )

        for file in get_onedrive_tree(access_token, page_limit=999):
            if "folder" in file:  # Skip folders
                continue

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

        # return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
