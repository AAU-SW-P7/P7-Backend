"""API endpoint for fetching and saving Dropbox files."""
import os
from ninja import Router, Header
from django.http import JsonResponse
from p7.helpers import validate_internal_auth, fetch_api
from repository.service import get_tokens, get_service
from repository.file import save_file


fetch_dropbox_files_router = Router()

@fetch_dropbox_files_router.get("/")
def fetch_dropbox_files(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    user_id: str = None,
):
    """Fetch and save Dropbox files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose Dropbox files are to be fetched.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    if not user_id:
        response = JsonResponse({"error": "user_id required"}, status=400)
        return response

    access_token, _ = get_tokens(user_id, "dropbox")
    service = get_service(user_id, "dropbox")

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
            # Behøves vi dette? Vi kunne jo tage "path" ("path" + "name")
            # og smække "https://www.dropbox.com/preview" på frontenden

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
        return JsonResponse(files, safe=False, status=200)
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
