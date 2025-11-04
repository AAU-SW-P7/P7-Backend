from django_q.models import Schedule

def delete_user_schedules(user_id: int) -> None:
    """
    Deletes all scheduled tasks for a user across all clusters.
    """
    Schedule.objects.filter(
        name__icontains=f"-{user_id}",
    ).delete()