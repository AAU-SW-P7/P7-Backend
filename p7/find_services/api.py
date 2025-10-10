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

find_services_router = Router()

@find_services_router.get("/")
def find_services(request, x_internal_auth: str = Header(..., alias="x-internal-auth"), userId: str = None):
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp
    
    if not userId:
        return JsonResponse({"error": "userId required"}, status=400)

    try:
        qs = Service.objects.filter(userId_id=userId)
    except Service.DoesNotExist:
        return JsonResponse({"error": "Service not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve service", "detail": str(e)}, status=500)

    def _serialize(service: Service):
        return {
            "id": service.id,
            "userId": service.userId.id,
            "oauthType": service.oauthType,
            "oauthToken": service.oauthToken,
            "accessToken": service.accessToken,
            "accessTokenExpiration": int(service.accessTokenExpiration.timestamp()),
            "refreshToken": service.refreshToken,
            "name": service.name,
            "accountId": service.accountId,
            "email": service.email,
            "scopeName": service.scopeName,
        }

    return [_serialize(s) for s in qs]