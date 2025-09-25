import os
import requests

from django.conf import settings
from django.http import JsonResponse
from django.db import connection

# Microsoft libs
import msal

def fetch_drive_files(request):
    """
    Fetch files from OneDrive for a given user.
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
            "SELECT access_token, refresh_token FROM accounts WHERE \"userId\" = %s and provider = 'microsoft-entra-id' LIMIT 1",
            [int(user_id)],
        )
        row = cursor.fetchone()

    if not row:
        return JsonResponse({"error": "No account tokens found for user"}, status=404)

    access_token, refresh_token = row

    if not refresh_token:
        return JsonResponse({"error": "No refresh_token available"}, status=400)

    # Ensure required OAuth fields are present (avoid refresh error)
    # Use 'common' to support both org and personal.
    authority = "https://login.microsoftonline.com/common"
    client_id = os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
    missing = [name for name, val in (("refresh_token", refresh_token),
                                       ("authority", authority),
                                       ("client_id", client_id),
                                       ("client_secret", client_secret)) if not val]
    if missing:
        return JsonResponse(
            {"error": "Missing OAuth fields required to refresh token", "missing": missing},
            status=500,
        )
        
    try:

        # Build MSAL app instance
        app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret,
        )

        # Scopes that should match what was consented at initial sign-in.
        # Ensure your initial auth requested offline_access and the Graph file scope.
        scopes = ["Files.Read.All"]

        # Refresh token
        result = app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=scopes,
        )

        # Helpful diagnostics if refresh fails (common AADSTS700016 / wrong tenant or missing consent)
        if "access_token" not in result:
            # If the error says the user must sign in / grant consent, return an auth URL
            err_desc = result.get("error_description", "")
            if "must first sign in" in err_desc or "unauthorized or expired" in err_desc or result.get("error") in ("invalid_grant",):
                try:
                    redirect_uri = getattr(settings, "MICROSOFT_REDIRECT_URI", None)
                    auth_url = app.get_authorization_request_url(scopes, redirect_uri=redirect_uri)
                except Exception:
                    auth_url = None

                return JsonResponse(
                    {
                        "error": "Reauthentication required",
                        "details": result,
                        "reauth_url": auth_url,
                    },
                    status=401,
                )

            return JsonResponse(
                {"error": "Failed to refresh access token", "details": result},
                status=500,
            )

        access_token = result["access_token"]
        new_refresh_token = result.get("refresh_token")  # May be None; only update if provided

        # Optionally update the refresh token in the database
        if new_refresh_token:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE accounts SET refresh_token = %s WHERE \"userId\" = %s and provider = 'microsoft-entra-id'",
                    [new_refresh_token, int(user_id)],
                )

        def get_onedrive_tree(access_token: str, page_limit: int = 999) -> list[dict]:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            def walk(url: str, depth: int = 0) -> list[dict]:
                results: list[dict] = []

                while url:
                    resp = requests.get(url, headers=headers, timeout=30)
                    
                    if resp.ok:
                        data = resp.json()
                        items = data.get("value", [])

                        for obj in items:
                            if "folder" in obj:
                                child_id = obj.get("id")
                                print(f"Recursing into folder {obj.get('name')} (id={child_id}) at depth {depth}")
                                obj["children"] = walk(f"https://graph.microsoft.com/v1.0/me/drive/items/{child_id}/children?$top={page_limit}", depth + 1)

                            results.append(obj)
                    
                    url = data.get("@odata.nextLink", None) # follow paging if present
                    if "@odata.nextLink" in data:
                        print(f"Following paging link: {url}")

                return results

            return walk(f"https://graph.microsoft.com/v1.0/me/drive/root/children?$top={page_limit}")

        return JsonResponse(get_onedrive_tree(access_token, page_limit=999), safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)