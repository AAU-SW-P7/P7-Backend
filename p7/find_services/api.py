"""API endpoint for finding services by user ID."""
from ninja import Router, Header
from django.http import JsonResponse
from repository.models import Service
from p7.helpers import validate_internal_auth

find_services_router = Router()

@find_services_router.get("/")
def find_services(request,
                  x_internal_auth: str = Header(..., alias="x-internal-auth"),
                  user_id: str = None):
    """Find services associated with a user ID.

    params:
        x_internal_auth (str): The internal auth header for validating the request.
        user_id (str): The ID of the user whose services are to be retrieved.
    """
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    if not user_id:
        return JsonResponse({"error": "user_id required"}, status=400)

    try:
        qs = Service.objects.filter(userId_id=user_id)
    except Service.DoesNotExist:
        return JsonResponse({"error": "Service not found"}, status=404)
    except (ValueError, TypeError, RuntimeError) as e:
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
