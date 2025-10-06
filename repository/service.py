import os
import requests
from datetime import datetime
from typing import Dict, Any

# Helper: compute the folder path pieces for a given folder id (memoized)
from functools import lru_cache

from ninja import Router, Body, Header
from django.http import JsonResponse
from django.db import IntegrityError
from repository.models import User, Service, File

# Google libs
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Microsoft libs
import msal

fetch_dropbox_files_router = Router()
fetch_google_drive_files_router = Router()
fetch_onedrive_files_router = Router()
create_user_router = Router()
find_user_by_email_router = Router()
create_service_router = Router()
find_services_router = Router()

def _validate_internal_auth(x_internal_auth: str) -> Any:
    """
    Validate the internal auth header value. Returns JsonResponse on failure, otherwise None.
    """
    if x_internal_auth != os.getenv("INTERNAL_API_KEY"):
        return JsonResponse({"error": "Unauthorized - invalid x-internal-auth"}, status=401)
    return None

def _google_drive_folder_path_parts(folder_id: str, file_by_id: Dict[str, dict]) -> list:
    """
    Returns a list like ['FolderA', 'FolderB'] for a folder id.
    Stops gracefully if an ancestor isn't in `files`.
    Works for 'root' (My Drive) and shared drives (top-level folder has no parents).
    """
    if not folder_id or folder_id == "root":
        return []

    folder = file_by_id.get(folder_id)
    if not folder:                      # ancestor not present in current listing
        return []                       # return partial path instead of failing

    parents = folder.get("parents") or []
    # Use the first parent if multiple
    prefix = _google_drive_folder_path_parts(parents[0], file_by_id) if parents else []
    return prefix + [folder.get("name", folder_id)]

