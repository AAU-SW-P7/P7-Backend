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

find_user_by_email_router = Router()

@find_user_by_email_router.get("/")
def find_user_by_email(request, email: str, x_internal_auth: str = Header(..., alias="x-internal-auth")):
    auth_resp = validate_internal_auth(x_internal_auth)
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