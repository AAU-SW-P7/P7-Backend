"""
Repository helpers for user persistence.

This module provides functions to create and persist User records.
"""


from typing import Union

from django.db import IntegrityError
from django.http import JsonResponse

from repository.models import User


def get_user(user_id: int) -> Union[User, JsonResponse]:
    """
    Gets a user from the database
    """
    try:
        # ensure we pass a User instance (ForeignKey expects model instance)
        user = User.objects.get(pk=user_id)
        return user
    except (ValueError, TypeError) as e:
        return JsonResponse({"error": "Invalid user id", "detail": str(e)}, status=400)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except RuntimeError as e:
        return JsonResponse(
            {"error": "Failed to retrieve user", "detail": str(e)}, status=500
        )
        
def save_user() -> Union[User, JsonResponse]:
    """Create and persist a new User.

    Returns the created ``User`` instance on success. On failure returns a
    ``JsonResponse`` containing an error message and appropriate HTTP status
    code.

    The function avoids catching overly-broad exceptions; unexpected errors
    will propagate so callers (or middleware) can handle them. Only
    ``IntegrityError`` is handled explicitly here.
    """
    try:
        user = User.objects.create()
        user.generate_salt()
        user.save()
        return user
    except IntegrityError as exc:
        return JsonResponse(
            {"error": "Failed to create user", "detail": str(exc)}, status=400
        )
    # Let unexpected exceptions propagate; callers or middleware should
    # translate them into HTTP responses where appropriate.

def delete_user(user_id: int) -> Union[User, JsonResponse]:
    """
    Deletes a user from the database
    """
    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

    try:
        user = User.objects.get(pk=user_id)
        user.delete()
        return {"status": 200}
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except RuntimeError as e:
        return JsonResponse(
            {"error": "Failed to delete user", "detail": str(e)}, status=500
        )