@fetch_dropbox_files_router.get("/")
def fetch_dropbox_files(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), userId: str = None):
    auth_resp = _validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    if not userId:
        return JsonResponse({"error": "userId required"}, status=400)

    access_token, refresh_token = get_tokens(userId, 'dropbox')
    
    try:
        service = Service.objects.get(userId_id=userId, name='dropbox')
    except Service.DoesNotExist:
        return JsonResponse({"error": "Service (Dropbox) not found for user"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve service (Dropbox)", "detail": str(e)}, status=500)

    try:
        # Fetch root folder metadata
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

        response = requests.post(url, headers=headers, json=data)
        if not response.ok:
            return JsonResponse({"error": "Failed to fetch files", "details": response.json()}, status=response.status_code)
        
        response_json = response.json()
        files = response_json["entries"]
        pages_searched = 1
        if "has_more" in response_json and response_json["has_more"] and "cursor" in response_json:
            cursor = response_json["cursor"]
            while cursor:
                response = requests.post(url + '/continue', headers=headers, json={"cursor": cursor})
                if not response.ok:
                    return JsonResponse({"error": "Failed to fetch files", "details": response.json()}, status=response.status_code)
                response_json = response.json()
                print(response_json)
                cursor = response_json.get("cursor")
                if "entries" in response_json:
                    files.extend(response_json["entries"])
                    pages_searched += 1
                    print(f"Fetched page {pages_searched}, total items: {len(files)}")
                    break # for testing, remove later
                if "has_more" in response_json and not response_json["has_more"]:
                    break
                
        for file in files:
            if file[".tag"] != "file":
                continue
            
            File.objects.create(
                serviceId=service,
                serviceFileId=file["id"],
                name=file["name"],
                extension=os.path.splitext(file["name"])[1],
                downloadable=file.get("is_downloadable"),
                path=file["path_display"], # or path_lower? - Vi burde nok fjerne "name" fra path for at spare plads
                link="https://www.dropbox.com/preview" + file["path_display"], # Behøves vi dette? Vi kunne jo tage "path" ("path" + "name") og smække "https://www.dropbox.com/preview" på frontenden
                size=file["size"],
                createdAt=file["client_modified"],
                modifiedAt=file["server_modified"],
                lastIndexed=None,
                snippet=None,
                content=None,
            )

        # return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@fetch_google_drive_files_router.get("/")
def fetch_google_drive_files(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), userId: str = None):
    auth_resp = _validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    if not userId:
        return JsonResponse({"error": "userId required"}, status=400)

    access_token, refresh_token = get_tokens(userId, 'google')

    try:
        service = Service.objects.get(userId_id=userId, name='google')
    except Service.DoesNotExist:
        return JsonResponse({"error": "Service (Google) not found for user"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve service (Google)", "detail": str(e)}, status=500)

    try:
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

        # Refresh if needed (this will update creds.token)
        if not creds.valid:
            print("Refreshing Google access token...")
            creds.refresh(Request())

        # Optionally persist the new access_token back to DB so next calls use it
        new_token = creds.token
        if new_token and new_token != access_token:
            # Update via Django ORM instead of raw SQL
            service.accessToken = new_token
            service.save(update_fields=['accessToken'])

        # Build Drive service and list files
        drive_api = build("drive", "v3", credentials=creds)
        # Request all file fields and paginate through results
        files = []
        page_token = None
        while True:
            resp = drive_api.files().list(
                pageSize=1000,
                fields="nextPageToken, files(id, name, parents, " \
                       "capabilities/canCopy, capabilities/canDownload, downloadRestrictions, " \
                       "kind, mimeType, starred, " \
                       "trashed, webContentLink, webViewLink, " \
                       "iconLink, hasThumbnail, viewedByMeTime, " \
                       "createdTime, modifiedTime, shared, " \
                       "ownedByMe, originalFilename, size)",
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            files.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        # Build a fast lookup for any item (files + folders)
        file_by_id = {file["id"]: file for file in files}

        def build_google_drive_path(file_meta: dict) -> str:
            """
            Build a display path like /FolderA/FolderB/filename using only the current `files` array.
            """
            parents = file_meta.get("parents") or []
            prefix_parts = _google_drive_folder_path_parts(parents[0], file_by_id) if parents else []
            # Join and include filename at the end to mimic Dropbox-style path_display
            return "/" + "/".join(prefix_parts + [file_meta.get("name", "")])

        for file in files:
            if file.get("mimeType") == "application/vnd.google-apps.folder" or \
               file.get("mimeType") == "application/vnd.google-apps.shortcut" or \
               file.get("mimeType") == "application/vnd.google-apps.drive-sdk": # https://developers.google.com/workspace/drive/api/guides/mime-types
                continue

            File.objects.create(
                serviceId=service,
                serviceFileId=file.get("id"),
                name=file.get("name"),
                extension=os.path.splitext(file.get("name", ""))[1],
                downloadable=file.get("capabilities", {}).get("canDownload"),
                path=build_google_drive_path(file),
                link=file.get("webViewLink"),
                size=file.get("size", 0), # size may be missing for Google Docs files
                createdAt=file.get("createdTime"),
                modifiedAt=file.get("modifiedTime"),
                lastIndexed=None,
                snippet=None,
                content=None,
            )
        
        # return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@fetch_onedrive_files_router.get("/")
def fetch_onedrive_files(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), userId: str = None):
    auth_resp = _validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    if not userId:
        return JsonResponse({"error": "userId required"}, status=400)

    access_token, refresh_token = get_tokens(userId, 'microsoft-entra-id')
    
    try:
        service = Service.objects.get(userId_id=userId, name='microsoft-entra-id')
    except Service.DoesNotExist:
        return JsonResponse({"error": "Service (OneDrive) not found for user"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve service (OneDrive)", "detail": str(e)}, status=500)

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
        new_refresh_token = result.get("refresh_token")  # May be None; only update if provided

        # Optionally update the refresh token in the database
        if new_refresh_token:
            service.refreshToken = new_refresh_token
            service.save(update_fields=["refreshToken"])

        def get_onedrive_tree(access_token: str, page_limit: int = 999) -> list[dict]:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            def walk(url: str, depth: int = 0) -> list[dict]: # dette kan der i hvertfald godt være nogle workers som kan tage sig af
                results: list[dict] = []

                while url:
                    resp = requests.get(url, headers=headers, timeout=30)
                    
                    if resp.ok:
                        data = resp.json()
                        items = data.get("value", [])

                        for obj in items:
                            if "folder" in obj:
                                child_id = obj["id"]
                                print(f"Recursing into folder {obj.get('name')} (id={child_id}) at depth {depth}")
                                results.extend(walk(f"https://graph.microsoft.com/v1.0/me/drive/items/{child_id}/children?$top={page_limit}", depth + 1))
                            elif "file" in obj:
                                results.append(obj)
                    
                    url = data.get("@odata.nextLink", None) # follow paging if present
                    if "@odata.nextLink" in data:
                        print(f"Following paging link: {url}")

                return results

            return walk(f"https://graph.microsoft.com/v1.0/me/drive/root/children?$top={page_limit}")
                
        for file in get_onedrive_tree(access_token, page_limit=999):
            if "folder" in file:  # Skip folders
                continue

            File.objects.create(
                serviceId=service,
                serviceFileId=file["id"],
                name=file["name"],
                extension=os.path.splitext(file["name"])[1],
                downloadable=True,  # idk, der er ikke noget felt for det i onedrive
                path=(file.get("parentReference", {}).get("path", "")).replace("/drive/root:", "") + "/" + file["name"],
                link=file.get("webUrl"), # file.get("@microsoft.graph.downloadUrl", ""),
                size=file.get("size", 0),
                createdAt=file.get("createdDateTime"),
                modifiedAt=file.get("lastModifiedDateTime"),
                lastIndexed=None,
                snippet=None,
                content=None,
            )

        # return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@create_user_router.post("/")
def create_user(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), payload: Dict[str, str] = Body(...)):
    auth_resp = _validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    username = payload.get("username")
    primary_provider = payload.get("primaryProvider")

    # if not all([username, primary_provider]):
    #     return JsonResponse({"error": "username and primaryProvider required"}, status=400)

    try:
        user = User.objects.create(
            # username=None,
            # primaryProvider=primary_provider
        )
    except IntegrityError as e:
        return JsonResponse({"error": "Failed to create user", "detail": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "Failed to create user", "detail": str(e)}, status=500)

    return {
        "id": user.id,
        # "username": user.username,
        # "primary_provider": user.primary_provider_id,
    }

@find_user_by_email_router.get("/")
def find_user_by_email(request, email: str, x_internal_auth: str = Header(..., alias="x-internal-auth")):
    auth_resp = _validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    if not email:
        return JsonResponse({"error": "email required"}, status=400)

    try:
        service = Service.objects.filter(email=email).first()
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve user", "detail": str(e)}, status=500)

    if not service:
        return JsonResponse({"error": "User not found"}, status=404)

    return {
        "id": service.userId_id,
        "email": service.email,
        # "primaryProvider": service.userId.primaryProvider if needed,
    }

@create_service_router.post("/")
def create_service(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), payload: Dict[str, Any] = Body(...)):
    auth_resp = _validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    userId = payload.get("userId")
    oauthType = payload.get("oauthType")
    oauthToken = payload.get("oauthToken")
    accessToken = payload.get("accessToken")
    accessTokenExpiration = payload.get("accessTokenExpiration")
    refreshToken = payload.get("refreshToken")
    name = payload.get("name")
    accountId = payload.get("accountId")
    email = payload.get("email")
    scopeName = payload.get("scopeName")

    if not all([userId, oauthType, oauthToken, accessToken, accessTokenExpiration, refreshToken, name, accountId, email, scopeName]):
        return JsonResponse({"error": "All fields are required"}, status=400)
    
    if isinstance(accessTokenExpiration, int):
        accessTokenExpiration = datetime.fromtimestamp(accessTokenExpiration)

    try:
        # ensure we pass a User instance (ForeignKey expects model instance)
        user = User.objects.get(pk=userId)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve user", "detail": str(e)}, status=500)

    try:
        service = Service.objects.create(
            userId=user,
            oauthType=oauthType,
            oauthToken=oauthToken,
            accessToken=accessToken,
            accessTokenExpiration=accessTokenExpiration,
            refreshToken=refreshToken,
            name=name,
            accountId=accountId,
            email=email,
            scopeName=scopeName,
        )
    except IntegrityError as e:
        return JsonResponse({"error": "Failed to create service", "detail": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "Failed to create service", "detail": str(e)}, status=500)

    return {
        "id": service.id,
        # "userId": service.userId,
        # "oauthType": service.oauthType,
        "name": service.name,
        # "accountId": service.accountId,
        # "scopeName": service.scopeName,
    }

@find_services_router.get("/")
def find_services(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), userId: str = None):
    auth_resp = _validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    if not userId:
        return JsonResponse({"error": "userId required"}, status=400)

    try:
        qs = Service.objects.filter(userId_id=userId)
    except Service.DoesNotExist:
        return JsonResponse({"error": "Service not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve service", "detail": str(e)}, status=500)

    def _serialize(service: Service):
        return {
            "id": service.id,
            "userId": service.userId.id,
            "oauthType": service.oauthType,
            "oauthToken": service.oauthToken,
            "accessToken": service.accessToken,
            "accessTokenExpiration": int(service.accessTokenExpiration.timestamp()),
            "refreshToken": service.refreshToken,
            "name": service.name,
            "accountId": service.accountId,
            "email": service.email,
            "scopeName": service.scopeName,
        }

    return [_serialize(s) for s in qs]

# Security risk with passing userid directly, should be fixed with session.
def get_tokens(user_id, service_name):
    """
    Fetches refresh and access token from database
    """
    try:
        service = Service.objects.get(userId=user_id, name=service_name)
    except Service.DoesNotExist:
        return JsonResponse({"error": "No account tokens found for user"}, status=404)
    
    return service.accessToken, service.refreshToken