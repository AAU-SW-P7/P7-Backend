from ninja import Router
from django.http import JsonResponse



router = Router()


@router.get('/')
def hello(request):
    return JsonResponse({"message": "Hello from Django!"})