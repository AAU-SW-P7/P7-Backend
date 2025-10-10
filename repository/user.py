from repository.models import User
from django.http import JsonResponse
from django.db import IntegrityError


def save_user():
    try:
        user = User.objects.create()
        return user
    except IntegrityError as e:
        return JsonResponse(
            {"error": "Failed to create user", "detail": str(e)}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Failed to create user", "detail": str(e)}, status=500
        )
