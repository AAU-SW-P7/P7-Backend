import os
import requests
from p7.helpers import validate_internal_auth, fetch_api
from repository.service import get_tokens, get_service
from repository.file import save_file

# Helper: compute the folder path pieces for a given folder id (memoized)
from functools import lru_cache

from ninja import Router, Header
from django.http import JsonResponse

fetch_dropbox_files_router = Router()

@fetch_dropbox_files_router.get("/")
def fetch_dropbox_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    userId: str = None,
):
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    if not userId:
        return JsonResponse({"error": "userId required"}, status=400)

    access_token, _ = get_tokens(userId, "dropbox")
    service = get_service(userId, "dropbox")

    try:
        url = "https://api.dropboxapi.com/2/files/list_folder"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        data = {
            "path": "",
            "recursive": True,
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_mounted_folders": True,
            "limit": 2000,
            "include_non_downloadable_files": True,
        }

        response_json = fetch_api(url, headers, data).json()
        files = response_json["entries"]

        pages_searched = 1

        if (
            "has_more" in response_json
            and response_json["has_more"]
            and "cursor" in response_json
        ):
            cursor = response_json["cursor"]
            while cursor:
                response = fetch_api(
                    url + "/continue", headers=headers, data={"cursor": cursor}
                )
                response_json = response.json()
                print(response_json)
                cursor = response_json.get("cursor")
                if "entries" in response_json:
                    files.extend(response_json["entries"])
                    pages_searched += 1
                    print(f"Fetched page {pages_searched}, total items: {len(files)}")
                    break  # for testing, remove later
                if "has_more" in response_json and not response_json["has_more"]:
                    break

        for file in files:
            if file[".tag"] != "file":
                continue

            extension = os.path.splitext(file["name"])[1]
            path = file["path_display"]
            link = "https://www.dropbox.com/preview" + path
            # Behøves vi dette? Vi kunne jo tage "path" ("path" + "name") og smække "https://www.dropbox.com/preview" på frontenden

            # Vi burde nok fjerne "name" fra path for at spare plads
            save_file(
                service,
                file["id"],
                file["name"],
                extension,
                file["is_downloadable"],
                path,
                link,
                file["size"],
                file["client_modified"],
                file["server_modified"],
                None,
                None,
                None,
            )
        # return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
