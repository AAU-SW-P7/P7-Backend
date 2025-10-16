"""API endpoint for finding a user by email."""

from ninja import Router, Header
from django.http import JsonResponse
from repository.service import get_user_service_related_to_email
from p7.helpers import validate_internal_auth

find_user_by_email_router = Router()


@find_user_by_email_router.get("/")
def find_user_by_email(
    request, email: str, x_internal_auth: str = Header(..., alias="x-internal-auth")
):
    """Find a user by their email address.
    params:
        email (str): The email address of the user to find.
        x_internal_auth (str): The internal auth header for validating the request.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    if not email:
        return JsonResponse({"error": "email required"}, status=400)

    service = get_user_service_related_to_email(email)

    if not service:
        return JsonResponse({"error": "User not found"}, status=404)

    return {
        "id": service.userId_id,
        "email": service.email,
    }
