import requests

from django.conf import settings
from django.http import JsonResponse
from repository.service import get_tokens

def fetch_drive_files(request):
    # Determine user id
    user_id = getattr(request.user, "id", None) or request.GET.get("userId")
    if not user_id:
        return JsonResponse({"error": "userId required"}, status=400)
    
    access_token, refresh_token = get_tokens(user_id, 'dropbox')
    
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
                if "has_more" in response_json and not response_json["has_more"]:
                    break

        return JsonResponse(files, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)