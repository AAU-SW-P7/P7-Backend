from ninja import Router, Header
from django.http import JsonResponse
from django_q.tasks import async_task
from p7.helpers import validate_internal_auth
from repository.service import get_service
from repository.user import get_user
from p7.get_local_files.helper import fetch_recursive_local_files
from p7.download_local_files.helper import download_recursive_local_files

download_local_files_router = Router()


@download_local_files_router.get("/")
def download_local_files(
    request,
    user_id: str,
    x_internal_auth: str = Header(..., alias="x-internal-auth"),
):
    auth_resp = validate_internal_auth(x_internal_auth)
    if auth_resp:
        return auth_resp

    user = get_user(user_id)
    if isinstance(user, JsonResponse):
        return user

    task_id = async_task(
        process_download_local_files,
        user_id,
        cluster="high",
        group=f"Local-{user_id}"
    )

    return JsonResponse({"task_id": task_id, "status": "processing"}, status=202)


def process_download_local_files(user_id):
    """Read file content + update tsvector."""
    try:
        service = get_service(user_id, "google")
        processed, errors = download_recursive_local_files(service)

        return {
            "files": processed,
            "errors": errors
        }

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
