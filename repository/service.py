from repository.models import User, Service
from django.http import JsonResponse

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