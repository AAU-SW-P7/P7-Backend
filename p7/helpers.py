"""Helper functions for internal API calls and validation."""
import os
import requests
from django.http import JsonResponse

def validate_internal_auth(x_internal_auth: str) -> JsonResponse | None:
    """
    Validate the internal auth header value. Returns JsonResponse on failure, otherwise None.

    params:
        x_internal_auth (str): The value of the x-internal-auth header to validate.
    """
    if x_internal_auth != os.getenv("INTERNAL_API_KEY"):
        return JsonResponse({"error": "Unauthorized - invalid x-internal-auth"}, status=401)
    return None

def fetch_api(url, headers, data):
    """
    Fetches a url with provided headers and data. Contains generic error handling

    params:
        url (str): The URL to fetch.
        headers (dict): The headers to include in the request.
        data (dict): The JSON body to include in the request.
    """
    response = requests.post(url, headers=headers, json=data, timeout=10)
    if not response.ok:
        return JsonResponse(
            {"error": "Failed to fetch files", "details": response.json()},
            status=response.status_code
        )
    return response
