"""API endpoint for finding a user by email."""
from ninja import Router, Header
from django.http import JsonResponse
from repository.models import Service
from p7.helpers import validate_internal_auth

find_user_by_email_router = Router()

@find_user_by_email_router.get("/")
def find_user_by_email(
    request,
    email: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth")
):
    """Find a user by their email address.
    params:
        email (str): The email address of the user to find.
        x_internal_auth (str): The internal auth header for validating the request.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    if not email:
        return JsonResponse({"error": "email required"}, status=400)

    try:
        service = Service.objects.filter(email=email).first()
    except Service.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except (ValueError, TypeError) as e:
        return JsonResponse({"error": "Invalid query parameters", "detail": str(e)}, status=400)
    except RuntimeError as e:  # Replace with a more specific exception type if applicable
        return JsonResponse(
            {"error": "An unexpected runtime error occurred",
             "detail": str(e)}, 
             status=500
            )

    if not service:
        return JsonResponse({"error": "User not found"}, status=404)

    return {
        "id": service.userId_id,
        "email": service.email,
        # "primaryProvider": service.userId.primaryProvider if needed,
    }
