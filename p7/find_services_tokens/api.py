"""API endpoint for finding services by user ID."""

from typing import Any

from ninja import Router, Header
from django.http import JsonResponse
from repository.service import get_all_user_services, serialize_service
from repository.user import get_user
from p7.helpers import validate_internal_auth

find_services_tokens_router = Router()


@find_services_tokens_router.get("/")
def find_services(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
) -> JsonResponse | list[dict[str, Any]]:
    """
    Debugging API endpoint to show rows in the service table unencrypted.
    Find services associated with a user ID.

    Returns a JsonResponse on error, otherwise a list of serialized service dicts.
    """
    # Validate internal auth header
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    qs = get_all_user_services(user_id)
    # get_all_user_services can return a JsonResponse on error
    if isinstance(qs, JsonResponse):
        return qs

    serialized_services = []
    for s in qs:
        ser = serialize_service(s)
        serialized_services.append(
            {
                "id": ser.get("id"),
                "oauthType": ser.get("oauthType"),
                "oauthToken": ser.get("oauthToken"),
                "accessToken": ser.get("accessToken"),
                "accessTokenExpiration": ser.get("accessTokenExpiration"),
                "refreshToken": ser.get("refreshToken"),
                "userId": ser.get("userId"),
                "name": ser.get("name"),
                "email": ser.get("email"),
            }
        )

    return serialized_services
