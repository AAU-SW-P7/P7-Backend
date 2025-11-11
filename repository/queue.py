"""Repository functions for managing queued tasks."""
from django_q.models import Task


def delete_user_queued_tasks(user_id: int) -> None:
    """
    Deletes all queued tasks for a user across all clusters.
    """
    Task.objects.filter(
        group__icontains=f"-{user_id}",
    ).delete()
