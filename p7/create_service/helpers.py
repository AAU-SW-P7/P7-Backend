"""Helper functions for create_service module."""
from django.db import IntegrityError
from django_q.tasks import async_task, schedule
from p7.get_google_drive_files.api import process_google_drive_files
from p7.get_dropbox_files.api import process_dropbox_files
from p7.get_onedrive_files.api import process_onedrive_files


def schedule_fetching_files(cleaned):
    """Schedule fetching files for the created service based on its name.

    params:
        cleaned (dict): The cleaned and validated payload containing service details.
    """
    match cleaned["name"]:
        case "google":
            try:
                group = f"Google-Drive-{cleaned['userId']}"
                # Could trigger Google Drive file fetch here if desired
                async_task(
                    process_google_drive_files,
                    cleaned["userId"],
                    cluster="high",
                    group=group,
                )
                # Schedule daily sync of Google Drive files
                # Pass the callable as a dotted path string and args as a list so django-q
                # worker can import and resolve the function at runtime.
                schedule(
                    func="p7.sync_files.service_sync_functions.sync_google_drive_files",
                    schedule_type="D",
                    name=group,
                    user_id=cleaned["userId"],
                    priority="low",
                    cluster="low",
                )
            except IntegrityError as e:
                print(f"Error scheduling Google Drive tasks: {e}")
        case "dropbox":
            try:
                group = f"Dropbox-{cleaned['userId']}"
                # Could trigger Dropbox file fetch here if desired
                async_task(process_dropbox_files, cleaned["userId"], cluster="high", group=group)
                # Schedule daily sync of Dropbox files
                schedule(
                    func="p7.sync_files.service_sync_functions.sync_dropbox_files",
                    schedule_type="D",
                    name=group,
                    user_id=cleaned["userId"],
                    priority="low",
                    cluster="low",
                )
            except IntegrityError as e:
                print(f"Error scheduling Dropbox tasks: {e}")
        case "onedrive":
            try:
                group = f"Onedrive-{cleaned['userId']}"
                # Could trigger OneDrive file fetch here if desired
                async_task(process_onedrive_files, cleaned["userId"], cluster="high", group=group)
                # Schedule daily sync of OneDrive files
                schedule(
                    func="p7.sync_files.service_sync_functions.sync_onedrive_files",
                    schedule_type="D",
                    name=group,
                    user_id=cleaned["userId"],
                    priority="low",
                    cluster="low",
                )
            except IntegrityError as e:
                print(f"Error scheduling OneDrive tasks: {e}")
        case _:
            raise NotImplementedError(f"Service fetch not implemented for {cleaned['name']}")
