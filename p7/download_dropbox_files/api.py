"""API endpoint to download Dropbox files for a user."""

from ninja import Router, Header
from django.http import JsonResponse
from p7.helpers import validate_internal_auth
from p7.get_dropbox_files.helper import (
    update_or_create_file, fetch_recursive_files, get_new_access_token
)
from repository.service import get_tokens, get_service
from repository.user import get_user

download_dropbox_files_router = Router()
@download_dropbox_files_router.get("/")
def download_dropbox_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Fetch and save Dropbox files for a given user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose Dropbox files are to be fetched.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    access_token, access_token_expiration, refresh_token = get_tokens(user_id, "dropbox")
    service = get_service(user_id, "dropbox")

    try:
        access_token, access_token_expiration = get_new_access_token(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )
        
        files = download_recursive_files(
            service,
            access_token,
            access_token_expiration,
            refresh_token,
        )
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

def download_recursive_files(
    service,
    access_token,
    access_token_expiration,
    refresh_token,
):
    """Download files recursively from a user's Dropbox account."""
    
    
    