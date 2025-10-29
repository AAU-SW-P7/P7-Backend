"""API endpoint for deleting a user."""
from ninja import Router, Header
from django.http import JsonResponse
from repository.user import get_user, delete_user
from p7.helpers import validate_internal_auth

delete_user_router = Router()

@delete_user_router.post("/")
def delete_user_endpoint(
    request,
    user_id: int,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    """Delete a user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    return delete_user(user_id)
