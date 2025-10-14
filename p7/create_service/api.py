"""API endpoint for creating a new service associated with a user."""
from datetime import datetime
from typing import Dict, Any
from ninja import Router, Body, Header
from django.http import JsonResponse
from django.db import IntegrityError
from repository.models import User, Service
from p7.helpers import validate_internal_auth

create_service_router = Router()

@create_service_router.post("/")
def create_service(
    request,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
    payload: Dict[str, Any] = Body(...)
    ):
    """Create a new service for a user.
    params:
        x_internal_auth (str): The internal auth header for validating the request.
        payload (dict): The service details including userId, oauthType, oauthToken, access"""
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user_id = payload.get("userId")
    oauth_type = payload.get("oauthType")
    oauth_token = payload.get("oauthToken")
    access_token = payload.get("accessToken")
    access_token_expiration = payload.get("accessTokenExpiration")
    refresh_token = payload.get("refreshToken")
    name = payload.get("name")
    account_id = payload.get("accountId")
    email = payload.get("email")
    scope_name = payload.get("scopeName")

    if not all([user_id,
                oauth_type,
                oauth_token,
                access_token,
                access_token_expiration,
                refresh_token,
                name,
                account_id,
                email,
                scope_name
                ]):
        return JsonResponse({"error": "All fields are required"}, status=400)

    if isinstance(access_token_expiration, int):
        access_token_expiration = datetime.fromtimestamp(access_token_expiration)

    try:
        # ensure we pass a User instance (ForeignKey expects model instance)
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except RuntimeError as e:
        return JsonResponse({"error": "Failed to retrieve user", "detail": str(e)}, status=500)

    try:
        service = Service.objects.create(
            userId=user,
            oauthType=oauth_type,
            oauthToken=oauth_token,
            accessToken=access_token,
            accessTokenExpiration=access_token_expiration,
            refreshToken=refresh_token,
            name=name,
            accountId=account_id,
            email=email,
            scopeName=scope_name,
        )
    except IntegrityError as e:
        return JsonResponse({"error": "Failed to create service", "detail": str(e)}, status=400)
    except RuntimeError as e:
        return JsonResponse({"error": "Failed to create service", "detail": str(e)}, status=500)

    return {
        "id": service.id,
        # "userId": service.userId,
        # "oauthType": service.oauthType,
        "name": service.name,
        # "accountId": service.accountId,
        # "scopeName": service.scopeName,
    }
