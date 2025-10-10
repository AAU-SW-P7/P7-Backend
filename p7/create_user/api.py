from ninja import Router, Body, Header
from repository.user import save_user
from p7.helpers import validate_internal_auth
from typing import Dict

create_user_router = Router()

@create_user_router.post("/")
def create_user(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), payload: Dict[str, str] = Body(...)):
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    user = save_user()
    return {
        "id": user.id,
    }   