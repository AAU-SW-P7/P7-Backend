from datetime import datetime
from typing import Dict, Any
from p7.helpers import validate_internal_auth

# Helper: compute the folder path pieces for a given folder id (memoized)
from functools import lru_cache

from ninja import Router, Body, Header
from django.http import JsonResponse
from django.db import IntegrityError
from repository.models import User, Service
from repository.user import save_user

create_service_router = Router()

@create_service_router.post("/")
def create_service(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), payload: Dict[str, Any] = Body(...)):
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    userId = payload.get("userId")
    oauthType = payload.get("oauthType")
    oauthToken = payload.get("oauthToken")
    accessToken = payload.get("accessToken")
    accessTokenExpiration = payload.get("accessTokenExpiration")
    refreshToken = payload.get("refreshToken")
    name = payload.get("name")
    accountId = payload.get("accountId")
    email = payload.get("email")
    scopeName = payload.get("scopeName")

    if not all([userId, oauthType, oauthToken, accessToken, accessTokenExpiration, refreshToken, name, accountId, email, scopeName]):
        return JsonResponse({"error": "All fields are required"}, status=400)
    
    if isinstance(accessTokenExpiration, int):
        accessTokenExpiration = datetime.fromtimestamp(accessTokenExpiration)

    try:
        # ensure we pass a User instance (ForeignKey expects model instance)
        user = User.objects.get(pk=userId)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve user", "detail": str(e)}, status=500)

    try:
        service = Service.objects.create(
            userId=user,
            oauthType=oauthType,
            oauthToken=oauthToken,
            accessToken=accessToken,
            accessTokenExpiration=accessTokenExpiration,
            refreshToken=refreshToken,
            name=name,
            accountId=accountId,
            email=email,
            scopeName=scopeName,
        )
    except IntegrityError as e:
        return JsonResponse({"error": "Failed to create service", "detail": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "Failed to create service", "detail": str(e)}, status=500)

    return {
        "id": service.id,
        # "userId": service.userId,
        # "oauthType": service.oauthType,
        "name": service.name,
        # "accountId": service.accountId,
        # "scopeName": service.scopeName,
    }