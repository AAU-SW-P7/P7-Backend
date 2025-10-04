import os
from datetime import datetime
from typing import Dict, Any

from ninja import Router, Body
from django.http import JsonResponse
from django.db import IntegrityError
from repository.models import User, Service

create_user_router = Router()
find_user_by_email_router = Router()
create_service_router = Router()
find_services_router = Router()

def _require_internal_auth(request):
    """
    Enforce presence of 'x-internal-auth' header for internal endpoints.
    Returns a JsonResponse (401) when missing, otherwise None.
    """
    if not request.headers.get("x-internal-auth") or request.headers.get("x-internal-auth") != os.getenv("INTERNAL_API_KEY"):
        return JsonResponse({"error": "Unauthorized - missing x-internal-auth header"}, status=401)
    return None

@create_user_router.post("/")
def create_user(request, payload: Dict[str, str] = Body(...)):
    auth_resp = _require_internal_auth(request)
    if auth_resp:
        return auth_resp

    username = payload.get("username")
    primary_provider = payload.get("primaryProvider")

    # if not all([username, primary_provider]):
    #     return JsonResponse({"error": "username and primaryProvider required"}, status=400)

    try:
        user = User.objects.create(
            # username=None,
            primaryProvider=primary_provider
        )
    except IntegrityError as e:
        return JsonResponse({"error": "Failed to create user", "detail": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": "Failed to create user", "detail": str(e)}, status=500)

    return {
        "id": user.id,
        # "username": user.username,
        # "primary_provider": user.primary_provider_id,
    }

@find_user_by_email_router.get("/")
def find_user_by_email(request, email: str):
    auth_resp = _require_internal_auth(request)
    if auth_resp:
        return auth_resp
    
    if not email:
        return JsonResponse({"error": "email required"}, status=400)

    try:
        service = Service.objects.filter(email=email).first()
    except Exception as e:
        return JsonResponse({"error": "Failed to retrieve user", "detail": str(e)}, status=500)

    if not service:
        return JsonResponse({"error": "User not found"}, status=404)

    return {
        "id": service.userId_id,
        "email": service.email,
        # "primaryProvider": service.userId.primaryProvider if needed,
    }

@create_service_router.post("/")
def create_service(request, payload: Dict[str, Any] = Body(...)):
    auth_resp = _require_internal_auth(request)
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

@find_services_router.get("/")
def find_services(request, userId: str = None):
    auth_resp = _require_internal_auth(request)
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

# Security risk with passing userid directly, should be fixed with session.
def get_tokens(user_id, service_name):
    """
    Fetches refresh and access token from database
    """
    try:
        service = Service.objects.get(userid=user_id, name=service_name)
        access_token = service.accessToken
        refresh_token = service.refreshToken
    except Service.DoesNotExist:
        return JsonResponse({"error": "No account tokens found for user"}, status=404)
    
    return access_token, refresh_token