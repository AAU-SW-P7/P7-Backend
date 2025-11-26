from asyncio import sleep
from ninja import Router, Header
from django.http import JsonResponse
from django_q.tasks import async_task
from p7.helpers import validate_internal_auth
from repository.service import get_service
from repository.user import get_user
from p7.get_local_files.helper import fetch_recursive_local_files
from p7.download_local_files.api import process_download_local_files
from p7.get_local_files.helper import update_or_create_local_file

fetch_local_files_router = Router()


@fetch_local_files_router.get("/")
def fetch_local_files(
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
        process_local_files,
        user_id,
        cluster="high",
        group=f"Local-{user_id}"
    )

    return JsonResponse({"task_id": task_id, "status": "processing"}, status=202)


def process_local_files(user_id):
    """Read metadata + create/update DB rows."""
    try:
        files = fetch_recursive_local_files(user_id)
        service = get_service(user_id, "google")
        batch = []
        for _, file in enumerate(files, start=1):
            if file[".tag"] == "file":
                batch.append(file)

            if len(batch) >= 500:
                for file in batch:
                    update_or_create_local_file(file, service)
                batch = []
                print("Processed 500 files, sleeping for 60 seconds to avoid overload...")
                sleep(60)

        # save remaining
        if batch:
            for file in batch:
                update_or_create_local_file(file, service)

        async_task(
            process_download_local_files,
            user_id,
            cluster="high",
            group=f"Local-{user_id}"
        )

        return files

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
