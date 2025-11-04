"""Helper functions for internal API calls and validation."""
import os
import mimetypes
from pathlib import Path
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

def smart_extension(provider: str, name: str, mime: str | None = None) -> str:
    """
    Determine the file extension based on provider, filename, and MIME type.
    """
    # known compression endings
    compressed_file_extensions = {'.gz', '.bz2', '.xz', '.zst', '.lz', '.lzma', '.br'}
     # known single extensions
    known_file_extensions = set(mimetypes.types_map) | compressed_file_extensions

    google_file_extensions = {}
    if provider == "google":
        google_file_extensions = {
            'application/vnd.google-apps.document': '.gdoc',
            'application/vnd.google-apps.spreadsheet': '.gsheet',
            'application/vnd.google-apps.presentation': '.gslides',
            'application/vnd.google-apps.drawing': '.gdraw',
            'application/vnd.google-apps.form': '.gform',
            'application/vnd.google-apps.fusiontable': '.gtable',
            'application/vnd.google-apps.map': '.gmap',
            'application/vnd.google-apps.script': '.gscript',
            'application/vnd.google-apps.site': '.gsite',
            'application/vnd.google-apps.jam': '.gjam',
        }

    path = Path(name)
    suffixes = [suffix.lower() for suffix in path.suffixes]

    # dotfile like ".gitignore" -> no extension
    if name.startswith(".") and len(suffixes) == 1 and not name.startswith(".."):
        return ""

    # keep only suffixes we recognize
    recognized = [suffix for suffix in suffixes if suffix in known_file_extensions]

    if recognized:
        # preserve compression combos like ".tar.gz"
        if len(recognized) >= 2 and recognized[-1] in compressed_file_extensions:
            return "".join(recognized[-2:])
        return recognized[-1]

    # fallback to MIME type
    if mime:
        ext = mimetypes.guess_extension(mime)  # None for Google Docs
        if ext:
            return ext.lower()
        return google_file_extensions.get(mime, "") if provider == "google" else ""

    return ""

def downloadable_file_extensions() -> set[str]:
    """Return a set of file extensions considered downloadable."""
    return {
        '.gdoc',
        '.gsheet',
        '.gslides',
        '.gdraw',
        '.gform',
        '.gtable',
        '.gmap',
        '.gscript',
        '.gsite',
        '.gjam',
        
        '.txt',
        '.hs',
        # '.pdf', # add libaries to do this
        # '.doc',
        # '.docx',
        # '.xls',
        # '.xlsx',
        # '.ppt',
        # '.pptx',
    }