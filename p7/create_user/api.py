"""API endpoint for creating a new user."""
from ninja import Router, Header
from repository.user import save_user
from p7.helpers import validate_internal_auth

create_user_router = Router()

@create_user_router.post("/")
def create_user(request, x_internal_auth: str = Header(..., alias="x-internal-auth")):
    """Create a new user and return its ID.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    user = save_user()
    return {
        "id": user.id,
    }
