from django.http import JsonResponse
from repository.models import Service

# Security risk with passing userid directly, should be fixed with session.
def get_tokens(user_id, service_name):
    """
    Fetches refresh and access token from database
    """
    try:
        service = Service.objects.get(userId=user_id, name=service_name)
    except Service.DoesNotExist:
        return JsonResponse({"error": "No account tokens found for user"}, status=404)
    
    return service.accessToken, service.refreshToken

def get_service(user_id, service_name) -> Service:
    """
    Fetches the entire service object based on user and service name
    """
    try:
        service = Service.objects.get(userId_id=user_id, name=service_name)
        return service
    except Service.DoesNotExist:
        return JsonResponse({"error": f"Service ({service_name}) not found for user"}, status=404)
    except Exception as e:
        return JsonResponse({"error": f"Failed to retrieve service ({service_name})", "detail": str(e)}, status=500)