"""API endpoint to search files by filename."""

import re
import time
from ninja import Router, Header
from django.http import JsonResponse
from repository.file import query_files
from repository.user import get_user
from repository.service import get_service_name
from p7.helpers import validate_internal_auth

search_router = Router()


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

    # 2. Remove all punctution except for - and _
    text = re.sub(r"[^\w\s\-_]", "", text)

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


@search_router.get("/")
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
    start_auth = time.perf_counter()
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    end_auth = time.perf_counter()
    print(f"Internal auth validation took {end_auth - start_auth:.6f} seconds")

    start_user = time.perf_counter()
    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user
    
    end_user = time.perf_counter()
    print(f"User retrieval took {end_user - start_user:.6f} seconds")

    if not search_string:
        return JsonResponse({"error": "search_string required"}, status=400)

    start_sanitized_input = time.perf_counter()
    sanitized_input = sanitize_user_search(search_string)
    end_sanitized_input = time.perf_counter()
    print(f"Sanitizing input took {end_sanitized_input - start_sanitized_input:.6f} seconds")
    
    start_tokens = time.perf_counter()
    tokens = tokenize(sanitized_input)
    end_tokens = time.perf_counter()
    print(f"Tokenizing input took {end_tokens - start_tokens:.6f} seconds")
    
    start_results = time.perf_counter()
    results = query_files(tokens, user_id)
    end_results = time.perf_counter()
    print(f"Querying files took {end_results - start_results:.6f} seconds")
    # Cache service lookups to avoid repeated DB calls
    service_name_cache: dict = {}

    files_data = []

    start_preprocess_files = time.perf_counter()
    for file in results:
        # Extract id as file.serviceId is a service object
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
    end_total = time.perf_counter()
    print(f"Preprocess Took {end_total - start_preprocess_files:.6f} seconds")
    print(f"Total responsetime took {end_total - start_auth:.6f} seconds")
    return JsonResponse({"files": files_data}, status=200)
