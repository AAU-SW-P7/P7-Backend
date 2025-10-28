"""API endpoint to search files by filename."""
import re
from ninja import Router, Header
from django.http import JsonResponse
from p7.helpers import validate_internal_auth
from repository.file import query_files_by_name
from repository.user import get_user
from repository.service import get_service_name

search_files_by_filename_router = Router()
def sanitize_user_search(text: str) -> str:
    """
    Sanitizes the user input by removing potentially harmful content and normalizing the text.
    Args:
        text (str): The user input string to be sanitized.
    Returns:
        str: The sanitized string.
    """
    # 1. Lowercase everything
    text = text.lower()

    # 2. Remove all punctution except for ' and - and _
    text = re.sub(r"[^\w\s'\-_]", "", text)

    # 3. Replace the '-_' with space
    text = re.sub(r"[\-_]", " ", text)

    # 4. Collapse extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text

def tokenize(input_str: str) -> list[str]:
    """
    Tokenizes the input string.
    Args:
        input_str (str): The input string to be tokenized.
    Returns:
        list[str]: A list of processed tokens.
    """
    return list(input_str.split())

@search_files_by_filename_router.get("/")
def search_files_by_filename(
    request,
    user_id: str,
    search_string: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Search files in the database by filename.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        filename (str): The filename or substring to search for.
    """

    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    if not search_string:
        return JsonResponse({"error": "search_string required"}, status=400)

    sanitized_input = sanitize_user_search(search_string)
    tokens = tokenize(sanitized_input)
    results = query_files_by_name(tokens, user_id)


    # Cache service lookups to avoid repeated DB calls
    service_name_cache: dict = {}

    files_data = []

    for file in results:
        #Extract id as file.serviceId is a service object
        service_ref = file.serviceId
        service_id = getattr(service_ref, "id", service_ref)

        if service_id not in service_name_cache:
            service_name = get_service_name(user_id, service_id)
            # get_service_name may return a JsonResponse on error — handle that safely
            if isinstance(service_name, JsonResponse):
                service_name_cache[service_id] = None
            else:
                service_name_cache[service_id] = service_name

        files_data.append(
            {
                "id": file.id,
                "name": file.name,
                "extension": file.extension,
                "path": file.path,
                "link": file.link,
                "size": file.size,
                "createdAt": file.createdAt,
                "modifiedAt": file.modifiedAt,
                "snippet": file.snippet,
                "serviceName": service_name_cache.get(service_id),
            }
        )

    return JsonResponse({"files": files_data}, status=200)
