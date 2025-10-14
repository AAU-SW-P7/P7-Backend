"""
Repository helpers for user persistence.

This module provides functions to create and persist User records.
"""

from typing import Union

from django.db import IntegrityError
from django.http import JsonResponse

from repository.models import User


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
        return user
    except IntegrityError as exc:
        return JsonResponse(
            {"error": "Failed to create user", "detail": str(exc)}, status=400
        )
    # Let unexpected exceptions propagate; callers or middleware should
    # translate them into HTTP responses where appropriate.
