"""Repository functions for handling File model operations."""
import logging
from datetime import datetime
from django.db import transaction
from django.db.models import Value, Q #, F # enable F when re-enabling modifiedAt__gt=F("indexedAt")
from django.contrib.postgres.search import SearchVector
from django.http import JsonResponse
from repository.models import File, Service, User
from p7.helpers import downloadable_file_extensions, smart_extension

def fetch_downloadable_files(service):
    """Fetches all downloadable files for a given service.

    params:
        service: The service object for which to fetch downloadable files.
    returns:
        A list of downloadable File objects associated with the service.
    """
    if isinstance(service, Service):
        return list(
            File.objects.filter(
                serviceId=service,
                extension__in=downloadable_file_extensions(),
                downloadable=True,
                # modifiedAt__gt=F("indexedAt"), # re-enable when debugging/coding is done
            )
        )

    return JsonResponse({"error": "Invalid service parameter"}, status=400)

def save_file(
    service_id,  # may be an int (Service.pk) or a Service instance
    service_file_id,
    name,
    extension,
    downloadable,
    path,
    link,
    size,
    created_at,
    modified_at,
    indexed_at,
    snippet,
):
    """Saves or updates file metadata and content to the database.

    params:
        service_id: ID of the service the file belongs to.
        serviceFileId: ID of the file in the external service.
        name: Name of the file.
        extension: File extension.
        downloadable: Boolean indicating if the file is downloadable.
        path: Path of the file in the service.
        link: URL link to the file.
        size: Size of the file in bytes.
        createdAt: Timestamp when the file was created.
        modifiedAt: Timestamp when the file was last modified.
        indexedAt: Timestamp when the file was last indexed.
        snippet: Text snippet or preview of the file content.
        """

    with transaction.atomic():
        # Insert the file
        defaults = {
            "name": name,
            "extension": extension,
            "downloadable": downloadable,
            "path": path,
            "link": link,
            "size": size,
            "createdAt": created_at,
            "modifiedAt": modified_at,
            "indexedAt": indexed_at,
            "snippet": snippet,
        }
        file, _ = File.objects.update_or_create(
            serviceId=service_id,
            serviceFileId=service_file_id,
            defaults=defaults,
        )

        update_tsvector(
            file,
            None,
            indexed_at
        )

    return file

def remove_extension_from_ts_vector_smart(file: File) -> str:
    """Removes the file extension from the file name for tsvector indexing.

    params:
        file: File instance whose name is to be processed.
    returns:
        The file name without its extension.
    """
    extension = smart_extension(file.serviceId.name, file.name)
    if extension and file.name.lower().endswith(extension.lower()):
        return file.name[: -len(extension)]
    return file.name

def update_tsvector(file, content: str | None, indexed_at: datetime | None) -> None:
    """Update the tsvector field for full-text search on the given file instance."""

    File.objects.filter(pk=file.pk).update(
        indexedAt=indexed_at,
        tsFilename=(
            SearchVector(Value(
                remove_extension_from_ts_vector_smart(file)
            ), weight="A", config='simple')
        ),
        tsContent=(
            SearchVector(Value(
                content or ""
            ), weight="B", config='english')
        ),
    )

    file.refresh_from_db(fields=["tsFilename", "tsContent"])

def query_files_by_name(
    name_query,
    user_id,
    provider=None,
    modified_after_date=None,
    modified_before_date=None,
    extension=None,
):
    """Query for files by name containing any of the given tokens and user id.

    params:
        name_query: List or tuple of substrings to search for in file names.
        user_id: User id to restrict results to. (applies as an AND).
    returns:
        QuerySet of File objects matching the search criteria.
    """
    try:
        User.objects.get(pk=user_id)  # Ensure user exists
    except User.DoesNotExist:
        return JsonResponse(
            {"error": f"Service ({user_id}) not found for user"}, status=404
        )

    assert isinstance(
        name_query, (list, tuple)
    ), "name_query must be a list or tuple of tokens"

    # Q() object to combine queries
    q = Q()
    if provider:
        for p in provider:
            q &= Q(serviceId__name__iexact=p)
    if modified_after_date:
        q &= Q(modifiedAt__gte=modified_after_date)
    if modified_before_date:
        q &= Q(modifiedAt__lte=modified_before_date)
    if extension:
        for ext in extension:
            q &= Q(extension__iexact=ext)
    # Always filter by user_id
    q &= Q(serviceId__userId=user_id)

    query_text = " ".join(name_query)
    results = File.objects.ranking_based_on_file_name(query_text, base_filter=q)
    return results


def get_files_by_service(service):
    """Retrieves all files associated with a given service.

    params:
        service: The service object for which to retrieve files.

    returns:
        A list of File objects associated with the service.
    """
    if isinstance(service, Service):
        return list(File.objects.filter(serviceId=service.id))
    return JsonResponse({"error": "Invalid service parameter"}, status=400)
