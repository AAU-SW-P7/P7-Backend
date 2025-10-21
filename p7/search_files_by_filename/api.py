import re 
from p7.helpers import validate_internal_auth
from repository.file import search_files_by_name

from ninja import Router, Header
from django.http import JsonResponse

fetch_database_files_by_filename_router = Router()



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
    return [token for token in input_str.split()]


@fetch_database_files_by_filename_router.get("/")
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

    if not search_string:
        return JsonResponse({"error": "search_string required"}, status=400)

    sanitized_input = sanitize_user_search(search_string)
    tokens = tokenize(sanitized_input)
    results = search_files_by_name(tokens, user_id)

    files_data = [
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
        }
        for file in results
    ]

    return JsonResponse({"files": files_data}, status=200)