"""API endpoint for deleting a user."""
from ninja import Router, Header

from repository.models import User
from repository.user import delete_user
from p7.helpers import validate_internal_auth

delete_user_router = Router()

@delete_user_router.post("/")
def delete_user_endpoint(request, user_id: int, x_internal_auth: str = Header(..., alias="x-internal-auth")):
    """Delete a user.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
  
    user = delete_user(user_id)
    return user