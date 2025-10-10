import requests
import os

from typing import Any
from django.http import JsonResponse

def validate_internal_auth(x_internal_auth: str) -> Any:
    """
    Validate the internal auth header value. Returns JsonResponse on failure, otherwise None.
    """
    if x_internal_auth != os.getenv("INTERNAL_API_KEY"):
        return JsonResponse({"error": "Unauthorized - invalid x-internal-auth"}, status=401)
    return None

def fetch_api(url, headers, data):
    """
    Fetches a url with provided headers and data. Contains generic error handling
    """
    response = requests.post(url, headers=headers, json=data)
    if not response.ok:
            return JsonResponse({"error": "Failed to fetch files", "details": response.json()}, status=response.status_code)
    return response