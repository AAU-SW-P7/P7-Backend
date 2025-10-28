"""API endpoint for creating a new service associated with a user."""

from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from ninja import Router, Body, Header
from django.http import JsonResponse
from repository.service import save_service
from repository.user import get_user
from p7.helpers import validate_internal_auth

create_service_router = Router()

@create_service_router.post("/")
def create_service(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    payload: Dict[str, Any] = Body(...),
):
    """
    Create a new service for a user.
    params:
        x_internal_auth (str): The internal auth header for validating the request.
        payload (dict): The service details including userId, oauthType, oauthToken
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    #Clean request params
    cleaned, error = _parse_and_validate_payload(payload)
    if error:
        return error

    # Save service and link to user
    user = get_user(cleaned["userId"])
    service = save_service(
        user,
        cleaned["oauthType"],
        cleaned["oauthToken"],
        cleaned["accessToken"],
        cleaned["accessTokenExpiration"],
        cleaned["refreshToken"],
        cleaned["name"],
        cleaned["accountId"],
        cleaned["email"],
        cleaned["scopeName"],
        datetime.now(timezone.utc),
    )

    # save_service returns either a Service or JsonResponse on error
    if isinstance(service, JsonResponse):
        return service

    return {"id": service.id, "name": service.name}


def _parse_and_validate_payload(
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], JsonResponse | None]:
    """
    Extract required fields from payload and validate them.
    Returns a tuple:(cleaned_payload, error_response). If validation passed, error_response is None.
    """
    fields = [
        "userId",
        "oauthType",
        "oauthToken",
        "accessToken",
        "accessTokenExpiration",
        "refreshToken",
        "name",
        "accountId",
        "email",
        "scopeName",
    ]

    cleaned: Dict[str, Any] = {k: payload.get(k) for k in fields}

    # Basic presence check
    if not all(cleaned.values()):
        return {}, JsonResponse({"error": "All fields are required"}, status=400)

    # Normalize timestamp -> datetime
    exp = cleaned["accessTokenExpiration"]
    if isinstance(exp, int):
        cleaned["accessTokenExpiration"] = datetime.fromtimestamp(exp)

    return cleaned, None
