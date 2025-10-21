"""Saves file metadata and content to the database."""

from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.contrib.postgres.search import SearchVector
from repository.models import File

from django.db.models import Q

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
    last_indexed,
    snippet,
    content,
    *,
    ts_config="english"  # allow overriding the FTS config if needed
):
    """Saves file metadata and content to the database.

    params:
        sericeId: ID of the service the file belongs to.
        serviceFileId: ID of the file in the external service.
        name: Name of the file.
        extension: File extension.
        downloadable: Boolean indicating if the file is downloadable.
        path: Path of the file in the service.
        link: URL link to the file.
        size: Size of the file in bytes.
        createdAt: Timestamp when the file was created.
        modifiedAt: Timestamp when the file was last modified.
        lastIndexed: Timestamp when the file was last indexed.
        snippet: Text snippet or preview of the file content.
        content: Full text content of the file.
    """

    with transaction.atomic():
        # Insert the file
        file = File.objects.create(
            serviceId=service_id,
            serviceFileId=service_file_id,
            name=name,
            extension=extension,
            downloadable=downloadable,
            path=path,
            link=link,
            size=size,
            createdAt=created_at,
            modifiedAt=modified_at,
            lastIndexed=last_indexed,
            snippet=snippet,
            content=content,
        )

        # 2) Compute & store the tsvector (use Coalesce to avoid NULLs)
        File.objects.filter(pk=file.pk).update(
            ts=(
                SearchVector(Coalesce("name", Value("")), weight="A", config=ts_config)
                + SearchVector(
                    Coalesce("content", Value("")), weight="B", config=ts_config
                )
            )
        )

        # 3) Load the computed ts on the instance
        file.refresh_from_db(fields=["ts"])

    return file
    
def search_files_by_name(name_query, user_id):
    """Searches for files by name containing the given query string and user id.

    params:
        name_query: Substring or list/tuple of substrings to search for in file names.
                    If a list/tuple is provided, tokens are combined with OR.
        user_id: User id to restrict results to. (applies as an AND).
    returns:
        QuerySet of File objects matching the search criteria.
    """
    if isinstance(name_query, (list, tuple)):
        q = Q()
        for token in name_query:
            q |= Q(name__icontains=token)
        if not q.children:
            return File.objects.none()
        if user_id is not None:
            q &= Q(serviceId__userId=user_id)
        return File.objects.filter(q)

    # Single string
    q = Q(name__icontains=name_query)
    if user_id is not None:
        q &= Q(serviceId__userId=user_id)
    return File.objects.filter(q)
