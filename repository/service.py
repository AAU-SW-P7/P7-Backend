"""Finds both tokens and service object for a user and service name."""

from django.http import JsonResponse
from django.db import IntegrityError
from repository.models import Service


# Security risk with passing userid directly, should be fixed with session.
def get_tokens(user_id, service_name):
    """
    Fetches refresh and access token from database.
    Raises Service.DoesNotExist if service not found.
    """
    service = Service.objects.get(userId=user_id, name=service_name)
    return service.accessToken, service.accessTokenExpiration, service.refreshToken


def get_service(user_id, service_name) -> Service:
    """
    Fetches the entire service object based on user and service name
    """
    try:
        service = Service.objects.get(userId_id=user_id, name=service_name)
        return service
    except Service.DoesNotExist:
        return JsonResponse(
            {"error": f"Service ({service_name}) not found for user"}, status=404
        )
    except Service.MultipleObjectsReturned as e:
        return JsonResponse(
            {"error": f"Failed to retrieve service ({service_name})", "detail": str(e)},
            status=500,
        )


def save_service(
    user_id,
    oauth_type,
    oauth_token,
    access_token,
    access_token_expiration,
    refresh_token,
    name,
    account_id,
    email,
    scope_name,
) -> Service:
    """
    Saves or updates sevice data in the database
    """
    try:
        service, _ = Service.objects.update_or_create(
            userId=user_id,
            name=name,
            defaults={
                "oauthType": oauth_type,
                "oauthToken": oauth_token,
                "accessToken": access_token,
                "accessTokenExpiration": access_token_expiration,
                "refreshToken": refresh_token,
                "accountId": account_id,
                "email": email,
                "scopeName": scope_name,
            }
        )
        return service
    except IntegrityError as e:
        return JsonResponse(
            {"error": "Failed to create service", "detail": str(e)}, status=400
        )
    except RuntimeError as e:
        return JsonResponse(
            {"error": "Failed to create service", "detail": str(e)}, status=500
        )
